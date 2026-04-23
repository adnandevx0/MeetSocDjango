from django.contrib import admin

from apps.verification.models import BlueVerificationRequest


@admin.register(BlueVerificationRequest)
class BlueVerificationRequestAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "status",
        "valid_from",
        "valid_until",
        "approved_at",
        "created_at",
    )
    list_filter = ("status", "created_at", "valid_until")
    search_fields = ("user__email", "user__username", "note", "admin_note")
    readonly_fields = ("created_at", "updated_at", "approved_at")
    actions = ("mark_rejected",)

    fieldsets = (
        (None, {"fields": ("user", "status", "note", "admin_note")}),
        ("Badge Window", {"fields": ("valid_from", "valid_until", "approved_at")}),
        ("Meta", {"fields": ("created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        if obj.status == "approved" and not obj.approved_at:
            from django.utils import timezone

            obj.approved_at = timezone.now()
            if not obj.valid_from:
                obj.valid_from = obj.approved_at
        super().save_model(request, obj, form, change)

    @admin.action(description="Mark selected requests as rejected")
    def mark_rejected(self, request, queryset):
        queryset.update(status="rejected")
