import uuid

from django.conf import settings
from django.db import models


class WatchVideo(models.Model):
    """Uploaded or linked watch feed video."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watch_videos")
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    video_file = models.FileField(upload_to="watch/videos/%Y/%m/")
    thumbnail = models.ImageField(upload_to="watch/thumbs/%Y/%m/", blank=True, null=True)
    duration = models.FloatField(default=0)
    category = models.ForeignKey(
        "posts.ContentCategory",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="watch_videos",
    )
    tags = models.ManyToManyField("posts.ContentTag", blank=True, related_name="watch_videos")
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "watch_watchvideo"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "-created_at"]),
        ]
