from django.urls import path
from .views import (
    LessonListView, LessonDetailView,
    AttemptCreateView, AttemptUpdateView, AttemptDetailView,
    UserAttemptsView, UserProgressView, VerifySignView,
)

urlpatterns = [
    path('lessons/', LessonListView.as_view(), name='lesson-list'),
    path('lessons/<slug:slug>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('attempts/', AttemptCreateView.as_view(), name='attempt-create'),
    path('attempts/<int:pk>/', AttemptUpdateView.as_view(), name='attempt-update'),
    path('attempts/<int:pk>/detail/', AttemptDetailView.as_view(), name='attempt-detail'),
    path('attempts/<int:pk>/verify/', VerifySignView.as_view(), name='attempt-verify'),
    path('me/attempts/', UserAttemptsView.as_view(), name='user-attempts'),
    path('me/progress/', UserProgressView.as_view(), name='user-progress'),
]
