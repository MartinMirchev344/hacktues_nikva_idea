from django.urls import reverse
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase

from .models import OTPCode, User


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

    def test_login_sends_otp_email(self):
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
        self.assertEqual(response.data, {'needs_otp': True, 'email': 'existing@example.com'})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['existing@example.com'])
        self.assertIn('verification code', mail.outbox[0].body.lower())
        self.assertTrue(
            OTPCode.objects.filter(email='existing@example.com', purpose=OTPCode.Purpose.LOGIN).exists()
        )

    def test_verify_otp_returns_token_for_existing_user(self):
        user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='MimicalPass123!',
        )
        otp = OTPCode.generate_for(user.email, OTPCode.Purpose.LOGIN)

        response = self.client.post(
            reverse('verify-otp'),
            {
                'email': user.email,
                'code': otp.code,
                'purpose': OTPCode.Purpose.LOGIN,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'existinguser')
