from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import OTPCode, User
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
        return Response({'token': token.key, 'user': profile_data})


class ForgotPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        user = User.objects.filter(email__iexact=email).first()

        # Always return the same message to avoid revealing whether email exists
        if user:
            otp = OTPCode.generate_for(email, OTPCode.Purpose.PASSWORD_RESET)
            send_mail(
                subject='Reset your Mimical password',
                message=f'Your password reset code is: {otp.code}\n\nThis code expires in 10 minutes.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

        return Response({'detail': 'If this email is registered, a reset code has been sent.'})


class ResetPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        code = request.data.get('code', '').strip()
        new_password = request.data.get('new_password', '')

        otp = OTPCode.objects.filter(
            email=email, code=code, purpose=OTPCode.Purpose.PASSWORD_RESET, is_used=False
        ).order_by('-created_at').first()

        if not otp or not otp.is_valid():
            return Response({'detail': 'Invalid or expired code.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({'detail': e.messages[0]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        otp.is_used = True
        otp.save()

        Token.objects.filter(user=user).delete()
        token, _ = Token.objects.get_or_create(user=user)
        profile_data = UserProfileSerializer(user).data
        return Response({'token': token.key, 'user': profile_data})


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
            at_risk = days_since == 1 and after_8pm

        return Response({
            'streak': user.streak,
            'practiced_today': practiced_today,
            'at_risk': at_risk,
        })
