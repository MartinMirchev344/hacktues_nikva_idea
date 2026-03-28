from __future__ import annotations

from recognition.compare import compare_video_to_template, has_template_support
from recognition.feedback_rules import build_exercise_feedback
from recognition.mediapipe_utils import extract_video_frames, normalize_sign_name


def verify_sign(
    video_file,
    expected_sign: str,
    lesson_id: int | None = None,
    passing_score: float = 70.0,
) -> dict:
    normalized_expected = normalize_sign_name(expected_sign)

    if has_template_support(normalized_expected):
        try:
            comparison = compare_video_to_template(
                video_file,
                normalized_expected,
                passing_score=passing_score,
            )
            coach_summary, feedback_items = build_exercise_feedback(normalized_expected, comparison)

            return {
                "exercise": comparison["exercise"],
                "is_correct": comparison["correct"],
                "correct": comparison["correct"],
                "score": comparison["score"],
                "confidence": comparison["score"],
                "detected_sign": normalized_expected,
                "accuracy_score": comparison["score"],
                "handshape_score": comparison["shape_score"],
                "speed_score": comparison["motion_score"],
                "position_score": comparison["position_score"],
                "coach_summary": coach_summary,
                "feedback_items": feedback_items,
                "tracking_data": comparison["tracking_data"],
                "metrics": comparison["metrics"],
                "candidates": [],
            }
        except Exception as exc:
            raise RuntimeError(
                f"LOCAL_TEMPLATE_ERROR[{type(exc).__name__}] sign={normalized_expected}: {exc}"
            ) from exc

    return _verify_with_classifier(video_file, normalized_expected, lesson_id=lesson_id)


def _verify_with_classifier(video_file, expected_sign: str, lesson_id: int | None = None) -> dict:
    from recognition.services import get_recognition_service, normalize_label

    frames = extract_video_frames(video_file)
    lesson_ids = [lesson_id] if lesson_id is not None else list(range(1, 20))
    prediction = get_recognition_service().predict_frames(
        frames=frames,
        lesson_ids=lesson_ids,
        top_k=3,
        include_tracking=True,
    )

    detected_sign = normalize_label(prediction.predicted_sign)
    is_correct = detected_sign == expected_sign
    no_landmarks = prediction.tracking_data.get("frames_with_landmarks", 1) == 0
    confidence = round(prediction.confidence * 100, 2)
    accuracy_score = confidence if is_correct else round(max(confidence * 0.6, 5.0), 2)
    handshape_score = round(max(confidence * 0.92, 5.0), 2)
    speed_score = 100.0

    if no_landmarks:
        coach_summary = (
            "Your hands and body were not detected in the video. "
            "Make sure your hands and upper body are clearly visible, well-lit, and centered in the frame."
        )
        feedback_items = ["No landmarks detected - try again with better lighting and positioning."]
    elif is_correct:
        coach_summary = f"Nice work! The model recognized '{detected_sign}' with {confidence:.0f}% confidence."
        feedback_items = []
    else:
        coach_summary = (
            f"The model thinks you signed '{detected_sign}' instead of '{expected_sign}'. "
            "Try centering your hands, signing more slowly, and ensuring good lighting."
        )
        feedback_items = [
            f"Expected: {expected_sign}",
            f"Detected: {detected_sign}",
        ]
        if prediction.candidates:
            top_candidates = ", ".join(
                f"{candidate.sign} ({round(candidate.score * 100, 0):.0f}%)"
                for candidate in prediction.candidates[:3]
            )
            feedback_items.append(f"Top predictions: {top_candidates}")

    return {
        "exercise": expected_sign,
        "is_correct": is_correct,
        "correct": is_correct,
        "score": accuracy_score,
        "confidence": confidence,
        "detected_sign": detected_sign,
        "accuracy_score": accuracy_score,
        "handshape_score": handshape_score,
        "speed_score": speed_score,
        "coach_summary": coach_summary,
        "feedback_items": feedback_items,
        "tracking_data": prediction.tracking_data,
        "candidates": [
            {
                "sign": candidate.sign,
                "score": round(candidate.score * 100, 2),
                "model_label": candidate.model_label,
                "class_index": candidate.class_index,
            }
            for candidate in prediction.candidates
        ],
    }
