from django.contrib import admin
from .models import Conversation, ConversationParticipant, Message, MessageSeen


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation_type', 'name', 'created_at']
    list_filter = ['conversation_type', 'created_at']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at']
    fieldsets = (
        ('Conversation Details', {
            'fields': ('id', 'name', 'conversation_type', 'avatar')
        }),
        ('Last Message', {
            'fields': ('last_message',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'user', 'role', 'is_muted', 'unread_count']
    list_filter = ['role', 'is_muted', 'joined_at']
    search_fields = ['user__username', 'conversation__name']
    readonly_fields = ['id', 'joined_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'message_type', 'is_edited', 'created_at']
    list_filter = ['message_type', 'is_edited', 'is_deleted', 'created_at']
    search_fields = ['sender__username', 'content', 'conversation__name']
    readonly_fields = ['id', 'created_at']
    fieldsets = (
        ('Message Details', {
            'fields': ('id', 'conversation', 'sender', 'content')
        }),
        ('Message Type & Media', {
            'fields': ('message_type', 'media', 'reply_to')
        }),
        ('Status', {
            'fields': ('is_edited', 'is_deleted')
        }),
        ('Engagement', {
            'fields': ('reactions',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(MessageSeen)
class MessageSeenAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'user', 'seen_at']
    list_filter = ['seen_at']
    search_fields = ['user__username', 'message__id']
    readonly_fields = ['id', 'seen_at']
