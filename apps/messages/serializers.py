from rest_framework import serializers

from apps.messages.models import Conversation, ConversationParticipant, Message, MessageSeen
from apps.users.serializers import UserPublicLiteSerializer


class ConversationParticipantSerializer(serializers.ModelSerializer):
    user = UserPublicLiteSerializer(read_only=True)

    class Meta:
        model = ConversationParticipant
        fields = (
            "id",
            "user",
            "role",
            "is_muted",
            "last_read_at",
            "unread_count",
            "joined_at",
        )


class MessageSerializer(serializers.ModelSerializer):
    sender = UserPublicLiteSerializer(read_only=True)

    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "sender",
            "message_type",
            "content",
            "media",
            "reply_to",
            "reactions",
            "is_edited",
            "is_deleted",
            "created_at",
        )
        read_only_fields = ("id", "is_edited", "is_deleted", "created_at")


class ConversationSerializer(serializers.ModelSerializer):
    cp = ConversationParticipantSerializer(many=True, read_only=True)
    last_message = MessageSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id",
            "conversation_type",
            "name",
            "avatar",
            "last_message",
            "cp",
            "created_at",
        )
        read_only_fields = ("id", "created_at")
