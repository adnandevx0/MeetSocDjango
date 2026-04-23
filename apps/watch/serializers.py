from rest_framework import serializers

from apps.watch.models import WatchVideo
from apps.users.serializers import UserPublicLiteSerializer


class WatchVideoSerializer(serializers.ModelSerializer):
    author = UserPublicLiteSerializer(read_only=True)

    class Meta:
        model = WatchVideo
        fields = (
            "id",
            "title",
            "description",
            "video_file",
            "thumbnail",
            "duration",
            "category",
            "tags",
            "views_count",
            "author",
            "created_at",
        )
        read_only_fields = ("id", "views_count", "created_at")
