from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    xp = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    avatar_url = models.URLField(blank=True)

    def __str__(self):
        return self.username
