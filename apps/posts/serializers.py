from rest_framework import serializers

from apps.posts.models import ContentCategory, ContentTag, Post, PostMedia, Story
from apps.users.serializers import UserPublicSerializer, UserPublicLiteSerializer


class ContentCategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentCategory
        fields = ("id", "name", "slug")


class ContentTagMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentTag
        fields = ("id", "name", "slug")


class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = ("id", "file", "media_type", "thumbnail", "width", "height", "duration", "order")


class PostListSerializer(serializers.ModelSerializer):
    media_items = PostMediaSerializer(many=True, read_only=True)
    author = UserPublicSerializer(read_only=True)
    category = ContentCategoryMiniSerializer(read_only=True)
    tags = ContentTagMiniSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "content",
            "post_type",
            "privacy",
            "feeling",
            "location",
            "link_preview",
            "reactions_count",
            "comments_count",
            "shares_count",
            "views_count",
            "created_at",
            "media_items",
            "category",
            "tags",
        )


class FeedPostListSerializer(serializers.ModelSerializer):
    """Optimized serializer for feed API with reduced user profile data."""
    media_items = PostMediaSerializer(many=True, read_only=True)
    author = UserPublicLiteSerializer(read_only=True)
    category = ContentCategoryMiniSerializer(read_only=True)
    tags = ContentTagMiniSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "content",
            "post_type",
            "privacy",
            "feeling",
            "location",
            "link_preview",
            "reactions_count",
            "comments_count",
            "shares_count",
            "views_count",
            "created_at",
            "media_items",
            "category",
            "tags",
        )


class PostDetailSerializer(PostListSerializer):
    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ("updated_at", "shared_post", "group", "page")


class StorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = (
            "id",
            "author",
            "media",
            "media_type",
            "text_content",
            "background_color",
            "stickers",
            "music",
            "privacy",
            "views_count",
            "expires_at",
            "created_at",
        )
