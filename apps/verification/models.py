import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class BlueVerificationRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blue_verification_requests",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    note = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "verification_blue_request"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status", "valid_until"]),
        ]

    def __str__(self):
        return f"{self.user_id} - {self.status}"

    @property
    def is_active_badge(self) -> bool:
        now = timezone.now()
        return (
            self.status == "approved"
            and self.valid_from is not None
            and self.valid_until is not None
            and self.valid_from <= now <= self.valid_until
        )

    @classmethod
    def get_active_for_user(cls, user):
        now = timezone.now()
        return (
            cls.objects.filter(
                user=user,
                status="approved",
                valid_from__lte=now,
                valid_until__gte=now,
            )
            .order_by("-valid_until")
            .first()
        )
