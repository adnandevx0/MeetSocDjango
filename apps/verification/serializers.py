from rest_framework import serializers

from apps.verification.models import BlueVerificationRequest


class BlueVerificationRequestSerializer(serializers.ModelSerializer):
    is_active_badge = serializers.BooleanField(read_only=True)

    class Meta:
        model = BlueVerificationRequest
        fields = (
            "id",
            "status",
            "note",
            "admin_note",
            "approved_at",
            "valid_from",
            "valid_until",
            "is_active_badge",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "status",
            "admin_note",
            "approved_at",
            "valid_from",
            "valid_until",
            "created_at",
            "updated_at",
        )
