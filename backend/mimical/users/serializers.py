from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    username = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        email = data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({'email': 'A user with this email already exists.'})
        data['email'] = email
        username = (data.get('username') or email.split('@')[0]).strip()
        if User.objects.filter(username__iexact=username).exists():
            username = email
        data['username'] = username
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs['email'].strip().lower()
        password = attrs['password']
        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            raise serializers.ValidationError({'email': 'No account found for this email.'})

        authenticated_user = authenticate(
            request=self.context.get('request'),
            username=user.username,
            password=password,
        )
        if authenticated_user is None:
            raise serializers.ValidationError({'password': 'Incorrect password.'})
        attrs['user'] = authenticated_user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'xp', 'streak', 'last_activity_date', 'avatar_url', 'date_joined')
        read_only_fields = ('id', 'xp', 'streak', 'last_activity_date', 'date_joined')
