import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class UserInteraction(models.Model):
    """
    Append-only behavior log: views, watch time, likes, shares, clicks.
    Denormalized category_id keeps aggregations cheap at scale.
    """

    ACTION_VIEW = "view"
    ACTION_WATCH = "watch"
    ACTION_LIKE = "like"
    ACTION_SHARE = "share"
    ACTION_CLICK = "click"
    ACTION_CHOICES = [
        (ACTION_VIEW, "View"),
        (ACTION_WATCH, "Watch"),
        (ACTION_LIKE, "Like"),
        (ACTION_SHARE, "Share"),
        (ACTION_CLICK, "Click"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interactions"
    )
    action = models.CharField(max_length=16, choices=ACTION_CHOICES, db_index=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")
    category = models.ForeignKey(
        "posts.ContentCategory",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="interactions",
    )
    watch_seconds = models.FloatField(default=0)
    points_applied = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "recommendations_userinteraction"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["category", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]
        ordering = ["-created_at"]


class UserCategoryScore(models.Model):
    """Rolling aggregate per user × category (single row update — O(1) per event)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="category_scores"
    )
    category = models.ForeignKey(
        "posts.ContentCategory", on_delete=models.CASCADE, related_name="user_scores"
    )
    score = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recommendations_usercategoryscore"
        constraints = [
            models.UniqueConstraint(fields=["user", "category"], name="unique_user_category_score"),
        ]
        indexes = [
            models.Index(fields=["user", "-score"]),
        ]
