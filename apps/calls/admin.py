from django.contrib import admin
from .models import Call, CallParticipant


@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ['id', 'call_type', 'caller', 'status', 'duration', 'created_at']
    list_filter = ['call_type', 'status', 'created_at']
    search_fields = ['caller__username', 'caller__email']
    readonly_fields = ['id', 'created_at', 'started_at', 'ended_at']
    fieldsets = (
        ('Call Information', {
            'fields': ('id', 'call_type', 'status', 'duration')
        }),
        ('Participants', {
            'fields': ('caller', 'conversation')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'ended_at')
        }),
    )


@admin.register(CallParticipant)
class CallParticipantAdmin(admin.ModelAdmin):
    list_display = ['id', 'call', 'user', 'joined_at', 'is_muted', 'is_video_on']
    list_filter = ['is_muted', 'is_video_on', 'joined_at']
    search_fields = ['user__username', 'call__id']
    readonly_fields = ['id', 'joined_at', 'left_at']
