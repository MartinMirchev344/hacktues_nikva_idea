from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AuthApiTests(APITestCase):
    def test_register_creates_user_and_returns_token(self):
        response = self.client.post(
            reverse('register'),
            {
                'email': 'newuser@example.com',
                'password': 'MimicalPass123!',
                'password2': 'MimicalPass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_login_returns_existing_user_token(self):
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='MimicalPass123!',
        )

        response = self.client.post(
            reverse('login'),
            {
                'email': 'existing@example.com',
                'password': 'MimicalPass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'existinguser')
