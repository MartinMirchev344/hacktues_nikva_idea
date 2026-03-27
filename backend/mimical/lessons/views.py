from decimal import Decimal
from django.db.models import Count
from django.utils import timezone
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Lesson, Exercise, Attempt, UserLessonProgress
from .serializers import (
    LessonListSerializer, LessonDetailSerializer,
    AttemptSerializer, AttemptCreateUpdateSerializer,
    UserLessonProgressSerializer,
)
from .sign_verifier import verify_sign

XP_PER_LESSON = 20


class LessonListView(generics.ListAPIView):
    serializer_class = LessonListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'sign_language']
    ordering_fields = ['difficulty', 'title', 'created_at']

    def get_queryset(self):
        qs = Lesson.objects.filter(is_published=True).annotate(exercise_count=Count('exercises'))
        sign_language = self.request.query_params.get('sign_language')
        difficulty = self.request.query_params.get('difficulty')
        if sign_language:
            qs = qs.filter(sign_language__iexact=sign_language)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        return qs


class LessonDetailView(generics.RetrieveAPIView):
    serializer_class = LessonDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        return Lesson.objects.filter(is_published=True).prefetch_related('exercises')


class AttemptCreateView(generics.CreateAPIView):
    """
    POST /api/attempts/
    Start a new attempt for an exercise.
    Body: { "exercise": <exercise_id> }
    """
    serializer_class = AttemptCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AttemptUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/attempts/<id>/
    Submit hand-tracking results for an attempt.

    Body (from mobile hand-tracking module):
    {
        "status": "completed",
        "accuracy_score": 87.5,
        "handshape_score": 90.0,
        "speed_score": 82.0,
        "detected_sign": "hello",
        "coach_summary": "Good form, slightly slow.",
        "feedback_items": ["Extend fingers more", "Steady wrist"],
        "tracking_data": { ... },   // raw landmark data, optional
        "completed_at": "2026-03-26T12:00:00Z"
    }

    When the attempt is marked completed, the overall score is computed,
    user XP and streak are updated, and lesson progress is recorded.
    """
    serializer_class = AttemptCreateUpdateSerializer
    http_method_names = ['patch']

    def get_queryset(self):
        return Attempt.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        attempt = serializer.save()

        if attempt.status != Attempt.Status.COMPLETED:
            return

        # Compute overall score as average of available subscores
        subscores = [s for s in [attempt.accuracy_score, attempt.handshape_score, attempt.speed_score] if s is not None]
        if subscores:
            attempt.score = sum(subscores) / len(subscores)
            attempt.save(update_fields=['score'])

        exercise = attempt.exercise
        lesson = exercise.lesson
        passing = Decimal(exercise.passing_score)

        # Update lesson progress
        progress, _ = UserLessonProgress.objects.get_or_create(
            user=self.request.user, lesson=lesson
        )
        progress.attempts_count += 1
        if attempt.score and attempt.score > progress.best_score:
            progress.best_score = attempt.score
        if attempt.score and attempt.score >= passing and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()
        progress.save()

        # Award XP and update streak on completion (only if passed)
        if attempt.score and attempt.score >= passing:
            user = self.request.user
            user.xp += XP_PER_LESSON
            today = timezone.now().date()
            if user.last_activity_date != today:
                if user.last_activity_date and (today - user.last_activity_date).days == 1:
                    user.streak += 1
                else:
                    user.streak = 1
                user.last_activity_date = today
            user.save()

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        response = super().update(request, *args, **kwargs)

        attempt = self.get_object()
        if attempt.status == Attempt.Status.COMPLETED:
            response.data['total_xp'] = request.user.xp
            response.data['streak'] = request.user.streak

        return response


class AttemptDetailView(generics.RetrieveAPIView):
    serializer_class = AttemptSerializer

    def get_queryset(self):
        return Attempt.objects.filter(user=self.request.user).select_related('exercise', 'exercise__lesson')


class UserAttemptsView(generics.ListAPIView):
    serializer_class = AttemptSerializer

    def get_queryset(self):
        return Attempt.objects.filter(user=self.request.user).select_related('exercise', 'exercise__lesson')


class UserProgressView(generics.ListAPIView):
    serializer_class = UserLessonProgressSerializer

    def get_queryset(self):
        return UserLessonProgress.objects.filter(user=self.request.user).select_related('lesson')


class VerifySignView(APIView):
    """
    POST /api/attempts/<id>/verify/
    Send a camera frame to the hand-tracking model and get back verification results.

    Request: multipart/form-data
        image — the camera frame (JPEG/PNG)

    Response 200:
    {
        "is_correct": true,
        "confidence": 91.5,
        "detected_sign": "hello",
        "accuracy_score": 90.0,
        "handshape_score": 93.0,
        "speed_score": 100.0,
        "coach_summary": "Great job!",
        "feedback_items": []
    }
    """

    def post(self, request, pk):
        try:
            attempt = Attempt.objects.select_related('exercise').get(pk=pk, user=request.user)
        except Attempt.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        video = request.FILES.get('video')
        if not video:
            return Response({"detail": "No video provided."}, status=status.HTTP_400_BAD_REQUEST)

<<<<<<< Updated upstream:backend/UNSPOKEN/lessons/views.py
        try:
            result = verify_sign(video, attempt.exercise.expected_sign, lesson_id=attempt.exercise.lesson_id)
        except Exception as exc:
            return Response({"detail": f"Recognition failed: {exc}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
=======
        result = verify_sign(
            video,
            attempt.exercise.expected_sign,
            lesson_ids=[attempt.exercise.lesson_id],
        )
>>>>>>> Stashed changes:backend/mimical/lessons/views.py
        return Response(result, status=status.HTTP_200_OK)
