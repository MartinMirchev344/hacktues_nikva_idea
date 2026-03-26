import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.request import urlretrieve

import numpy as np

from django.conf import settings

from lessons.models import Exercise

from .exceptions import RecognitionConfigurationError, RecognitionDependencyError
from .tgcn_config import TGCNConfig

DEFAULT_SUPPORTED_LESSONS = (1, 2, 5)
SUPPORTED_SIGN_ALIASES = {
    "hello": ["hello"],
    "goodbye": ["goodbye", "good bye"],
    "thank_you": ["thank_you", "thank you", "thanks"],
    "please": ["please"],
    "sorry": ["sorry"],
    "yes": ["yes"],
    "no": ["no"],
    "maybe": ["maybe"],
    "mother": ["mother"],
    "father": ["father"],
    "brother": ["brother"],
    "sister": ["sister"],
    "friend": ["friend"],
}
POSE_INDICES = (0, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22)
KEYPOINT_COUNT = 55


def normalize_label(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def env_list(name: str, default: tuple[int, ...]) -> list[int]:
    raw_value = os.getenv(name)
    if not raw_value:
        return list(default)
    return [int(item.strip()) for item in raw_value.split(",") if item.strip()]


@dataclass
class RecognitionSettings:
    repo_id: str
    variant: str
    dataset_repo_id: str
    dataset_labels_file: str
    token: str | None
    cache_dir: Path
    labels_path: Path | None
    holistic_task_path: Path
    holistic_task_url: str
    supported_lessons: list[int]


@dataclass
class PredictionCandidate:
    sign: str
    score: float
    model_label: str
    class_index: int


@dataclass
class PredictionResult:
    predicted_sign: str
    confidence: float
    candidates: list[PredictionCandidate]
    tracking_data: dict[str, Any]
    warnings: list[str]
    model: dict[str, Any]


class MediaPipeHolisticExtractor:
    def __init__(self, config: RecognitionSettings):
        try:
            import mediapipe as mp
            from mediapipe.tasks.python import BaseOptions
            from mediapipe.tasks.python import vision
        except ImportError as exc:
            raise RecognitionDependencyError(
                "MediaPipe dependencies are missing. Install mediapipe in your backend environment."
            ) from exc

        self.mp = mp
        task_path = self._ensure_task_asset(config)
        options = vision.HolisticLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(task_path)),
            running_mode=vision.RunningMode.IMAGE,
            output_face_blendshapes=False,
            output_segmentation_mask=False,
        )
        self.holistic = vision.HolisticLandmarker.create_from_options(options)

    def extract_sequence(self, frames: list[np.ndarray], frame_count: int) -> tuple[np.ndarray, dict[str, Any]]:
        if not frames:
            raise RecognitionConfigurationError("No frames were provided for recognition.")

        sampled_frames = self._sample_frames(frames, frame_count)
        keypoint_frames = []
        detected_frames = 0

        for frame in sampled_frames:
            mp_image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=frame)
            results = self.holistic.detect(mp_image)
            keypoints, frame_detected = self._collect_keypoints(results)
            keypoint_frames.append(keypoints)
            if frame_detected:
                detected_frames += 1

        sequence = np.stack(keypoint_frames, axis=0)
        model_input = sequence.transpose(1, 0, 2).reshape(KEYPOINT_COUNT, frame_count * 2)
        tracking_data = {
            "frames_received": len(frames),
            "frames_analyzed": len(sampled_frames),
            "frames_with_landmarks": detected_frames,
            "keypoints_per_frame": KEYPOINT_COUNT,
            "layout": "55x(frame_count*2)",
        }
        return model_input.astype(np.float32), tracking_data

    def _sample_frames(self, frames: list[np.ndarray], frame_count: int) -> list[np.ndarray]:
        if len(frames) == frame_count:
            return frames
        indices = np.linspace(0, len(frames) - 1, num=frame_count, dtype=int)
        return [frames[index] for index in indices]

    def _collect_keypoints(self, results) -> tuple[np.ndarray, bool]:
        points = []
        detected = False

        pose_landmarks = getattr(results, "pose_landmarks", None) or []
        left_hand_landmarks = getattr(results, "left_hand_landmarks", None) or []
        right_hand_landmarks = getattr(results, "right_hand_landmarks", None) or []

        if pose_landmarks:
            detected = True
            for index in POSE_INDICES:
                landmark = pose_landmarks[index]
                points.append([landmark.x, landmark.y])
        else:
            points.extend([[0.0, 0.0] for _ in POSE_INDICES])

        for hand_landmarks in (left_hand_landmarks, right_hand_landmarks):
            if hand_landmarks:
                detected = True
                for landmark in hand_landmarks:
                    points.append([landmark.x, landmark.y])
            else:
                points.extend([[0.0, 0.0] for _ in range(21)])

        return np.array(points, dtype=np.float32), detected

    def _ensure_task_asset(self, config: RecognitionSettings) -> Path:
        task_path = config.holistic_task_path
        if task_path.exists():
            return task_path

        task_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            urlretrieve(config.holistic_task_url, task_path)
        except Exception as exc:
            raise RecognitionConfigurationError(
                "Could not download the MediaPipe holistic task file. Set MEDIAPIPE_HOLISTIC_TASK_PATH to a valid local .task file."
            ) from exc
        return task_path


class WlaslTGCNBackend:
    def __init__(self, config: RecognitionSettings):
        self.config = config
        self._model = None
        self._tgcn_config = None
        self._label_map = None

    def status(self) -> dict[str, Any]:
        warnings = []
        dependencies_ready = self._torch_is_available() and self._hub_is_available()
        model_ready = False

        if not dependencies_ready:
            warnings.append("PyTorch and huggingface_hub must be installed in the backend environment.")
        else:
            try:
                self._ensure_loaded()
                model_ready = True
            except RecognitionConfigurationError as exc:
                warnings.append(str(exc))

        return {
            "status": "ready" if model_ready else "setup_required",
            "model_ready": model_ready,
            "dependencies_ready": dependencies_ready,
            "supported_lessons": self.config.supported_lessons,
            "configured_model": self.config.repo_id,
            "configured_variant": self.config.variant,
            "cache_dir": str(self.config.cache_dir),
            "warnings": warnings,
        }

    def predict(self, sequence: np.ndarray, allowed_signs: list[str], top_k: int) -> tuple[list[PredictionCandidate], list[str]]:
        self._ensure_loaded()

        import torch

        inputs = torch.from_numpy(sequence).unsqueeze(0)
        with torch.no_grad():
            logits = self._model(inputs)
            probabilities = torch.softmax(logits, dim=1)[0].cpu().numpy()

        allowed_indices = self._resolve_allowed_indices(allowed_signs)
        warnings = []

        if allowed_indices:
            ranked_indices = sorted(
                allowed_indices,
                key=lambda index: float(probabilities[index]),
                reverse=True,
            )[:top_k]
        else:
            warnings.append(
                "No label mapping could be resolved for the requested lessons. Using the model's unrestricted top predictions."
            )
            ranked_indices = list(np.argsort(probabilities)[::-1][:top_k])

        candidates = []
        for index in ranked_indices:
            raw_label = self._label_map.get(index, f"class_{index}")
            sign = self._resolve_sign_name(raw_label, allowed_signs)
            candidates.append(
                PredictionCandidate(
                    sign=sign,
                    score=float(probabilities[index]),
                    model_label=raw_label,
                    class_index=int(index),
                )
            )
        return candidates, warnings

    @property
    def num_samples(self) -> int:
        self._ensure_loaded()
        return self._tgcn_config.num_samples

    def _ensure_loaded(self):
        if self._model is not None and self._label_map is not None and self._tgcn_config is not None:
            return

        try:
            import torch
            from huggingface_hub import hf_hub_download
            from .tgcn_model import GCNMultiAtt
        except ImportError as exc:
            raise RecognitionDependencyError(
                "Install torch and huggingface_hub to use the recognition backend."
            ) from exc

        checkpoint_filename = f"checkpoints/{self.config.variant}/pytorch_model.bin"
        config_filename = f"checkpoints/{self.config.variant}/config.ini"

        try:
            checkpoint_path = hf_hub_download(
                repo_id=self.config.repo_id,
                filename=checkpoint_filename,
                cache_dir=str(self.config.cache_dir),
                token=self.config.token,
            )
            config_path = hf_hub_download(
                repo_id=self.config.repo_id,
                filename=config_filename,
                cache_dir=str(self.config.cache_dir),
                token=self.config.token,
            )
        except Exception as exc:
            raise RecognitionConfigurationError(
                "Could not download the configured Hugging Face model. Check HF_TOKEN, network access, and the repo id."
            ) from exc

        self._tgcn_config = TGCNConfig(config_path)
        label_map = self._load_label_map()
        class_count = self._infer_class_count(label_map)
        self._model = GCNMultiAtt(
            input_feature=self._tgcn_config.num_samples * 2,
            hidden_feature=self._tgcn_config.hidden_size,
            num_class=class_count,
            p_dropout=self._tgcn_config.drop_p,
            num_stage=self._tgcn_config.num_stages,
        )

        checkpoint = torch.load(checkpoint_path, map_location="cpu")
        state_dict = checkpoint.get("state_dict", checkpoint)
        self._model.load_state_dict(state_dict, strict=False)
        self._model.eval()
        self._label_map = label_map

    def _load_label_map(self) -> dict[int, str]:
        if self.config.labels_path and self.config.labels_path.exists():
            return self._read_label_file(self.config.labels_path)

        try:
            from huggingface_hub import hf_hub_download
        except ImportError as exc:
            raise RecognitionDependencyError(
                "Install huggingface_hub to resolve WLASL labels automatically."
            ) from exc

        for filename in (
            f"checkpoints/{self.config.variant}/labels.json",
            "labels.json",
            "id2label.json",
        ):
            try:
                downloaded = hf_hub_download(
                    repo_id=self.config.repo_id,
                    filename=filename,
                    cache_dir=str(self.config.cache_dir),
                    token=self.config.token,
                )
                return self._read_label_file(Path(downloaded))
            except Exception:
                continue

        try:
            samples_path = hf_hub_download(
                repo_id=self.config.dataset_repo_id,
                repo_type="dataset",
                filename=self.config.dataset_labels_file,
                cache_dir=str(self.config.cache_dir),
                token=self.config.token,
            )
            return self._extract_labels_from_wlasl(Path(samples_path))
        except Exception as exc:
            raise RecognitionConfigurationError(
                "Could not resolve a label map for the WLASL model. Set RECOGNITION_LABELS_PATH to a JSON label file."
            ) from exc

    def _read_label_file(self, path: Path) -> dict[int, str]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return {index: str(label) for index, label in enumerate(payload)}
        if isinstance(payload, dict):
            if all(str(key).isdigit() for key in payload.keys()):
                return {int(key): str(value) for key, value in payload.items()}
            return {int(value): str(key) for key, value in payload.items()}
        raise RecognitionConfigurationError(f"Unsupported label map format in {path}.")

    def _extract_labels_from_wlasl(self, path: Path) -> dict[int, str]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        discovered = {}
        ordered_labels = []
        seen_labels = set()

        def visit(value: Any):
            if isinstance(value, dict):
                label = None
                label_id = None
                gloss = value.get("gloss")
                if isinstance(gloss, dict):
                    label = gloss.get("label")
                elif isinstance(gloss, str):
                    label = gloss

                if label is None:
                    for key in ("label", "word", "name", "text"):
                        candidate = value.get(key)
                        if isinstance(candidate, str):
                            label = candidate
                            break

                for key in ("label_id", "target", "class_id", "class", "index", "gloss_id"):
                    candidate = value.get(key)
                    if isinstance(candidate, int):
                        label_id = candidate
                        break

                if label is not None and label_id is not None:
                    discovered[label_id] = label
                if label is not None:
                    normalized = normalize_label(label)
                    if normalized not in seen_labels:
                        seen_labels.add(normalized)
                        ordered_labels.append(label)

                for nested in value.values():
                    visit(nested)
            elif isinstance(value, list):
                for nested in value:
                    visit(nested)

        visit(payload)
        if not discovered and ordered_labels:
            return {index: label for index, label in enumerate(ordered_labels)}
        if not discovered:
            raise RecognitionConfigurationError(
                "WLASL labels could not be extracted automatically. Provide RECOGNITION_LABELS_PATH."
            )
        return discovered

    def _infer_class_count(self, label_map: dict[int, str]) -> int:
        if label_map:
            return max(label_map.keys()) + 1
        digits = "".join(character for character in self.config.variant if character.isdigit())
        if digits:
            return int(digits)
        raise RecognitionConfigurationError("Could not infer the class count for the configured model variant.")

    def _resolve_allowed_indices(self, allowed_signs: list[str]) -> list[int]:
        normalized_map = {}
        for index, label in self._label_map.items():
            normalized_map.setdefault(normalize_label(label), []).append(index)

        indices = []
        for sign in allowed_signs:
            aliases = SUPPORTED_SIGN_ALIASES.get(sign, [sign])
            for alias in aliases:
                indices.extend(normalized_map.get(normalize_label(alias), []))
        return sorted(set(indices))

    def _resolve_sign_name(self, model_label: str, allowed_signs: list[str]) -> str:
        normalized_model_label = normalize_label(model_label)
        for sign in allowed_signs:
            aliases = SUPPORTED_SIGN_ALIASES.get(sign, [sign])
            if normalized_model_label in {normalize_label(alias) for alias in aliases}:
                return sign
        return normalized_model_label

    def _torch_is_available(self) -> bool:
        try:
            import torch  # noqa: F401
        except ImportError:
            return False
        return True

    def _hub_is_available(self) -> bool:
        try:
            import huggingface_hub  # noqa: F401
        except ImportError:
            return False
        return True


class RecognitionService:
    def __init__(self):
        self.config = self._load_config()
        self.extractor = None
        self.backend = WlaslTGCNBackend(self.config)

    def health(self) -> dict[str, Any]:
        status = self.backend.status()
        try:
            self._get_extractor()
        except RecognitionDependencyError as exc:
            status["dependencies_ready"] = False
            status["warnings"].append(str(exc))
        return status

    def predict_frames(
        self,
        frames: list[np.ndarray],
        lesson_ids: list[int],
        top_k: int = 3,
        include_tracking: bool = True,
    ) -> PredictionResult:
        allowed_signs = self._load_allowed_signs(lesson_ids)
        sequence, tracking_data = self._get_extractor().extract_sequence(frames, self.backend.num_samples)
        candidates, warnings = self.backend.predict(sequence, allowed_signs=allowed_signs, top_k=top_k)

        if not candidates:
            raise RecognitionConfigurationError("No predictions were produced by the configured model.")

        best_candidate = candidates[0]
        return PredictionResult(
            predicted_sign=best_candidate.sign,
            confidence=best_candidate.score,
            candidates=candidates,
            tracking_data=tracking_data if include_tracking else {},
            warnings=warnings,
            model={
                "repo_id": self.config.repo_id,
                "variant": self.config.variant,
                "allowed_signs": allowed_signs,
            },
        )

    def _load_config(self) -> RecognitionSettings:
        cache_dir = Path(
            os.getenv(
                "RECOGNITION_CACHE_DIR",
                Path(settings.BASE_DIR).parent / "model_cache",
            )
        )
        cache_dir.mkdir(parents=True, exist_ok=True)

        labels_path = os.getenv("RECOGNITION_LABELS_PATH")
        holistic_task_path = Path(
            os.getenv(
                "MEDIAPIPE_HOLISTIC_TASK_PATH",
                cache_dir / "mediapipe" / "holistic_landmarker.task",
            )
        )
        return RecognitionSettings(
            repo_id=os.getenv("RECOGNITION_MODEL_REPO", "sharonn18/tgcn-wlasl"),
            variant=os.getenv("RECOGNITION_MODEL_VARIANT", "asl2000"),
            dataset_repo_id=os.getenv("RECOGNITION_DATASET_REPO", "Voxel51/WLASL"),
            dataset_labels_file=os.getenv("RECOGNITION_DATASET_LABELS_FILE", "samples.json"),
            token=os.getenv("HF_TOKEN"),
            cache_dir=cache_dir,
            labels_path=Path(labels_path) if labels_path else None,
            holistic_task_path=holistic_task_path,
            holistic_task_url=os.getenv(
                "MEDIAPIPE_HOLISTIC_TASK_URL",
                "https://storage.googleapis.com/mediapipe-models/holistic_landmarker/holistic_landmarker/float16/latest/holistic_landmarker.task",
            ),
            supported_lessons=env_list("RECOGNITION_SUPPORTED_LESSONS", DEFAULT_SUPPORTED_LESSONS),
        )

    def _load_allowed_signs(self, lesson_ids: list[int]) -> list[str]:
        signs = list(
            Exercise.objects.filter(lesson_id__in=lesson_ids)
            .order_by("lesson_id", "order", "id")
            .values_list("expected_sign", flat=True)
            .distinct()
        )
        if not signs:
            raise RecognitionConfigurationError("No lesson signs were found for the requested lesson ids.")
        return [normalize_label(sign) for sign in signs]

    def _get_extractor(self) -> MediaPipeHolisticExtractor:
        if self.extractor is None:
            self.extractor = MediaPipeHolisticExtractor(self.config)
        return self.extractor


@lru_cache(maxsize=1)
def get_recognition_service() -> RecognitionService:
    return RecognitionService()

