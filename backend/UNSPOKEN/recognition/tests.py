from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase


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

