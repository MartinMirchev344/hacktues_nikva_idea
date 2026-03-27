from django.urls import path
from .views import (
    RegisterView, LoginView,
    ForgotPasswordView, ResetPasswordView,
    ProfileView, LeaderboardView, StreakStatusView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('me/', ProfileView.as_view(), name='profile'),
    path('me/streak/', StreakStatusView.as_view(), name='streak-status'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
