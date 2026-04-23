from rest_framework import serializers

from apps.memories.models import Memory
from apps.users.serializers import UserPublicLiteSerializer
from apps.posts.serializers import PostListSerializer


class MemorySerializer(serializers.ModelSerializer):
    user = UserPublicLiteSerializer(read_only=True)
    post = PostListSerializer(read_only=True)

    class Meta:
        model = Memory
        fields = (
            "id",
            "user",
            "year",
            "post",
            "summary",
            "created_at",
        )
        read_only_fields = ("id", "created_at")
