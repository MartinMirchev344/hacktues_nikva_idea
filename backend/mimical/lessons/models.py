from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Lesson(models.Model):
    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.BEGINNER,
    )
    sign_language = models.CharField(max_length=50, default="ASL")
    estimated_duration_minutes = models.PositiveIntegerField(default=10)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["difficulty", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Exercise(models.Model):
    class ExerciseType(models.TextChoices):
        GESTURE_PRACTICE = "gesture_practice", "Gesture Practice"
        MOVEMENT_DRILL = "movement_drill", "Movement Drill"
        QUIZ = "quiz", "Quiz"

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="exercises",
    )
    title = models.CharField(max_length=255)
    exercise_type = models.CharField(
        max_length=30,
        choices=ExerciseType.choices,
        default=ExerciseType.GESTURE_PRACTICE,
    )
    prompt = models.TextField()
    instructions = models.TextField(blank=True)
    expected_sign = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)
    repetitions_target = models.PositiveIntegerField(default=1)
    passing_score = models.PositiveIntegerField(default=70)
    target_pose_data = models.JSONField(default=dict, blank=True)
    target_motion_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["lesson", "order", "id"]
        unique_together = ("lesson", "order")

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class Attempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        NEEDS_REVIEW = "needs_review", "Needs Review"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    accuracy_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    speed_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    handshape_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    detected_sign = models.CharField(max_length=255, blank=True)
    coach_summary = models.TextField(blank=True)
    feedback_items = models.JSONField(default=list, blank=True)
    tracking_data = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.exercise.title} ({self.status})"


class UserLessonProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="user_progress",
    )
    is_completed = models.BooleanField(default=False)
    best_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    attempts_count = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "lesson")

    def __str__(self):
        return f"{self.user} - {self.lesson.title} ({'done' if self.is_completed else 'in progress'})"
