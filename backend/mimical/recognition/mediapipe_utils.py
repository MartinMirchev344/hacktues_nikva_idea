from __future__ import annotations

import os
import tempfile
from types import SimpleNamespace
from pathlib import Path
from urllib.request import urlretrieve

import numpy as np
from django.conf import settings

DEFAULT_MEDIAPIPE_TASK_URL = (
    "https://storage.googleapis.com/mediapipe-models/holistic_landmarker/"
    "holistic_landmarker/float16/latest/holistic_landmarker.task"
)
DEFAULT_TARGET_FRAME_COUNT = 30
FACE_LANDMARK_INDICES = {
    "forehead": 10,
    "nose": 1,
    "mouth_left": 61,
    "mouth_right": 291,
    "chin": 152,
}
POSE_LANDMARK_INDICES = {
    "nose": 0,
    "left_shoulder": 11,
    "right_shoulder": 12,
}


def normalize_sign_name(value: str) -> str:
    return (value or "").strip().lower().replace("-", "_").replace(" ", "_")


def get_holistic_task_path() -> Path:
    cache_dir = Path(
        os.getenv(
            "RECOGNITION_CACHE_DIR",
            Path(settings.BASE_DIR).parent / "model_cache",
        )
    )
    task_path = Path(
        os.getenv(
            "MEDIAPIPE_HOLISTIC_TASK_PATH",
            cache_dir / "mediapipe" / "holistic_landmarker.task",
        )
    )

    if task_path.exists():
        return task_path

    task_path.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(
        os.getenv("MEDIAPIPE_HOLISTIC_TASK_URL", DEFAULT_MEDIAPIPE_TASK_URL),
        task_path,
    )
    return task_path


def extract_video_frames(video_source) -> list[np.ndarray]:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is required to process uploaded videos.") from exc

    temp_path = None
    source_path = None

    if isinstance(video_source, (str, Path)):
        source_path = str(video_source)
    else:
        suffix = os.path.splitext(getattr(video_source, "name", "upload.mp4"))[1] or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            for chunk in video_source.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name
        source_path = temp_path

    capture = cv2.VideoCapture(str(source_path))
    frames: list[np.ndarray] = []
    try:
        while True:
            success, frame = capture.read()
            if not success:
                break
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        capture.release()
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

    if not frames:
        raise RuntimeError("No frames could be extracted from the uploaded video.")

    return frames


class HolisticSequenceExtractor:
    def __init__(self):
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise RuntimeError(
                "MediaPipe dependencies are missing. Install mediapipe in your backend environment."
            ) from exc

        self.mp = mp
        self.detector = mp.solutions.holistic.Holistic(
            static_image_mode=True,
            model_complexity=1,
            smooth_landmarks=False,
            enable_segmentation=False,
            refine_face_landmarks=False,
        )

    def close(self) -> None:
        if self.detector:
            self.detector.close()

    def extract_from_frames(self, frames: list[np.ndarray], target_frames: int = DEFAULT_TARGET_FRAME_COUNT) -> dict:
        detected_frames: list[dict] = []
        detected_count = 0
        secondary_detected_count = 0
        current_side = None

        for frame in frames:
            raw_results = self.detector.process(frame)
            results = SimpleNamespace(
                left_hand_landmarks=list(getattr(getattr(raw_results, "left_hand_landmarks", None), "landmark", []) or []),
                right_hand_landmarks=list(getattr(getattr(raw_results, "right_hand_landmarks", None), "landmark", []) or []),
                pose_landmarks=list(getattr(getattr(raw_results, "pose_landmarks", None), "landmark", []) or []),
                face_landmarks=list(getattr(getattr(raw_results, "face_landmarks", None), "landmark", []) or []),
            )
            frame_record = self._build_frame_record(results, current_side)
            if frame_record is not None:
                detected_frames.append(frame_record)
                current_side = frame_record["handedness"]
                detected_count += 1
                if "secondary_hand_landmarks" in frame_record:
                    secondary_detected_count += 1

        if detected_frames:
            detected_frames = _fill_missing_anchor_values(detected_frames)
            resampled_frames = _resample_frame_records(detected_frames, target_frames)
        else:
            resampled_frames = []

        handedness = _dominant_handedness(detected_frames)
        return {
            "sequence_version": 1,
            "frame_count_original": len(frames),
            "usable_frame_count": detected_count,
            "secondary_usable_frame_count": secondary_detected_count,
            "resampled_frame_count": len(resampled_frames),
            "handedness": handedness,
            "frames": resampled_frames,
        }

    def _build_frame_record(self, results, current_side: str | None) -> dict | None:
        hands = _choose_hands(results, current_side)
        if hands is None:
            return None

        primary_payload = _build_hand_payload(hands["primary_landmarks"])
        largest_palm_size = primary_payload["palm_size"]
        frame_record = {
            "handedness": hands["primary_side"],
            "hand_landmarks": primary_payload["hand_landmarks"],
            "hand_center": primary_payload["hand_center"],
            "openness": primary_payload["openness"],
            "palm_size": primary_payload["palm_size"],
        }

        if hands.get("secondary_landmarks") is not None:
            secondary_payload = _build_hand_payload(hands["secondary_landmarks"])
            largest_palm_size = max(largest_palm_size, secondary_payload["palm_size"])
            frame_record.update(
                {
                    "secondary_handedness": hands["secondary_side"],
                    "secondary_hand_landmarks": secondary_payload["hand_landmarks"],
                    "secondary_hand_center": secondary_payload["hand_center"],
                    "secondary_openness": secondary_payload["openness"],
                    "secondary_palm_size": secondary_payload["palm_size"],
                }
            )

        anchors = _extract_anchor_points(results, largest_palm_size)
        scale_hint = max(float(anchors["scale_hint"]), largest_palm_size * 3.5, 1e-6)
        frame_record["scale_hint"] = scale_hint
        frame_record["anchors"] = anchors
        return frame_record


def extract_landmark_sequence_from_video(video_source, target_frames: int = DEFAULT_TARGET_FRAME_COUNT) -> dict:
    frames = extract_video_frames(video_source)
    extractor = HolisticSequenceExtractor()
    try:
        return extractor.extract_from_frames(frames, target_frames=target_frames)
    finally:
        extractor.close()


def _dominant_handedness(frames: list[dict]) -> str | None:
    if not frames:
        return None
    left_count = sum(1 for frame in frames if frame["handedness"] == "left")
    right_count = sum(1 for frame in frames if frame["handedness"] == "right")
    return "left" if left_count > right_count else "right"


def _landmark_to_xyz(landmark) -> list[float]:
    return [float(landmark.x), float(landmark.y), float(getattr(landmark, "z", 0.0))]


def _choose_hands(results, current_side: str | None):
    left_hand = getattr(results, "left_hand_landmarks", None) or []
    right_hand = getattr(results, "right_hand_landmarks", None) or []

    if not left_hand and not right_hand:
        return None

    if left_hand and right_hand:
        if current_side in {"left", "right"}:
            primary_side = current_side
        else:
            left_span = _bbox_area(left_hand)
            right_span = _bbox_area(right_hand)
            primary_side = "left" if left_span >= right_span else "right"
        secondary_side = "right" if primary_side == "left" else "left"
        return {
            "primary_side": primary_side,
            "primary_landmarks": left_hand if primary_side == "left" else right_hand,
            "secondary_side": secondary_side,
            "secondary_landmarks": right_hand if primary_side == "left" else left_hand,
        }

    if left_hand:
        return {
            "primary_side": "left",
            "primary_landmarks": left_hand,
            "secondary_side": None,
            "secondary_landmarks": None,
        }
    return {
        "primary_side": "right",
        "primary_landmarks": right_hand,
        "secondary_side": None,
        "secondary_landmarks": None,
    }


def _build_hand_payload(hand_landmarks) -> dict[str, list[float] | float | list[list[float]]]:
    hand_array = np.array([_landmark_to_xyz(landmark) for landmark in hand_landmarks], dtype=np.float32)
    wrist = hand_array[0]
    palm_span = float(np.linalg.norm(hand_array[17, :2] - hand_array[5, :2]))
    palm_height = float(np.linalg.norm(hand_array[9, :2] - wrist[:2]))
    palm_size = max(palm_span, palm_height, 1e-6)
    hand_center = hand_array.mean(axis=0)
    fingertip_indices = (4, 8, 12, 16, 20)
    openness = float(np.mean([np.linalg.norm(hand_array[index, :2] - wrist[:2]) for index in fingertip_indices]) / palm_size)
    return {
        "hand_landmarks": hand_array.tolist(),
        "hand_center": hand_center.tolist(),
        "openness": openness,
        "palm_size": palm_size,
    }


def _bbox_area(landmarks) -> float:
    points = np.array([_landmark_to_xyz(landmark)[:2] for landmark in landmarks], dtype=np.float32)
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    width, height = maxs - mins
    return float(width * height)


def _extract_anchor_points(results, palm_size: float) -> dict[str, list[float] | float]:
    pose_landmarks = getattr(results, "pose_landmarks", None) or []
    face_landmarks = getattr(results, "face_landmarks", None) or []

    left_shoulder = _safe_landmark(pose_landmarks, POSE_LANDMARK_INDICES["left_shoulder"])
    right_shoulder = _safe_landmark(pose_landmarks, POSE_LANDMARK_INDICES["right_shoulder"])
    shoulder_center = _midpoint(left_shoulder, right_shoulder, fallback=[0.5, 0.62, 0.0])
    shoulder_span = _distance(left_shoulder, right_shoulder, fallback=max(palm_size * 3.5, 0.2))

    pose_nose = _safe_landmark(pose_landmarks, POSE_LANDMARK_INDICES["nose"])
    face_nose = _safe_landmark(face_landmarks, FACE_LANDMARK_INDICES["nose"])
    nose = pose_nose or face_nose or [0.5, 0.34, 0.0]

    forehead = _safe_landmark(face_landmarks, FACE_LANDMARK_INDICES["forehead"])
    chin = _safe_landmark(face_landmarks, FACE_LANDMARK_INDICES["chin"])
    mouth_left = _safe_landmark(face_landmarks, FACE_LANDMARK_INDICES["mouth_left"])
    mouth_right = _safe_landmark(face_landmarks, FACE_LANDMARK_INDICES["mouth_right"])
    mouth = _midpoint(mouth_left, mouth_right)

    if forehead is None:
        forehead = [nose[0], nose[1] - shoulder_span * 0.22, nose[2]]
    if mouth is None:
        mouth = [nose[0], nose[1] + shoulder_span * 0.06, nose[2]]
    if chin is None:
        chin = [nose[0], mouth[1] + shoulder_span * 0.10, nose[2]]

    return {
        "nose": nose,
        "forehead": forehead,
        "mouth": mouth,
        "chin": chin,
        "left_shoulder": left_shoulder or [shoulder_center[0] - (shoulder_span / 2.0), shoulder_center[1], 0.0],
        "right_shoulder": right_shoulder or [shoulder_center[0] + (shoulder_span / 2.0), shoulder_center[1], 0.0],
        "shoulder_center": shoulder_center,
        "scale_hint": shoulder_span,
    }


def _safe_landmark(landmarks, index: int):
    if landmarks and 0 <= index < len(landmarks):
        return _landmark_to_xyz(landmarks[index])
    return None


def _midpoint(a, b, fallback=None):
    if a is None and b is None:
        return fallback
    if a is None:
        return b
    if b is None:
        return a
    return [float((a[i] + b[i]) / 2.0) for i in range(3)]


def _distance(a, b, fallback: float) -> float:
    if a is None or b is None:
        return float(fallback)
    return float(np.linalg.norm(np.array(a[:2], dtype=np.float32) - np.array(b[:2], dtype=np.float32)))


def _fill_missing_anchor_values(frames: list[dict]) -> list[dict]:
    anchor_names = ("nose", "forehead", "mouth", "chin", "left_shoulder", "right_shoulder", "shoulder_center")
    filled_frames = [
        {
            **frame,
            "anchors": dict(frame["anchors"]),
        }
        for frame in frames
    ]

    for anchor_name in anchor_names:
        anchor_series = np.array(
            [frame["anchors"].get(anchor_name, [np.nan, np.nan, np.nan]) for frame in filled_frames],
            dtype=np.float32,
        )
        anchor_series = _interpolate_nan_rows(anchor_series)
        for index, frame in enumerate(filled_frames):
            frame["anchors"][anchor_name] = anchor_series[index].tolist()

    scale_series = np.array([frame.get("scale_hint", np.nan) for frame in filled_frames], dtype=np.float32)
    scale_series = _interpolate_nan_vector(scale_series, fallback=0.2)

    for index, frame in enumerate(filled_frames):
        frame["scale_hint"] = float(max(scale_series[index], 1e-6))
        frame["anchors"]["scale_hint"] = float(max(scale_series[index], 1e-6))

    _fill_optional_hand_values(filled_frames, prefix="secondary_")
    return filled_frames


def _fill_optional_hand_values(frames: list[dict], prefix: str) -> None:
    landmark_key = f"{prefix}hand_landmarks"
    center_key = f"{prefix}hand_center"
    openness_key = f"{prefix}openness"
    palm_size_key = f"{prefix}palm_size"
    handedness_key = f"{prefix}handedness"

    if not any(landmark_key in frame for frame in frames):
        return

    landmarks = []
    centers = []
    openness = []
    palm_sizes = []
    handedness_values = []

    for frame in frames:
        if landmark_key in frame:
            landmarks.append(np.array(frame[landmark_key], dtype=np.float32))
            centers.append(np.array(frame[center_key], dtype=np.float32))
            openness.append(float(frame[openness_key]))
            palm_sizes.append(float(frame[palm_size_key]))
            handedness_values.append(frame.get(handedness_key))
        else:
            landmarks.append(np.full((21, 3), np.nan, dtype=np.float32))
            centers.append(np.full((3,), np.nan, dtype=np.float32))
            openness.append(np.nan)
            palm_sizes.append(np.nan)
            handedness_values.append(None)

    landmarks_array = _interpolate_nan_higher_dim(np.stack(landmarks, axis=0))
    centers_array = _interpolate_nan_rows(np.stack(centers, axis=0))
    openness_array = _interpolate_nan_vector(np.array(openness, dtype=np.float32), fallback=0.0)
    palm_sizes_array = _interpolate_nan_vector(np.array(palm_sizes, dtype=np.float32), fallback=0.0)
    resolved_handedness = next((value for value in handedness_values if value), None)

    for index, frame in enumerate(frames):
        frame[landmark_key] = landmarks_array[index].tolist()
        frame[center_key] = centers_array[index].tolist()
        frame[openness_key] = float(max(openness_array[index], 0.0))
        frame[palm_size_key] = float(max(palm_sizes_array[index], 1e-6))
        if resolved_handedness:
            frame[handedness_key] = resolved_handedness


def _resample_frame_records(frames: list[dict], target_frames: int) -> list[dict]:
    if not frames:
        return []
    if len(frames) == target_frames:
        return frames

    hand_landmarks = np.array([frame["hand_landmarks"] for frame in frames], dtype=np.float32)
    hand_centers = np.array([frame["hand_center"] for frame in frames], dtype=np.float32)
    openness = np.array([frame["openness"] for frame in frames], dtype=np.float32)
    palm_sizes = np.array([frame["palm_size"] for frame in frames], dtype=np.float32)
    scale_hints = np.array([frame["scale_hint"] for frame in frames], dtype=np.float32)
    handedness = _dominant_handedness(frames)
    anchor_names = ("nose", "forehead", "mouth", "chin", "left_shoulder", "right_shoulder", "shoulder_center")
    anchors = {
        name: np.array([frame["anchors"][name] for frame in frames], dtype=np.float32)
        for name in anchor_names
    }

    resampled_hand_landmarks = _resample_numeric_array(hand_landmarks, target_frames)
    resampled_hand_centers = _resample_numeric_array(hand_centers, target_frames)
    resampled_openness = _resample_numeric_array(openness, target_frames)
    resampled_palm_sizes = _resample_numeric_array(palm_sizes, target_frames)
    resampled_scale_hints = _resample_numeric_array(scale_hints, target_frames)
    resampled_anchors = {
        name: _resample_numeric_array(values, target_frames)
        for name, values in anchors.items()
    }
    has_secondary = any("secondary_hand_landmarks" in frame for frame in frames)
    if has_secondary:
        secondary_hand_landmarks = np.array([frame["secondary_hand_landmarks"] for frame in frames], dtype=np.float32)
        secondary_hand_centers = np.array([frame["secondary_hand_center"] for frame in frames], dtype=np.float32)
        secondary_openness = np.array([frame["secondary_openness"] for frame in frames], dtype=np.float32)
        secondary_palm_sizes = np.array([frame["secondary_palm_size"] for frame in frames], dtype=np.float32)
        secondary_handedness = next((frame.get("secondary_handedness") for frame in frames if frame.get("secondary_handedness")), None)
        resampled_secondary_hand_landmarks = _resample_numeric_array(secondary_hand_landmarks, target_frames)
        resampled_secondary_hand_centers = _resample_numeric_array(secondary_hand_centers, target_frames)
        resampled_secondary_openness = _resample_numeric_array(secondary_openness, target_frames)
        resampled_secondary_palm_sizes = _resample_numeric_array(secondary_palm_sizes, target_frames)

    return [
        {
            "handedness": handedness,
            "hand_landmarks": resampled_hand_landmarks[index].tolist(),
            "hand_center": resampled_hand_centers[index].tolist(),
            "openness": float(resampled_openness[index]),
            "palm_size": float(max(resampled_palm_sizes[index], 1e-6)),
            "scale_hint": float(max(resampled_scale_hints[index], 1e-6)),
            "anchors": {
                name: resampled_anchors[name][index].tolist()
                for name in anchor_names
            }
            | {"scale_hint": float(max(resampled_scale_hints[index], 1e-6))},
        }
        | (
            {
                "secondary_handedness": secondary_handedness,
                "secondary_hand_landmarks": resampled_secondary_hand_landmarks[index].tolist(),
                "secondary_hand_center": resampled_secondary_hand_centers[index].tolist(),
                "secondary_openness": float(resampled_secondary_openness[index]),
                "secondary_palm_size": float(max(resampled_secondary_palm_sizes[index], 1e-6)),
            }
            if has_secondary
            else {}
        )
        for index in range(target_frames)
    ]


def _interpolate_nan_rows(values: np.ndarray) -> np.ndarray:
    result = values.copy()
    for axis in range(result.shape[1]):
        result[:, axis] = _interpolate_nan_vector(result[:, axis], fallback=0.5 if axis == 0 else 0.0)
    return result


def _interpolate_nan_higher_dim(values: np.ndarray) -> np.ndarray:
    result = values.copy()
    flattened = result.reshape(result.shape[0], -1)
    for axis in range(flattened.shape[1]):
        flattened[:, axis] = _interpolate_nan_vector(flattened[:, axis], fallback=0.0)
    return flattened.reshape(result.shape)


def _interpolate_nan_vector(values: np.ndarray, fallback: float) -> np.ndarray:
    result = values.astype(np.float32, copy=True)
    valid = np.isfinite(result)
    if not np.any(valid):
        result[:] = fallback
        return result
    indices = np.arange(result.shape[0], dtype=np.float32)
    result[~valid] = np.interp(indices[~valid], indices[valid], result[valid])
    return result


def _resample_numeric_array(values: np.ndarray, target_frames: int) -> np.ndarray:
    if values.shape[0] == target_frames:
        return values
    source_positions = np.linspace(0.0, 1.0, num=values.shape[0], dtype=np.float32)
    target_positions = np.linspace(0.0, 1.0, num=target_frames, dtype=np.float32)
    flattened = values.reshape(values.shape[0], -1)
    resampled = np.stack(
        [
            np.interp(target_positions, source_positions, flattened[:, column_index])
            for column_index in range(flattened.shape[1])
        ],
        axis=1,
    )
    return resampled.reshape((target_frames,) + values.shape[1:]).astype(np.float32)
