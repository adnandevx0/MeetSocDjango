from django.contrib import admin
from .models import SavedPost, FeedHide, FeedSnooze, RecentSearch


@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__id']
    readonly_fields = ['id', 'created_at']


@admin.register(FeedHide)
class FeedHideAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__id']
    readonly_fields = ['id', 'created_at']


@admin.register(FeedSnooze)
class FeedSnoozeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'snoozed_user', 'until']
    list_filter = ['until']
    search_fields = ['user__username', 'snoozed_user__username']
    readonly_fields = ['id']


@admin.register(RecentSearch)
class RecentSearchAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'query', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'query']
    readonly_fields = ['id', 'created_at']
