import io
from pathlib import Path

import numpy as np
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RecognitionHealthSerializer
from .services import get_recognition_service

HAND_LANDMARK_MODEL = Path(settings.BASE_DIR).parent / 'data' / 'models' / 'hand_landmarker.task'


def detect_hand_landmarks(pil_image):
    """
    Detect 21 hand landmarks using MediaPipe Tasks API.
    Returns list of NormalizedLandmark, or None if no hand found.
    """
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision

    img_np = np.array(pil_image)

    options = mp_vision.HandLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(HAND_LANDMARK_MODEL)),
        num_hands=1,
        min_hand_detection_confidence=0.3,
        min_hand_presence_confidence=0.3,
        min_tracking_confidence=0.3,
    )
    with mp_vision.HandLandmarker.create_from_options(options) as detector:
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_np)
        result = detector.detect(mp_img)

    if result.hand_landmarks:
        return result.hand_landmarks[0]
    return None


def classify_asl_landmarks(landmarks):
    """
    Rule-based ASL letter classifier from 21 hand landmarks.
    Works for the letters: A B D F J K M R T W
    Returns (letter, confidence_float).
    """
    lm = np.array([[l.x, l.y, l.z] for l in landmarks])  # (21, 3)

    wrist = lm[0, :2]

    # Hand scale: wrist → middle-finger MCP (landmark 9)
    hand_size = np.linalg.norm(lm[9, :2] - wrist)
    if hand_size < 1e-6:
        return None, 0.0

    def extended(tip, pip):
        """True if fingertip is further from wrist than the PIP joint."""
        return (np.linalg.norm(lm[tip, :2] - wrist) >
                np.linalg.norm(lm[pip, :2] - wrist) * 1.15)

    index_up  = extended(8,  6)
    middle_up = extended(12, 10)
    ring_up   = extended(16, 14)
    pinky_up  = extended(20, 18)

    # Palm centre x (between index MCP and pinky MCP)
    palm_cx = (lm[5, 0] + lm[17, 0]) / 2.0

    # Thumb sideways: tip x is noticeably away from the palm centre line
    thumb_sideways = abs(lm[4, 0] - palm_cx) > hand_size * 0.35

    def dist(a, b):
        """Normalised 2-D distance between two landmark indices."""
        return np.linalg.norm(lm[a, :2] - lm[b, :2]) / hand_size

    thumb_index_touch   = dist(4, 8)  < 0.40
    # T: thumb tucked between index and middle at MCP level (near index MCP)
    thumb_near_index_mcp = dist(4, 5) < 0.40

    # ── Pattern matching ──────────────────────────────────────────────────────
    # B: all four fingers up, thumb folded
    if index_up and middle_up and ring_up and pinky_up:
        return 'b', 82.0

    # W: index + middle + ring up, pinky down
    if index_up and middle_up and ring_up and not pinky_up:
        return 'w', 80.0

    # K: index + middle up, thumb forward/sideways
    if index_up and middle_up and not ring_up and not pinky_up and thumb_sideways:
        return 'k', 78.0

    # R: index + middle up (crossed), thumb in
    if index_up and middle_up and not ring_up and not pinky_up:
        return 'r', 74.0

    # D: only index finger up
    if index_up and not middle_up and not ring_up and not pinky_up:
        return 'd', 79.0

    # J / I: only pinky up
    if pinky_up and not index_up and not middle_up and not ring_up:
        return 'j', 77.0

    # F: index bent/touching thumb, middle + ring + pinky up
    if not index_up and middle_up and ring_up and pinky_up:
        return 'f', 75.0

    # Fist family: no fingers extended
    if not index_up and not middle_up and not ring_up and not pinky_up:
        if thumb_sideways:
            return 'a', 72.0          # A: fist, thumb to the side
        if thumb_near_index_mcp:
            return 't', 67.0          # T: thumb between index and middle at base
        return 'm', 63.0              # M / S default

    return None, 0.0


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
            from PIL import Image, ImageOps

            raw_bytes = image_file.read()
            raw = Image.open(io.BytesIO(raw_bytes))
            image = ImageOps.exif_transpose(raw).convert('RGB')

            landmarks = detect_hand_landmarks(image)

            if landmarks is None:
                return Response(
                    {'detail': 'No hand detected in the image. Make sure your hand is clearly visible.'},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            letter, confidence = classify_asl_landmarks(landmarks)

            if not letter:
                return Response(
                    {'detail': 'Could not identify the hand sign. Try a different angle.'},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            return Response({
                'predicted_letter': letter,
                'confidence': round(confidence, 1),
                'top_predictions': [{'letter': letter, 'confidence': round(confidence, 1)}],
            })

        except Exception as exc:
            return Response(
                {'detail': f'Prediction failed: {exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
