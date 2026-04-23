from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'post', 'parent', 'replies_count', 'created_at']
    list_filter = ['created_at', 'is_edited', 'parent']
    search_fields = ['author__username', 'content', 'post__id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'reactions_count', 'replies_count']
    fieldsets = (
        ('Comment Content', {
            'fields': ('id', 'post', 'author', 'parent', 'content', 'media')
        }),
        ('Engagement', {
            'fields': ('reactions_count', 'replies_count', 'is_edited')
        }),
        ('Tagged Users', {
            'fields': ('tagged_users',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    filter_horizontal = ['tagged_users']
