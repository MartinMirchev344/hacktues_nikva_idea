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
