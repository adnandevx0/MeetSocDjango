from django.contrib import admin

from apps.recommendations.models import UserCategoryScore, UserInteraction


@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "action", "category", "watch_seconds", "points_applied", "created_at")
    list_filter = ("action", "created_at", "category")
    search_fields = ("user__email", "user__username", "object_id")
    readonly_fields = ("id", "created_at", "content_type", "object_id", "content_object")
    date_hierarchy = "created_at"


@admin.register(UserCategoryScore)
class UserCategoryScoreAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "category", "score", "updated_at")
    list_filter = ("category", "updated_at")
    search_fields = ("user__email", "user__username", "category__name")
    readonly_fields = ("id", "updated_at")
