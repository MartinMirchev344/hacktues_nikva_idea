import os
import tempfile

from recognition.services import get_recognition_service, normalize_label


def verify_sign(video_file, expected_sign: str, lesson_id: int | None = None) -> dict:
    frames = extract_video_frames(video_file)
    lesson_ids = [lesson_id] if lesson_id is not None else list(range(1, 20))
    prediction = get_recognition_service().predict_frames(
        frames=frames,
        lesson_ids=lesson_ids,
        top_k=3,
        include_tracking=True,
    )

    detected_sign = normalize_label(prediction.predicted_sign)
    normalized_expected = normalize_label(expected_sign)
    is_correct = detected_sign == normalized_expected

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
        feedback_items = ["No landmarks detected — try again with better lighting and positioning."]
    elif is_correct:
        coach_summary = f"Nice work! The model recognized '{detected_sign}' with {confidence:.0f}% confidence."
        feedback_items = []
    else:
        coach_summary = (
            f"The model thinks you signed '{detected_sign}' instead of '{normalized_expected}'. "
            "Try centering your hands, signing more slowly, and ensuring good lighting."
        )
        feedback_items = [
            f"Expected: {normalized_expected}",
            f"Detected: {detected_sign}",
        ]
        if prediction.candidates:
            top_candidates = ", ".join(
                f"{c.sign} ({round(c.score * 100, 0):.0f}%)" for c in prediction.candidates[:3]
            )
            feedback_items.append(f"Top predictions: {top_candidates}")

    return {
        "is_correct": is_correct,
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


def extract_video_frames(video_file):
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is required to process uploaded videos.") from exc

    suffix = os.path.splitext(getattr(video_file, "name", "upload.mp4"))[1] or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        for chunk in video_file.chunks():
            temp_file.write(chunk)
        temp_path = temp_file.name

    capture = cv2.VideoCapture(temp_path)
    frames = []
    try:
        while True:
            success, frame = capture.read()
            if not success:
                break
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(rgb_frame)
    finally:
        capture.release()
        os.unlink(temp_path)

    if not frames:
        raise RuntimeError("No frames could be extracted from the uploaded video.")

    return frames

