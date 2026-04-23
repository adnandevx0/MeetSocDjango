from django.contrib import admin
from .models import Reaction


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'reaction_type', 'content_type', 'object_id', 'created_at']
    list_filter = ['reaction_type', 'created_at', 'content_type']
    search_fields = ['user__username']
    readonly_fields = ['id', 'created_at']
    fieldsets = (
        ('Reaction Details', {
            'fields': ('id', 'user', 'reaction_type')
        }),
        ('Content Target', {
            'fields': ('content_type', 'object_id')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
