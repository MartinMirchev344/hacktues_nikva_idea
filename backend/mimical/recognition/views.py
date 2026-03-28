import io
import logging
import os
from functools import lru_cache
from pathlib import Path
from urllib.request import urlretrieve

import numpy as np
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import RecognitionConfigurationError, RecognitionDependencyError
from .serializers import RecognitionHealthSerializer
from .services import get_recognition_service

DEFAULT_MEDIAPIPE_TASK_URL = (
    "https://storage.googleapis.com/mediapipe-models/holistic_landmarker/"
    "holistic_landmarker/float16/latest/holistic_landmarker.task"
)
logger = logging.getLogger(__name__)


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


def _bbox_area_for_landmarks(landmarks):
    if not landmarks:
        return 0.0
    coords = np.array([[float(landmark.x), float(landmark.y)] for landmark in landmarks], dtype=np.float32)
    mins = coords.min(axis=0)
    maxs = coords.max(axis=0)
    width, height = maxs - mins
    return float(width * height)


def _choose_primary_hand_landmarks(left_hand_landmarks, right_hand_landmarks):
    left_hand_landmarks = left_hand_landmarks or []
    right_hand_landmarks = right_hand_landmarks or []

    if left_hand_landmarks and right_hand_landmarks:
        return (
            left_hand_landmarks
            if _bbox_area_for_landmarks(left_hand_landmarks) >= _bbox_area_for_landmarks(right_hand_landmarks)
            else right_hand_landmarks
        )
    if left_hand_landmarks:
        return left_hand_landmarks
    if right_hand_landmarks:
        return right_hand_landmarks
    return None


@lru_cache(maxsize=1)
def _get_tasks_holistic_detector():
    try:
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python import vision
    except ImportError as exc:
        raise RecognitionDependencyError(
            "MediaPipe dependencies are missing. Install mediapipe in your backend environment."
        ) from exc

    task_path = get_holistic_task_path()
    options = vision.HolisticLandmarkerOptions(
        base_options=BaseOptions(
            model_asset_path=str(task_path),
            delegate=BaseOptions.Delegate.CPU,
        ),
        running_mode=vision.RunningMode.IMAGE,
        output_face_blendshapes=False,
        output_segmentation_mask=False,
    )
    return mp, vision.HolisticLandmarker.create_from_options(options)


def detect_hand_landmarks(pil_image):
    """
    Detect 21 hand landmarks and return the primary hand, or None if no hand was found.
    """
    img_np = np.array(pil_image)

    try:
        mp, detector = _get_tasks_holistic_detector()
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_np)
        result = detector.detect(mp_image)
        return _choose_primary_hand_landmarks(
            getattr(result, "left_hand_landmarks", None),
            getattr(result, "right_hand_landmarks", None),
        )
    except RecognitionDependencyError:
        raise
    except Exception as exc:
        logger.warning("Falling back to legacy MediaPipe Hands API: %s", exc)

    try:
        import mediapipe as mp
    except ImportError as exc:
        raise RecognitionDependencyError(
            "MediaPipe dependencies are missing. Install mediapipe in your backend environment."
        ) from exc

    hands_api = getattr(getattr(mp, "solutions", None), "hands", None)
    if hands_api is None:
        raise RecognitionDependencyError(
            "The installed mediapipe package does not expose either the Tasks API or mp.solutions.hands."
        )

    with hands_api.Hands(
        static_image_mode=True,
        max_num_hands=1,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as detector:
        result = detector.process(img_np)

    if getattr(result, "multi_hand_landmarks", None):
        return result.multi_hand_landmarks[0].landmark
    return None


def _clamp01(value):
    return float(max(0.0, min(1.0, value)))


def _score_ge(value, target, softness):
    if value >= target:
        return 1.0
    return _clamp01((value - (target - softness)) / max(softness, 1e-6))


def _score_le(value, target, softness):
    if value <= target:
        return 1.0
    return _clamp01(((target + softness) - value) / max(softness, 1e-6))


def _average(*values):
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _segment_intersection(p1, p2, q1, q2):
    def orientation(a, b, c):
        cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(cross) < 1e-6:
            return 0
        return 1 if cross > 0 else -1

    o1 = orientation(p1, p2, q1)
    o2 = orientation(p1, p2, q2)
    o3 = orientation(q1, q2, p1)
    o4 = orientation(q1, q2, p2)
    return o1 != o2 and o3 != o4


def _normalize_expected_letter(value):
    normalized = (value or "").strip().lower()
    if len(normalized) == 1 and normalized.isalpha():
        return normalized
    return None


def _empty_alphabet_analysis(summary):
    return {
        "summary": summary,
        "extended_fingers": [],
        "folded_fingers": [],
        "finger_extension_scores": {},
        "quality": {
            "score": 0.0,
            "hand_box_span": 0.0,
            "center_offset": 0.0,
            "clipped_edges": [],
        },
        "thumb": {
            "lateral_distance": 0.0,
            "index_touch_distance": 0.0,
            "middle_base_distance": 0.0,
            "index_middle_gap_distance": 0.0,
            "knuckle_height": 0.0,
            "ring_tip_distance": 0.0,
        },
        "spreads": {
            "index_middle": 0.0,
            "middle_ring": 0.0,
            "ring_pinky": 0.0,
        },
        "crossed_index_middle": False,
    }


def _empty_alphabet_prediction(summary):
    return {
        "predicted_letter": None,
        "confidence": 0.0,
        "top_predictions": [],
        "analysis": _empty_alphabet_analysis(summary),
    }


def analyze_asl_landmarks(landmarks):
    """
    Static handshape analysis for alphabet practice.
    Supports the letters: A B D F K M R T V W.
    """
    if not landmarks or len(landmarks) < 21:
        return _empty_alphabet_prediction("insufficient_landmarks")

    try:
        lm = np.array(
            [
                [
                    float(landmark.x),
                    float(landmark.y),
                    float(getattr(landmark, "z", 0.0)),
                ]
                for landmark in landmarks[:21]
            ],
            dtype=np.float32,
        )
    except (AttributeError, TypeError, ValueError):
        return _empty_alphabet_prediction("invalid_landmarks")

    if not np.isfinite(lm).all():
        return _empty_alphabet_prediction("invalid_landmarks")

    wrist = lm[0, :2]
    palm_width = np.linalg.norm(lm[17, :2] - lm[5, :2])
    palm_height = np.linalg.norm(lm[9, :2] - wrist)
    hand_size = max(float(max(palm_width, palm_height)), 1e-6)

    if hand_size < 1e-6:
        return _empty_alphabet_prediction("invalid_landmarks")

    palm_center = (lm[5, :2] + lm[17, :2]) / 2.0
    palm_x_axis = lm[17, :2] - lm[5, :2]
    palm_x_norm = np.linalg.norm(palm_x_axis)
    if palm_x_norm < 1e-6:
        palm_x_axis = np.array([1.0, 0.0], dtype=np.float32)
    else:
        palm_x_axis = palm_x_axis / palm_x_norm

    def dist(a, b):
        return float(np.linalg.norm(lm[a, :2] - lm[b, :2]) / hand_size)

    def midpoint_distance(index, a, b):
        midpoint = (lm[a, :2] + lm[b, :2]) / 2.0
        return float(np.linalg.norm(lm[index, :2] - midpoint) / hand_size)

    def lateral_distance(index):
        return float(abs(np.dot(lm[index, :2] - palm_center, palm_x_axis)) / hand_size)

    finger_points = {
        "index": (5, 6, 8),
        "middle": (9, 10, 12),
        "ring": (13, 14, 16),
        "pinky": (17, 18, 20),
    }

    finger_extension_scores = {}
    finger_fold_scores = {}

    for name, (mcp, pip, tip) in finger_points.items():
        tip_wrist_ratio = float(
            np.linalg.norm(lm[tip, :2] - wrist) / max(np.linalg.norm(lm[pip, :2] - wrist), 1e-6)
        )
        tip_height = float((lm[pip, 1] - lm[tip, 1]) / hand_size)
        finger_extension_scores[name] = _average(
            _score_ge(tip_wrist_ratio, 1.14, 0.20),
            _score_ge(tip_height, 0.20, 0.14),
        )
        finger_fold_scores[name] = _average(
            _score_le(tip_wrist_ratio, 1.05, 0.20),
            _score_le(tip_height, 0.08, 0.18),
        )

    extended_fingers = [name for name, score in finger_extension_scores.items() if score >= 0.62]
    folded_fingers = [name for name, score in finger_fold_scores.items() if score >= 0.62]

    thumb_lateral = lateral_distance(4)
    thumb_index_touch = dist(4, 8)
    thumb_middle_tip = dist(4, 12)
    thumb_ring_tip = dist(4, 16)
    thumb_middle_mcp = dist(4, 9)
    thumb_index_middle_gap = midpoint_distance(4, 5, 9)
    thumb_knuckle_height = float((((lm[5, 1] + lm[9, 1]) / 2.0) - lm[4, 1]) / hand_size)

    index_middle_spread = dist(8, 12) / max(dist(5, 9), 1e-6)
    middle_ring_spread = dist(12, 16) / max(dist(9, 13), 1e-6)
    ring_pinky_spread = dist(16, 20) / max(dist(13, 17), 1e-6)
    crossed_index_middle = _segment_intersection(lm[6, :2], lm[8, :2], lm[10, :2], lm[12, :2])

    bbox_min = lm[:, :2].min(axis=0)
    bbox_max = lm[:, :2].max(axis=0)
    hand_box_width = float(bbox_max[0] - bbox_min[0])
    hand_box_height = float(bbox_max[1] - bbox_min[1])
    hand_box_span = max(hand_box_width, hand_box_height)
    center_offset = float(np.linalg.norm(((bbox_min + bbox_max) / 2.0) - np.array([0.5, 0.5])))
    clipped_edges = []
    margin = 0.05
    if bbox_min[0] < margin:
        clipped_edges.append("left")
    if bbox_max[0] > (1.0 - margin):
        clipped_edges.append("right")
    if bbox_min[1] < margin:
        clipped_edges.append("top")
    if bbox_max[1] > (1.0 - margin):
        clipped_edges.append("bottom")

    quality_score = 1.0
    if hand_box_span < 0.28:
        quality_score -= 0.15
    if center_offset > 0.30:
        quality_score -= 0.10
    if clipped_edges:
        quality_score -= min(0.16, 0.06 * len(clipped_edges))
    quality_score = _clamp01(quality_score)

    scores = {
        "a": _average(
            finger_fold_scores["index"],
            finger_fold_scores["middle"],
            finger_fold_scores["ring"],
            finger_fold_scores["pinky"],
            _score_ge(thumb_lateral, 0.38, 0.18),
            1.0 - _score_le(thumb_index_middle_gap, 0.26, 0.14),
        ),
        "b": _average(
            finger_extension_scores["index"],
            finger_extension_scores["middle"],
            finger_extension_scores["ring"],
            finger_extension_scores["pinky"],
            _score_le(thumb_lateral, 0.34, 0.18),
            _score_le(index_middle_spread, 1.15, 0.35),
            _score_le(middle_ring_spread, 1.15, 0.35),
            _score_le(ring_pinky_spread, 1.15, 0.35),
        ),
        "d": _average(
            finger_extension_scores["index"],
            finger_fold_scores["middle"],
            finger_fold_scores["ring"],
            finger_fold_scores["pinky"],
            _average(
                _score_le(thumb_middle_tip, 0.44, 0.18),
                _score_le(thumb_ring_tip, 0.46, 0.18),
            ),
        ),
        "f": _average(
            _score_le(thumb_index_touch, 0.34, 0.14),
            finger_fold_scores["index"],
            finger_extension_scores["middle"],
            finger_extension_scores["ring"],
            finger_extension_scores["pinky"],
        ),
        "k": _average(
            finger_extension_scores["index"],
            finger_extension_scores["middle"],
            finger_fold_scores["ring"],
            finger_fold_scores["pinky"],
            _score_ge(thumb_middle_mcp, 0.28, 0.06),
            _score_ge(thumb_lateral, 0.10, 0.03),
            _score_ge(thumb_ring_tip, 0.72, 0.18),
            _score_ge(index_middle_spread, 1.05, 0.28),
            1.0 - _score_le(thumb_index_touch, 0.30, 0.12),
        ) * _score_ge(thumb_knuckle_height, 0.08, 0.08),
        "m": _average(
            finger_fold_scores["index"],
            finger_fold_scores["middle"],
            finger_fold_scores["ring"],
            finger_fold_scores["pinky"],
            _score_le(thumb_ring_tip, 0.42, 0.20),
            1.0 - _score_le(thumb_lateral, 0.34, 0.14),
            1.0 - _score_le(thumb_index_middle_gap, 0.24, 0.12),
        ),
        "r": _average(
            finger_extension_scores["index"],
            finger_extension_scores["middle"],
            finger_fold_scores["ring"],
            finger_fold_scores["pinky"],
            _score_le(index_middle_spread, 0.90, 0.12),
            1.0 if crossed_index_middle else 0.0,
        ),
        "t": _average(
            finger_fold_scores["index"],
            finger_fold_scores["middle"],
            finger_fold_scores["ring"],
            finger_fold_scores["pinky"],
            _score_le(thumb_index_middle_gap, 0.24, 0.12),
            _score_le(thumb_lateral, 0.28, 0.12),
        ),
        "v": _average(
            finger_extension_scores["index"],
            finger_extension_scores["middle"],
            finger_fold_scores["ring"],
            finger_fold_scores["pinky"],
            _score_ge(index_middle_spread, 1.28, 0.32),
            _score_le(thumb_knuckle_height, 0.04, 0.10),
            1.0 - _score_le(thumb_middle_mcp, 0.36, 0.16),
            0.0 if crossed_index_middle else 1.0,
        ),
        "w": _average(
            finger_extension_scores["index"],
            finger_extension_scores["middle"],
            finger_extension_scores["ring"],
            1.0 - finger_fold_scores["ring"],
            finger_fold_scores["pinky"],
            1.0 - finger_extension_scores["pinky"],
            _score_ge(index_middle_spread, 1.08, 0.28),
            _score_ge(middle_ring_spread, 1.08, 0.28),
            _score_ge(ring_pinky_spread, 1.40, 0.35),
        ),
    }

    ranked_candidates = [
        {
            "letter": letter,
            "confidence": round(_clamp01(score * quality_score) * 100, 1),
        }
        for letter, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    ]

    top_candidate = ranked_candidates[0]
    runner_up = ranked_candidates[1]
    top_confidence = top_candidate["confidence"]
    confidence_gap = top_candidate["confidence"] - runner_up["confidence"]
    predicted_letter = top_candidate["letter"]

    if top_confidence < 48.0 or confidence_gap < 8.0:
        predicted_letter = None
        top_confidence = 0.0

    return {
        "predicted_letter": predicted_letter,
        "confidence": round(top_confidence, 1),
        "top_predictions": [
            {"letter": candidate["letter"], "confidence": candidate["confidence"]}
            for candidate in ranked_candidates[:3]
        ],
        "analysis": {
            "summary": "ok",
            "extended_fingers": extended_fingers,
            "folded_fingers": folded_fingers,
            "finger_extension_scores": {
                name: round(score * 100, 1) for name, score in finger_extension_scores.items()
            },
            "quality": {
                "score": round(quality_score * 100, 1),
                "hand_box_span": round(hand_box_span, 3),
                "center_offset": round(center_offset, 3),
                "clipped_edges": clipped_edges,
            },
            "thumb": {
                "lateral_distance": round(thumb_lateral, 3),
                "index_touch_distance": round(thumb_index_touch, 3),
                "middle_base_distance": round(thumb_middle_mcp, 3),
                "index_middle_gap_distance": round(thumb_index_middle_gap, 3),
                "knuckle_height": round(thumb_knuckle_height, 3),
                "ring_tip_distance": round(thumb_ring_tip, 3),
            },
            "spreads": {
                "index_middle": round(index_middle_spread, 3),
                "middle_ring": round(middle_ring_spread, 3),
                "ring_pinky": round(ring_pinky_spread, 3),
            },
            "crossed_index_middle": crossed_index_middle,
        },
    }


def classify_asl_landmarks(landmarks):
    analysis = analyze_asl_landmarks(landmarks)
    return analysis["predicted_letter"], analysis["confidence"]


def build_alphabet_feedback(expected_letter, prediction):
    analysis = prediction["analysis"]
    quality = analysis["quality"]
    extended = set(analysis["extended_fingers"])
    thumb = analysis["thumb"]
    spreads = analysis["spreads"]
    feedback_items = []

    if quality["hand_box_span"] < 0.28:
        feedback_items.append("Move your hand a little closer to the camera so the finger details are easier to read.")
    if quality["center_offset"] > 0.30:
        feedback_items.append("Center your hand in the frame before taking the photo.")
    if quality["clipped_edges"]:
        feedback_items.append("Keep your whole hand inside the frame and leave a small margin around it.")

    expected_specific = {
        "a": [
            (bool(extended), "Curl all four fingers into a fist for the letter A."),
            (thumb["lateral_distance"] < 0.36, "Rest your thumb on the outside of the fist instead of tucking it between fingers."),
        ],
        "b": [
            (not {"index", "middle", "ring", "pinky"}.issubset(extended), "Straighten all four fingers fully for the letter B."),
            (thumb["lateral_distance"] > 0.34, "Fold your thumb across the palm so it stays tucked in."),
            (max(spreads["index_middle"], spreads["middle_ring"], spreads["ring_pinky"]) > 1.20, "Keep the four fingers closer together so the hand looks flatter."),
        ],
        "d": [
            ("index" not in extended, "Raise the index finger straight up."),
            (bool({"middle", "ring", "pinky"} & extended), "Tuck the middle, ring, and pinky fingers down."),
            (thumb["middle_base_distance"] > 0.44, "Bring the thumb closer to the middle finger to form the D handshape."),
        ],
        "f": [
            (thumb["index_touch_distance"] > 0.34, "Touch the thumb and index finger to form a clear circle."),
            (not {"middle", "ring", "pinky"}.issubset(extended), "Keep the middle, ring, and pinky fingers up."),
        ],
        "k": [
            (not {"index", "middle"}.issubset(extended), "Lift the index and middle fingers into a V shape."),
            (bool({"ring", "pinky"} & extended), "Keep the ring and pinky fingers folded down."),
            (thumb["middle_base_distance"] > 0.42, "Place the thumb against the middle finger instead of letting it float away."),
        ],
        "m": [
            (bool(extended), "Fold the fingers down into a closed fist for M."),
            (thumb["ring_tip_distance"] > 0.44, "Tuck the thumb deeper under the first three fingers."),
        ],
        "r": [
            (not {"index", "middle"}.issubset(extended), "Lift the index and middle fingers for R."),
            (not analysis["crossed_index_middle"], "Cross the middle finger over the index finger more clearly."),
            (bool({"ring", "pinky"} & extended), "Keep the ring and pinky fingers folded down."),
        ],
        "t": [
            (bool(extended), "Close the hand into a fist for T."),
            (thumb["index_middle_gap_distance"] > 0.26, "Tuck the thumb between the index and middle fingers."),
        ],
        "v": [
            (not {"index", "middle"}.issubset(extended), "Raise the index and middle fingers for V."),
            (spreads["index_middle"] < 1.24, "Spread the index and middle fingers farther apart."),
            (bool({"ring", "pinky"} & extended), "Keep the ring and pinky fingers folded down."),
        ],
        "w": [
            (not {"index", "middle", "ring"}.issubset(extended), "Lift the index, middle, and ring fingers for W."),
            ("pinky" in extended, "Tuck the pinky down to separate W from B."),
            (min(spreads["index_middle"], spreads["middle_ring"]) < 1.08, "Spread the three raised fingers a little more."),
        ],
    }

    for should_add, message in expected_specific.get(expected_letter, []):
        if should_add and message not in feedback_items:
            feedback_items.append(message)
        if len(feedback_items) >= 3:
            break

    return feedback_items[:3]


def build_alphabet_response(prediction, expected_letter=None):
    predicted_letter = prediction["predicted_letter"]
    confidence = prediction["confidence"]
    is_correct = None
    accuracy_score = round(confidence, 1)
    handshape_score = round(confidence, 1)
    coach_summary = "The model found a handshape, but it still needs a clearer view to be fully confident."
    feedback_items = []

    if expected_letter:
        is_correct = predicted_letter == expected_letter
        accuracy_score = round(confidence if is_correct else max(confidence * 0.45, 5.0), 1)
        if is_correct:
            coach_summary = (
                f'This looks like a solid "{expected_letter.upper()}" handshape. '
                f'The letter pattern matches with {confidence:.0f}% confidence.'
            )
        elif predicted_letter:
            coach_summary = (
                f'This looks closer to "{predicted_letter.upper()}" than "{expected_letter.upper()}". '
                "Adjust the finger shape and try another photo."
            )
        else:
            coach_summary = (
                f'The photo did not match "{expected_letter.upper()}" clearly enough yet. '
                "Try a clearer handshape, steadier framing, or slightly different angle."
            )
        feedback_items = build_alphabet_feedback(expected_letter, prediction)
    elif predicted_letter:
        coach_summary = (
            f'The handshape looks closest to "{predicted_letter.upper()}" with {confidence:.0f}% confidence.'
        )

    return {
        "predicted_letter": predicted_letter,
        "confidence": confidence,
        "top_predictions": prediction["top_predictions"],
        "expected_letter": expected_letter,
        "is_correct": is_correct,
        "accuracy_score": accuracy_score,
        "handshape_score": handshape_score,
        "coach_summary": coach_summary,
        "feedback_items": feedback_items,
        "analysis": prediction["analysis"],
    }


class RecognitionHealthView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        service = get_recognition_service()
        serializer = RecognitionHealthSerializer(service.health())
        return Response(serializer.data)


class AlphabetPredictView(APIView):
    """
    POST /api/recognition/alphabet/predict/
    Accepts multipart/form-data with an 'image' field.
    Returns the predicted ASL letter via hand-landmark analysis.
    """

    def post(self, request):
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'detail': 'No image provided.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            try:
                from PIL import Image, ImageOps, UnidentifiedImageError
            except ImportError as exc:
                raise RecognitionDependencyError(
                    "Pillow is required to process uploaded images. Install pillow in your backend environment."
                ) from exc

            raw_bytes = image_file.read()
            try:
                raw = Image.open(io.BytesIO(raw_bytes))
            except UnidentifiedImageError:
                return Response(
                    {'detail': 'The uploaded file is not a supported image.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            image = ImageOps.exif_transpose(raw).convert('RGB')

            landmarks = detect_hand_landmarks(image)

            if landmarks is None:
                return Response(
                    {'detail': 'No hand detected in the image. Make sure your hand is clearly visible.'},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            expected_letter = _normalize_expected_letter(request.data.get("expected_letter"))
            prediction = analyze_asl_landmarks(landmarks)
            letter = prediction["predicted_letter"]

            if not letter:
                return Response(
                    {'detail': 'Could not identify the hand sign clearly enough. Try a clearer handshape or a slightly different angle.'},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            return Response(build_alphabet_response(prediction, expected_letter=expected_letter))

        except (RecognitionDependencyError, RecognitionConfigurationError) as exc:
            logger.warning("Alphabet prediction unavailable: %s", exc)
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.exception("Unexpected alphabet prediction failure")
            return Response(
                {'detail': f'Prediction failed: {exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
