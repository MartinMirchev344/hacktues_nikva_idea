from unittest.mock import patch
from types import SimpleNamespace

from rest_framework import status
from rest_framework.test import APITestCase

from .views import classify_asl_landmarks


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
    def test_classify_v_when_index_and_middle_are_spread(self):
        landmarks = build_two_finger_landmarks(0.34, 0.66)

        letter, confidence = classify_asl_landmarks(landmarks)

        self.assertEqual(letter, "v")
        self.assertGreater(confidence, 0)

    def test_classify_r_when_index_and_middle_are_close(self):
        landmarks = build_two_finger_landmarks(0.48, 0.52)

        letter, confidence = classify_asl_landmarks(landmarks)

        self.assertEqual(letter, "r")
        self.assertGreater(confidence, 0)

    def test_return_none_for_ambiguous_two_finger_shape(self):
        landmarks = build_two_finger_landmarks(0.44, 0.56)

        letter, confidence = classify_asl_landmarks(landmarks)

        self.assertIsNone(letter)
        self.assertEqual(confidence, 0.0)

