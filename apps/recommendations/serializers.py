from rest_framework import serializers


class ContentCategorySerializer(serializers.Serializer):
    """Serializer for content categories in recommendations."""
    id = serializers.CharField()
    name = serializers.CharField()


class UserInterestSummarySerializer(serializers.Serializer):
    """Serializer for user interest summary."""
    category = serializers.CharField()
    score = serializers.FloatField()


class InteractionSerializer(serializers.Serializer):
    """Serializer for interaction tracking."""
    content_id = serializers.CharField()
    interaction_type = serializers.CharField()
    score = serializers.FloatField(required=False)
