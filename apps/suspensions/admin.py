from django.contrib import admin

from apps.suspensions.models import AccountSuspension


@admin.register(AccountSuspension)
class AccountSuspensionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "status",
        "is_permanent",
        "starts_at",
        "ends_at",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "is_permanent", "created_at")
    search_fields = ("user__email", "user__username", "reason")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("user", "status", "reason")}),
        ("Window", {"fields": ("starts_at", "ends_at", "is_permanent")}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at")}),
    )
