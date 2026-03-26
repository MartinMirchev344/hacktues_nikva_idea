from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from users.models import User

from .models import Attempt, Exercise, Lesson


class VerifySignApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester",
            email="tester@example.com",
            password="UnspokenPass123!",
        )
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        self.lesson = Lesson.objects.create(
            title="Greetings",
            description="Practice greetings.",
            difficulty="beginner",
            sign_language="ASL",
            estimated_duration_minutes=5,
            is_published=True,
        )
        self.exercise = Exercise.objects.create(
            lesson=self.lesson,
            title="Hello",
            prompt="Sign hello",
            instructions="Wave with your dominant hand.",
            expected_sign="hello",
            order=1,
            repetitions_target=1,
            passing_score=70,
        )
        self.attempt = Attempt.objects.create(user=self.user, exercise=self.exercise)

    @patch("lessons.views.verify_sign")
    def test_verify_endpoint_returns_model_output(self, mock_verify_sign):
        mock_verify_sign.return_value = {
            "is_correct": True,
            "confidence": 91.5,
            "detected_sign": "hello",
            "accuracy_score": 90.0,
            "handshape_score": 93.0,
            "speed_score": 100.0,
            "coach_summary": "Great job!",
            "feedback_items": [],
        }

        video = SimpleUploadedFile("sign.mp4", b"fake-video", content_type="video/mp4")
        response = self.client.post(
            f"/api/attempts/{self.attempt.id}/verify/",
            {"video": video},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detected_sign"], "hello")
        mock_verify_sign.assert_called_once()

    def test_verify_endpoint_requires_video(self):
        response = self.client.post(
            f"/api/attempts/{self.attempt.id}/verify/",
            {},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "No video provided.")

