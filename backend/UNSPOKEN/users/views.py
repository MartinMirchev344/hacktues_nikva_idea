from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import LoginSerializer, RegisterSerializer, UserProfileSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        profile_data = UserProfileSerializer(user).data
        return Response(
            {
                'token': token.key,
                'user': profile_data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        profile_data = UserProfileSerializer(user).data
        return Response(
            {
                'token': token.key,
                'user': profile_data,
            }
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class LeaderboardView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        top_users = User.objects.order_by('-xp')[:20]
        serializer = UserProfileSerializer(top_users, many=True)
        return Response(serializer.data)


class StreakStatusView(APIView):
    def get(self, request):
        user = request.user
        today = timezone.now().date()
        practiced_today = user.last_activity_date == today

        import zoneinfo
        local_now = timezone.now().astimezone(zoneinfo.ZoneInfo('Europe/Sofia'))
        after_8pm = local_now.hour >= 20

        if user.last_activity_date is None:
            at_risk = False
        elif practiced_today:
            at_risk = False
        else:
            days_since = (today - user.last_activity_date).days
            at_risk = days_since == 1 and after_8pm  # practiced yesterday, not yet today, past 8pm

        return Response({
            'streak': user.streak,
            'practiced_today': practiced_today,
            'at_risk': at_risk,
        })
