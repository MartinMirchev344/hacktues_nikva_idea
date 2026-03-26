from django.urls import path
from .views import RegisterView, ProfileView, LeaderboardView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', ProfileView.as_view(), name='profile'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]

try:
    from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
except ImportError:
    TokenObtainPairView = None
    TokenRefreshView = None

if TokenObtainPairView is not None and TokenRefreshView is not None:
    urlpatterns.extend([
        path('login/', TokenObtainPairView.as_view(), name='login'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ])
