from rest_framework import serializers

from apps.suspensions.models import AccountSuspension


class AccountSuspensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSuspension
        fields = (
            "id",
            "user",
            "reason",
            "starts_at",
            "ends_at",
            "is_permanent",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_by", "created_at", "updated_at")
