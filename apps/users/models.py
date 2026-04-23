import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone is required")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
        ("prefer_not", "Prefer not to say"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True, null=True, blank=True)
    phone = models.CharField(max_length=32, unique=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default="prefer_not")
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name", "gender"]

    objects = UserManager()

    class Meta:
        db_table = "users_user"
        ordering = ["-created_at"]

    def __str__(self):
        return self.phone or self.email or str(self.id)


class UserProfile(models.Model):
    RELATIONSHIP_CHOICES = [
        ("single", "Single"),
        ("relationship", "In a relationship"),
        ("married", "Married"),
        ("complicated", "It's complicated"),
        ("unspecified", "Unspecified"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True, null=True)
    cover_photo = models.ImageField(upload_to="covers/%Y/%m/", blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    country = models.CharField(max_length=30, blank=True, null=True)
    city = models.CharField(max_length=30, blank=True,  null=True)
    hometown = models.CharField(max_length=30, blank=True, null=True)
    hobbies = models.CharField(max_length=500, blank=True, null=True)
    publiccontacts = models.CharField(max_length=200, blank=True, null=True)
    facebookUsername = models.CharField(max_length=100, blank=True)
    tiktokUsername = models.CharField(max_length=100, blank=True)
    youtubeUsername = models.CharField(max_length=100, blank=True)
    linkedinUsername = models.CharField(max_length=100, blank=True)
    instagramUsername = models.CharField(max_length=100, blank=True)
    twitterUsername = models.CharField(max_length=100, blank=True)
    snapchatUsername = models.CharField(max_length=100, blank=True)
    otherinfo = models.JSONField(max_length=500, blank=True, null=True)
    work = models.CharField(max_length=200, blank=True, null=True)
    education = models.CharField(null=True, max_length=200, blank=True)
    relationship = models.CharField(
        max_length=32, choices=RELATIONSHIP_CHOICES, default="unspecified"
    )
    is_private = models.BooleanField(default=False)
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    friends_count = models.PositiveIntegerField(default=0)
    posts_count = models.PositiveIntegerField(default=0)
    

    # Cached snapshot for recommendations (top categories, refreshed by signals / scoring).
    interest_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "users_userprofile"

    def __str__(self):
        return f"Profile of {self.user_id}"


class Friendship(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("blocked", "Blocked"),
        ("declined", "Declined"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friendship_sent")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friendship_received")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users_friendship"
        constraints = [
            models.UniqueConstraint(
                fields=["sender", "receiver"],
                name="unique_friendship_pair",
            ),
        ]
        indexes = [
            models.Index(fields=["sender", "status"]),
            models.Index(fields=["receiver", "status"]),
        ]

    def __str__(self):
        return f"{self.sender_id} -> {self.receiver_id} ({self.status})"


class Follow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following_rel")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="follower_rel")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_follow"
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="unique_follow_pair"),
        ]


class BlockList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocks_initiated")
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocked_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_blocklist"
        constraints = [
            models.UniqueConstraint(fields=["blocker", "blocked"], name="unique_block_pair"),
        ]
