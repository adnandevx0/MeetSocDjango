from rest_framework import serializers

from apps.comments.models import Comment
from apps.users.serializers import UserPublicLiteSerializer


class CommentSerializer(serializers.ModelSerializer):
    author = UserPublicLiteSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "author",
            "parent",
            "content",
            "media",
            "reactions_count",
            "replies_count",
            "is_edited",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reactions_count", "replies_count", "is_edited", "created_at", "updated_at")


class CommentDetailSerializer(CommentSerializer):
    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields
