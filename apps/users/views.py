import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.posts.models import Post, PostMedia
from apps.users.models import BlockList, Follow, Friendship, UserProfile
from apps.users.serializers import (
    LoginTokenObtainPairSerializer,
    MeSerializer,
    MeUpdateSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    SocialTokenSerializer,
    UserPublicSerializer,
    VerifyEmailSerializer,
    VerifyPhoneSerializer,
    store_otp,
)
from apps.users.services import get_friend_suggestions
from core.media_processing import optimize_image
from core.throttling import LoginAnonThrottle, OTPThrottle
from core.utils import check_ip_rate_limit, check_rate_limit, sanitize_html
from apps.users.serializers import FriendshipSerializer, FollowSerializer

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


class RegisterView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        # Ensure profile is created for new user
        UserProfile.objects.get_or_create(user=user)
        return Response(
            {
                "success": True,
                "data": {"user": UserPublicSerializer(user).data},
                "message": "Registered successfully.",
                "meta": {},
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginAnonThrottle]
    serializer_class = LoginTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        ip = request.META.get("REMOTE_ADDR", "unknown")
        if not check_ip_rate_limit(ip, "login", settings.RATELIMIT_LOGIN_PER_MINUTE, 60):
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT",
                        "message": "Too many login attempts.",
                        "details": {},
                    },
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def post(self, request):
        refresh_str = request.data.get("refresh")
        if refresh_str:
            try:
                token = RefreshToken(refresh_str)
                token.blacklist()
                jti = token.access_token.get("jti")
                if jti:
                    cache.set(
                        f"jwt_blacklist:{jti}",
                        1,
                        timeout=int(token.access_token.lifetime.total_seconds()),
                    )
            except Exception:
                pass
        return Response({"success": True, "data": {}, "message": "Logged out.", "meta": {}})


class RefreshTokenView(TokenRefreshView):
    permission_classes = [AllowAny]


class VerifyEmailSendView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerifyEmailSerializer

    def post(self, request):
        from celery_tasks.email_tasks import send_email_verification_task

        code = store_otp(request.user.email)
        send_email_verification_task.delay(str(request.user.id), code)
        return Response({"success": True, "data": {}, "message": "Verification email sent.", "meta": {}})


class VerifyEmailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerifyEmailSerializer
    throttle_classes = [OTPThrottle]

    def post(self, request):
        ser = VerifyEmailSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if ser.validated_data["email"].lower() != request.user.email.lower():
            return Response(
                {
                    "success": False,
                    "error": {"code": "MISMATCH", "message": "Email mismatch.", "details": {}},
                },
                status=400,
            )
        cache.delete(f"otp:{ser.validated_data['email']}")
        request.user.is_verified = True
        request.user.save(update_fields=["is_verified"])
        return Response({"success": True, "data": {}, "message": "Email verified.", "meta": {}})


class VerifyPhoneSendView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerifyPhoneSerializer
    throttle_classes = [OTPThrottle]

    def post(self, request):
        phone = request.data.get("phone")
        if not phone:
            return Response({"success": False, "error": {"code": "REQUIRED", "message": "Phone required.", "details": {}}}, status=400)
        if not check_rate_limit(str(request.user.id), "otp_phone", settings.RATELIMIT_OTP_PER_10MIN, 600):
            return Response({"success": False, "error": {"code": "RATE_LIMIT", "message": "Too many OTP attempts.", "details": {}}}, status=429)
        from celery_tasks.email_tasks import send_sms_otp_task

        code = store_otp(phone)
        send_sms_otp_task.delay(phone, code)
        return Response({"success": True, "data": {}, "message": "SMS sent.", "meta": {}})


class VerifyPhoneView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerifyPhoneSerializer
    throttle_classes = [OTPThrottle]

    def post(self, request):
        ser = VerifyPhoneSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        cache.delete(f"otp:{ser.validated_data['phone']}")
        request.user.phone = ser.validated_data["phone"]
        request.user.save(update_fields=["phone"])
        return Response({"success": True, "data": {}, "message": "Phone verified.", "meta": {}})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        ser = PasswordResetRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email = ser.validated_data["email"]
        user = User.objects.filter(email__iexact=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            tok = token_generator.make_token(user)
            from celery_tasks.email_tasks import send_password_reset_email_task

            send_password_reset_email_task.delay(email, force_str(uid), tok)
        return Response(
            {
                "success": True,
                "data": {},
                "message": "If the email exists, reset instructions were sent.",
                "meta": {},
            }
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        ser = PasswordResetConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            uid = force_str(urlsafe_base64_decode(ser.validated_data["uid"]))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {"success": False, "error": {"code": "INVALID", "message": "Invalid uid.", "details": {}}},
                status=400,
            )
        if not token_generator.check_token(user, ser.validated_data["token"]):
            return Response(
                {"success": False, "error": {"code": "INVALID", "message": "Invalid token.", "details": {}}},
                status=400,
            )
        user.set_password(ser.validated_data["new_password"])
        user.save()
        return Response({"success": True, "data": {}, "message": "Password updated.", "meta": {}})


class GoogleOAuthView(APIView):
    permission_classes = [AllowAny]
    serializer_class = SocialTokenSerializer

    def post(self, request):
        ser = SocialTokenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        id_tok = ser.validated_data.get("id_token") or ser.validated_data.get("access_token")
        if not id_tok:
            return Response({"success": False, "error": {"code": "REQUIRED", "message": "Token required.", "details": {}}}, status=400)
        try:
            if ser.validated_data.get("id_token"):
                info = google_id_token.verify_oauth2_token(
                    ser.validated_data["id_token"],
                    google_requests.Request(),
                    settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                )
            else:
                r = requests.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {id_tok}"},
                    timeout=10,
                )
                r.raise_for_status()
                info = r.json()
        except Exception:
            return Response(
                {"success": False, "error": {"code": "INVALID", "message": "Invalid Google token.", "details": {}}},
                status=400,
            )
        email = info.get("email")
        if not email:
            return Response({"success": False, "error": {"code": "EMAIL", "message": "Email not provided.", "details": {}}}, status=400)
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            base_username = email.split("@")[0][:150]
            uname = base_username
            n = 0
            while User.objects.filter(username=uname).exists():
                n += 1
                uname = f"{base_username}{n}"[:150]
            user = User(
                email=email.lower(),
                username=uname,
                full_name=info.get("name", email.split("@")[0]),
                is_verified=True,
            )
            user.set_unusable_password()
            user.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "success": True,
                "data": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": UserPublicSerializer(user).data,
                },
                "message": "",
                "meta": {},
            }
        )


class FacebookOAuthView(APIView):
    permission_classes = [AllowAny]
    serializer_class = SocialTokenSerializer

    def post(self, request):
        ser = SocialTokenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        token = ser.validated_data.get("access_token")
        if not token:
            return Response({"success": False, "error": {"code": "REQUIRED", "message": "access_token required.", "details": {}}}, status=400)
        r = requests.get(
            f"https://graph.facebook.com/me?fields=id,name,email&access_token={token}",
            timeout=10,
        )
        if r.status_code != 200:
            return Response(
                {"success": False, "error": {"code": "INVALID", "message": "Invalid Facebook token.", "details": {}}},
                status=400,
            )
        info = r.json()
        email = info.get("email") or f"fb_{info['id']}@facebook.local"
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            uname = f"fb_{info['id']}"[:150]
            n = 0
            while User.objects.filter(username=uname).exists():
                n += 1
                uname = f"fb_{info['id']}_{n}"[:150]
            user = User(
                email=email.lower() if "@" in email else email,
                username=uname,
                full_name=info.get("name", "Facebook User"),
                is_verified=bool(info.get("email")),
            )
            user.set_unusable_password()
            user.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "success": True,
                "data": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": UserPublicSerializer(user).data,
                },
                "message": "",
                "meta": {},
            }
        )


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return MeUpdateSerializer
        return MeSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        user = self.get_object()
        
        # Ensure user has a profile
        user.profile  # This will create it if it doesn't exist via OneToOneField
        if not hasattr(user, 'profile') or user.profile is None:
            UserProfile.objects.get_or_create(user=user)
        
        # Get profile data - support both nested and flat structures
        prof_data = request.data.get("profile", {})
        if not isinstance(prof_data, dict):
            prof_data = {}
        
        # Profile field names from UserProfile model
        profile_fields = {
            "avatar", "cover_photo", "bio", "website", "work", "education",
            "relationship", "is_private", "country", "city", "hometown",
            "hobbies", "publiccontacts", "facebookUsername", "tiktokUsername",
            "youtubeUsername", "linkedinUsername", "instagramUsername",
            "twitterUsername", "snapchatUsername", "otherinfo"
        }
        
        # Extract profile fields from root request (flat structure)
        for field in profile_fields:
            if field in request.data and field not in prof_data:
                prof_data[field] = request.data[field]
        
        # Extract user fields only (exclude profile fields)
        user_data = {k: v for k, v in request.data.items() 
                     if k not in profile_fields and k != "profile"}
        
        # Update user fields if any
        if user_data:
            ser = self.get_serializer(user, data=user_data, partial=True)
            ser.is_valid(raise_exception=True)
            ser.save()
        
        # Update profile fields if any
        if prof_data:
            pser = ProfileUpdateSerializer(user.profile, data=prof_data, partial=True)
            pser.is_valid(raise_exception=True)
            pser.save()
        
        # Refresh user and profile from database to get latest data
        user.refresh_from_db()
        user.profile.refresh_from_db()
        
        return Response({"success": True, "data": MeSerializer(user).data, "message": "Updated.", "meta": {}})

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class AvatarUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MeUpdateSerializer

    def patch(self, request):
        avatar = request.FILES.get("avatar")
        if not avatar:
            return Response({"success": False, "error": {"code": "REQUIRED", "message": "avatar file required.", "details": {}}}, status=400)
        request.user.profile.avatar = optimize_image(avatar)
        request.user.profile.save(update_fields=["avatar"])
        return Response({"success": True, "data": UserPublicSerializer(request.user).data, "message": "", "meta": {}})


class CoverUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MeUpdateSerializer

    def patch(self, request):
        cover = request.FILES.get("cover_photo")
        if not cover:
            return Response({"success": False, "error": {"code": "REQUIRED", "message": "cover_photo required.", "details": {}}}, status=400)
        request.user.profile.cover_photo = optimize_image(cover)
        request.user.profile.save(update_fields=["cover_photo"])
        return Response({"success": True, "data": UserPublicSerializer(request.user).data, "message": "", "meta": {}})


class PublicProfileView(generics.RetrieveAPIView):
    lookup_field = "username"
    queryset = User.objects.select_related("profile")
    serializer_class = UserPublicSerializer
    permission_classes = [AllowAny]


class UserPostsView(generics.ListAPIView):
    serializer_class = None
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        qs = Post.objects.filter(author=user, privacy="public").order_by("-created_at")[:50]
        from apps.posts.serializers import PostListSerializer

        data = PostListSerializer(qs, many=True, context={"request": request}).data
        return Response({"success": True, "data": data, "message": "", "meta": {}})


class UserPhotosView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        media = PostMedia.objects.filter(post__author=user, media_type="image")[:100]
        urls = [request.build_absolute_uri(m.file.url) if m.file else "" for m in media]
        return Response({"success": True, "data": {"photos": urls}, "message": "", "meta": {}})


class UserFriendsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        ids = Friendship.objects.filter(
            Q(sender=user, status="accepted") | Q(receiver=user, status="accepted")
        )
        friends = []
        for f in ids:
            other = f.receiver if f.sender_id == user.id else f.sender
            friends.append(UserPublicSerializer(other).data)
        return Response({"success": True, "data": friends, "message": "", "meta": {}})


class FollowersListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        qs = User.objects.filter(following_rel__following=user)
        return Response(
            {
                "success": True,
                "data": UserPublicSerializer(qs[:100], many=True).data,
                "message": "",
                "meta": {},
            }
        )


class FollowingListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        qs = User.objects.filter(follower_rel__follower=user)
        return Response(
            {
                "success": True,
                "data": UserPublicSerializer(qs[:100], many=True).data,
                "message": "",
                "meta": {},
            }
        )


class FriendRequestView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FriendshipSerializer

    def post(self, request, user_id):
        other = get_object_or_404(User, pk=user_id)
        if other.id == request.user.id:
            return Response({"success": False, "error": {"code": "INVALID", "message": "Cannot friend self.", "details": {}}}, status=400)
        Friendship.objects.update_or_create(
            sender=request.user,
            receiver=other,
            defaults={"status": "pending"},
        )
        return Response({"success": True, "data": {}, "message": "Request sent.", "meta": {}})


class FriendAcceptView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FriendshipSerializer

    def post(self, request, user_id):
        other = get_object_or_404(User, pk=user_id)
        fr = Friendship.objects.filter(sender=other, receiver=request.user, status="pending").first()
        if not fr:
            return Response({"success": False, "error": {"code": "NOT_FOUND", "message": "No pending request.", "details": {}}}, status=404)
        fr.status = "accepted"
        fr.save()
        for u, p in ((request.user, request.user.profile), (other, other.profile)):
            p.friends_count = Friendship.objects.filter(
                Q(sender=u, status="accepted") | Q(receiver=u, status="accepted")
            ).count()
            p.save(update_fields=["friends_count"])
        return Response({"success": True, "data": {}, "message": "Accepted.", "meta": {}})


class FriendDeclineView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FriendshipSerializer

    def post(self, request, user_id):
        other = get_object_or_404(User, pk=user_id)
        Friendship.objects.filter(sender=other, receiver=request.user, status="pending").update(status="declined")
        return Response({"success": True, "data": {}, "message": "Declined.", "meta": {}})


class FriendUnfriendView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def delete(self, request, user_id):
        other = get_object_or_404(User, pk=user_id)
        Friendship.objects.filter(
            Q(sender=request.user, receiver=other) | Q(sender=other, receiver=request.user)
        ).delete()
        return Response({"success": True, "data": {}, "message": "Unfriended.", "meta": {}})


class FriendRequestsListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FriendshipSerializer

    def get(self, request):
        qs = Friendship.objects.filter(receiver=request.user, status="pending")
        from apps.users.serializers import FriendshipSerializer

        return Response(
            {
                "success": True,
                "data": FriendshipSerializer(qs, many=True).data,
                "message": "",
                "meta": {},
            }
        )


class FriendSuggestionsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserPublicSerializer

    def get(self, request):
        users = get_friend_suggestions(request.user, limit=30)
        return Response(
            {
                "success": True,
                "data": UserPublicSerializer(users, many=True).data,
                "message": "",
                "meta": {},
            }
        )


class FollowUserView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FollowSerializer

    def post(self, request, user_id):
        other = get_object_or_404(User, pk=user_id)
        if other.id == request.user.id:
            return Response({"success": False, "error": {"code": "INVALID", "message": "Cannot follow self.", "details": {}}}, status=400)
        Follow.objects.get_or_create(follower=request.user, following=other)
        other.profile.followers_count = Follow.objects.filter(following=other).count()
        request.user.profile.following_count = Follow.objects.filter(follower=request.user).count()
        other.profile.save(update_fields=["followers_count"])
        request.user.profile.save(update_fields=["following_count"])
        return Response({"success": True, "data": {}, "message": "Followed.", "meta": {}})


class UnfollowUserView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def delete(self, request, user_id):
        other = get_object_or_404(User, pk=user_id)
        Follow.objects.filter(follower=request.user, following=other).delete()
        return Response({"success": True, "data": {}, "message": "Unfollowed.", "meta": {}})


class BlockUserView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def post(self, request, user_id):
        other = get_object_or_404(User, pk=user_id)
        BlockList.objects.get_or_create(blocker=request.user, blocked=other)
        return Response({"success": True, "data": {}, "message": "Blocked.", "meta": {}})


class UnblockUserView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def delete(self, request, user_id):
        other = get_object_or_404(User, pk=user_id)
        BlockList.objects.filter(blocker=request.user, blocked=other).delete()
        return Response({"success": True, "data": {}, "message": "Unblocked.", "meta": {}})


class BlockedListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserPublicSerializer

    def get(self, request):
        qs = User.objects.filter(blocked_by__blocker=request.user)
        return Response(
            {
                "success": True,
                "data": UserPublicSerializer(qs, many=True).data,
                "message": "",
                "meta": {},
            }
        )


class PeopleYouMayKnowView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserPublicSerializer

    def get(self, request):
        users = get_friend_suggestions(request.user, limit=20)
        return Response(
            {
                "success": True,
                "data": UserPublicSerializer(users, many=True).data,
                "message": "",
                "meta": {},
            }
        )
