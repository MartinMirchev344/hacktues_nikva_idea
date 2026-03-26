"""
Sign verification module — plug the hand-tracking ML model in here.

Called by: POST /api/attempts/<id>/verify/
Input:  video_file    — an InMemoryUploadedFile (from request.FILES['video'])
        expected_sign — str, e.g. "hello" (from exercise.expected_sign)
Output: dict with keys:
            is_correct    — bool
            confidence    — float 0-100
            detected_sign — str (what the model thinks it saw, or "" if nothing)
            accuracy_score    — float 0-100
            handshape_score   — float 0-100
            speed_score       — float 0-100
            coach_summary     — str
            feedback_items    — list[str]
"""


def verify_sign(video_file, expected_sign: str) -> dict:
    """
    TODO: replace this stub with the real model inference.

    `video_file` is a Django InMemoryUploadedFile containing the recorded video.
    Read the raw bytes with:
        video_bytes = video_file.read()
    Or save it to a temp file and pass the path to MediaPipe:
        import tempfile, os
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
            tmp.write(video_file.read())
            tmp_path = tmp.name
        # run mediapipe on tmp_path
        os.unlink(tmp_path)

    Return a dict matching the shape above.
    """
    # --- STUB — remove everything below and add real inference ---
    return {
        "is_correct": False,
        "confidence": 0.0,
        "detected_sign": "",
        "accuracy_score": 0.0,
        "handshape_score": 0.0,
        "speed_score": 100.0,
        "coach_summary": "Model not implemented yet.",
        "feedback_items": [],
    }
