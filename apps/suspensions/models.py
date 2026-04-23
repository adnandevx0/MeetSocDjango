import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class AccountSuspension(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("lifted", "Lifted"),
        ("expired", "Expired"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account_suspensions",
    )
    reason = models.TextField(blank=True)
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_permanent = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_suspensions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "suspensions_account"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["ends_at"]),
        ]

    def __str__(self):
        return f"{self.user_id} suspended ({self.status})"

    def is_currently_active(self) -> bool:
        if self.status != "active":
            return False
        now = timezone.now()
        if self.starts_at and self.starts_at > now:
            return False
        if self.is_permanent:
            return True
        if self.ends_at is None:
            return True
        return self.ends_at >= now

    @classmethod
    def get_active_for_user(cls, user):
        now = timezone.now()
        qs = cls.objects.filter(user=user, status="active", starts_at__lte=now).filter(
            models.Q(is_permanent=True) | models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now)
        )
        return qs.order_by("-created_at").first()
