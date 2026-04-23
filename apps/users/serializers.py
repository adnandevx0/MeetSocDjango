import random
import string

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.users.models import BlockList, Follow, Friendship, UserProfile
from core.utils import sanitize_html

User = get_user_model()


def _otp_key(identifier: str) -> str:
    return f"otp:{identifier}"


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            "avatar",
            "cover_photo",
            "bio",
            "country",
            "city",
            "hometown",
            "website",
            "work",
            "hobbies",
            "publiccontacts",
            "education",
            "relationship",
            "is_private",
            "followers_count",
            "following_count",
            "friends_count",
            "posts_count",
            "facebookUsername",
            "tiktokUsername",
            "youtubeUsername",
            "linkedinUsername",
            "instagramUsername",
            "twitterUsername",
            "snapchatUsername",
            "otherinfo"
            
        )


class UserProfileLiteSerializer(serializers.ModelSerializer):
    """Lightweight profile serializer for feed optimization."""
    class Meta:
        model = UserProfile
        fields = (
            "avatar",
            "bio",
        )


class UserPublicSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    has_blue_badge = serializers.SerializerMethodField()
    blue_badge_valid_until = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "full_name",
            "is_verified",
            "has_blue_badge",
            "blue_badge_valid_until",
            "created_at",
            "profile",
        )

    def get_has_blue_badge(self, obj):
        from apps.verification.models import BlueVerificationRequest

        return bool(BlueVerificationRequest.get_active_for_user(obj))

    def get_blue_badge_valid_until(self, obj):
        from apps.verification.models import BlueVerificationRequest

        active = BlueVerificationRequest.get_active_for_user(obj)
        return active.valid_until if active else None


class UserPublicLiteSerializer(serializers.ModelSerializer):
    """Lightweight user serializer for feed optimization."""
    profile = UserProfileLiteSerializer(read_only=True)
    has_blue_badge = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "full_name",
            "is_verified",
            "has_blue_badge",
            "profile",
        )

    def get_has_blue_badge(self, obj):
        from apps.verification.models import BlueVerificationRequest

        return bool(BlueVerificationRequest.get_active_for_user(obj))



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "phone",
            "username",
            "full_name",
            "date_of_birth",
            "gender",
            "password",
            "password_confirm",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class MeSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    has_blue_badge = serializers.SerializerMethodField()
    blue_badge_valid_until = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone",
            "username",
            "full_name",
            "date_of_birth",
            "gender",
            "is_verified",
            "has_blue_badge",
            "blue_badge_valid_until",
            "created_at",
            "profile",
        )

    def get_has_blue_badge(self, obj):
        from apps.verification.models import BlueVerificationRequest

        return bool(BlueVerificationRequest.get_active_for_user(obj))

    def get_blue_badge_valid_until(self, obj):
        from apps.verification.models import BlueVerificationRequest

        active = BlueVerificationRequest.get_active_for_user(obj)
        return active.valid_until if active else None


class MeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "email",
            "phone",
            "username",
            "full_name",
            "date_of_birth",
            "gender",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional for profile updates
        for field in self.fields.values():
            field.required = False

    def validate_full_name(self, value):
        return sanitize_html(value) if value else value


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            "avatar",
            "cover_photo",
            "bio",
            "website",
            "work",
            "education",
            "relationship",
            "is_private",
            "country",
            "city",
            "hometown",
            "hobbies",
            "publiccontacts",
            "facebookUsername",
            "tiktokUsername",
            "youtubeUsername",
            "linkedinUsername",
             "instagramUsername",
             "twitterUsername",
             "snapchatUsername",
             "otherinfo",
        )

    def validate_bio(self, value):
        return sanitize_html(value) if value else value


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=8)

    def validate(self, attrs):
        key = _otp_key(attrs["email"])
        expected = cache.get(key)
        if not expected or expected != attrs["code"]:
            raise serializers.ValidationError({"code": "Invalid or expired code."})
        return attrs


class VerifyPhoneSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    code = serializers.CharField(max_length=8)

    def validate(self, attrs):
        key = _otp_key(attrs["phone"])
        expected = cache.get(key)
        if not expected or expected != attrs["code"]:
            raise serializers.ValidationError({"code": "Invalid or expired code."})
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        validate_password(attrs["new_password"])
        return attrs


class SocialTokenSerializer(serializers.Serializer):
    access_token = serializers.CharField(required=False, allow_blank=True)
    id_token = serializers.CharField(required=False, allow_blank=True)


class FriendshipSerializer(serializers.ModelSerializer):
    sender = UserPublicSerializer(read_only=True)
    receiver = UserPublicSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = ("id", "sender", "receiver", "status", "created_at", "updated_at")


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ("id", "follower", "following", "created_at")


def generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def store_otp(identifier: str, ttl: int = 600) -> str:
    code = generate_otp()
    cache.set(_otp_key(identifier), code, timeout=ttl)
    return code


class LoginTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        from apps.suspensions.models import AccountSuspension

        active = AccountSuspension.get_active_for_user(self.user)
        if active:
            raise AuthenticationFailed("Your account is suspended.")
        return data
