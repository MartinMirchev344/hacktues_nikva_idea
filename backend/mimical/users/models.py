import random
import string
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    xp = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    avatar_url = models.URLField(blank=True)

    def __str__(self):
        return self.username


class OTPCode(models.Model):
    class Purpose(models.TextChoices):
        PASSWORD_RESET = 'password_reset', 'Password Reset'

    email = models.EmailField()
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.created_at + timedelta(minutes=10)

    @classmethod
    def generate_for(cls, email, purpose):
        cls.objects.filter(email=email, purpose=purpose, is_used=False).delete()
        code = ''.join(random.choices(string.digits, k=6))
        return cls.objects.create(email=email, code=code, purpose=purpose)
