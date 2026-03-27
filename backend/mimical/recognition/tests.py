from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from PIL import Image

from .views import analyze_asl_landmarks, classify_asl_landmarks


def make_landmark(x: float, y: float, z: float = 0.0):
    return SimpleNamespace(x=x, y=y, z=z)


def build_two_finger_landmarks(index_tip_x: float, middle_tip_x: float):
    points = [(0.5, 1.0, 0.0)] * 21

    # Wrist
    points[0] = (0.50, 1.00, 0.0)

    # Thumb tucked in so this is not classified as K
    points[1] = (0.53, 0.88, 0.0)
    points[2] = (0.55, 0.84, 0.0)
    points[3] = (0.57, 0.80, 0.0)
    points[4] = (0.58, 0.78, 0.0)

    # Index finger up
    points[5] = (0.44, 0.72, 0.0)
    points[6] = (0.43, 0.60, 0.0)
    points[7] = (0.42, 0.42, 0.0)
    points[8] = (index_tip_x, 0.18, 0.0)

    # Middle finger up
    points[9] = (0.56, 0.72, 0.0)
    points[10] = (0.55, 0.60, 0.0)
    points[11] = (0.54, 0.40, 0.0)
    points[12] = (middle_tip_x, 0.18, 0.0)

    # Ring finger folded
    points[13] = (0.61, 0.76, 0.0)
    points[14] = (0.61, 0.86, 0.0)
    points[15] = (0.61, 0.90, 0.0)
    points[16] = (0.61, 0.92, 0.0)

    # Pinky folded
    points[17] = (0.68, 0.77, 0.0)
    points[18] = (0.68, 0.87, 0.0)
    points[19] = (0.68, 0.91, 0.0)
    points[20] = (0.68, 0.93, 0.0)

    return [make_landmark(*point) for point in points]


def build_k_landmarks():
    landmarks = build_two_finger_landmarks(0.36, 0.62)
    landmarks[4] = make_landmark(0.55, 0.63, 0.0)
    return landmarks


def build_four_finger_landmarks(*, pinky_up: bool, spread: float):
    points = [(0.5, 1.0, 0.0)] * 21

    points[0] = (0.50, 1.00, 0.0)

    # Thumb tucked across the palm.
    points[1] = (0.53, 0.88, 0.0)
    points[2] = (0.52, 0.82, 0.0)
    points[3] = (0.50, 0.78, 0.0)
    points[4] = (0.49, 0.76, 0.0)

    points[5] = (0.36, 0.74, 0.0)
    points[6] = (0.34, 0.60, 0.0)
    points[7] = (0.33, 0.40, 0.0)
    points[8] = (0.33 - spread, 0.16, 0.0)

    points[9] = (0.49, 0.72, 0.0)
    points[10] = (0.49, 0.58, 0.0)
    points[11] = (0.49, 0.38, 0.0)
    points[12] = (0.49, 0.15, 0.0)

    points[13] = (0.62, 0.74, 0.0)
    points[14] = (0.63, 0.60, 0.0)
    points[15] = (0.64, 0.40, 0.0)
    points[16] = (0.65 + spread, 0.16, 0.0)

    points[17] = (0.74, 0.77, 0.0)
    if pinky_up:
        points[18] = (0.76, 0.62, 0.0)
        points[19] = (0.78, 0.42, 0.0)
        points[20] = (0.80 + spread, 0.20, 0.0)
    else:
        points[18] = (0.75, 0.88, 0.0)
        points[19] = (0.75, 0.91, 0.0)
        points[20] = (0.75, 0.94, 0.0)

    return [make_landmark(*point) for point in points]


def build_test_image():
    image = Image.new("RGB", (12, 12), color="white")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return SimpleUploadedFile("hand.jpg", buffer.getvalue(), content_type="image/jpeg")


class RecognitionHealthTests(APITestCase):
    @patch("recognition.views.get_recognition_service")
    def test_health_endpoint_returns_status(self, mock_service_factory):
        mock_service = mock_service_factory.return_value
        mock_service.health.return_value = {
            "status": "ready",
            "model_ready": True,
            "dependencies_ready": True,
            "supported_lessons": [1, 2, 5],
            "configured_model": "sharonn18/tgcn-wlasl",
            "configured_variant": "asl2000",
            "cache_dir": "C:/tmp",
            "warnings": [],
        }

        response = self.client.get("/api/recognition/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ready")


class AlphabetClassifierTests(APITestCase):
    def test_classify_k_when_thumb_supports_middle_finger(self):
        letter, confidence = classify_asl_landmarks(build_k_landmarks())

        self.assertEqual(letter, "k")
        self.assertGreaterEqual(confidence, 50.0)

    def test_classify_v_when_index_and_middle_are_spread(self):
        landmarks = build_two_finger_landmarks(0.34, 0.66)

        letter, confidence = classify_asl_landmarks(landmarks)

        self.assertEqual(letter, "v")
        self.assertGreater(confidence, 0)

    def test_classify_r_when_index_and_middle_are_close(self):
        landmarks = build_two_finger_landmarks(0.56, 0.46)

        letter, confidence = classify_asl_landmarks(landmarks)

        self.assertEqual(letter, "r")
        self.assertGreater(confidence, 0)

    def test_return_none_for_ambiguous_two_finger_shape(self):
        landmarks = build_two_finger_landmarks(0.44, 0.56)

        letter, confidence = classify_asl_landmarks(landmarks)

        self.assertIsNone(letter)
        self.assertEqual(confidence, 0.0)

    def test_analysis_distinguishes_b_from_w_using_pinky_and_spread(self):
        b_prediction = analyze_asl_landmarks(build_four_finger_landmarks(pinky_up=True, spread=0.00))
        w_prediction = analyze_asl_landmarks(build_four_finger_landmarks(pinky_up=False, spread=0.10))

        self.assertEqual(b_prediction["predicted_letter"], "b")
        self.assertEqual(w_prediction["predicted_letter"], "w")


class AlphabetPredictViewTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            email="tester@example.com",
            password="password123",
        )
        self.client.force_authenticate(self.user)

    @patch("recognition.views.detect_hand_landmarks")
    def test_returns_targeted_feedback_when_prediction_differs_from_expected(self, mock_detect_hand_landmarks):
        mock_detect_hand_landmarks.return_value = build_four_finger_landmarks(pinky_up=True, spread=0.00)

        response = self.client.post(
            "/api/recognition/alphabet/predict/",
            {"image": build_test_image(), "expected_letter": "w"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["predicted_letter"], "b")
        self.assertEqual(response.data["expected_letter"], "w")
        self.assertFalse(response.data["is_correct"])
        self.assertTrue(any("pinky" in item.lower() for item in response.data["feedback_items"]))
