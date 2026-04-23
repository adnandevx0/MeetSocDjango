from django.contrib import admin
from .models import Notification, NotificationSettings, FCMDevice


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'recipient', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'verb']
    readonly_fields = ['id', 'created_at']
    fieldsets = (
        ('Notification Details', {
            'fields': ('id', 'recipient', 'actor', 'notification_type', 'verb')
        }),
        ('Target', {
            'fields': ('target_type', 'target_id')
        }),
        ('Status', {
            'fields': ('is_read', 'is_seen', 'push_sent')
        }),
        ('Data', {
            'fields': ('data',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_friend_requests', 'push_friend_requests']
    list_filter = ['email_friend_requests', 'email_messages', 'email_posts']
    search_fields = ['user__username']
    readonly_fields = ['user']


@admin.register(FCMDevice)
class FCMDeviceAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'token', 'device_id', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'token']
    readonly_fields = ['id', 'created_at', 'updated_at']
