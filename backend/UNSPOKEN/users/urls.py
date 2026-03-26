from django.urls import path
from .views import RegisterView, LoginView, ProfileView, LeaderboardView, StreakStatusView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', ProfileView.as_view(), name='profile'),
    path('me/streak/', StreakStatusView.as_view(), name='streak-status'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
