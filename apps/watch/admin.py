from django.contrib import admin
from .models import WatchVideo


@admin.register(WatchVideo)
class WatchVideoAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'category', 'duration', 'views_count', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'description', 'author__username']
    readonly_fields = ['id', 'views_count', 'created_at']
    filter_horizontal = ['tags']
    fieldsets = (
        ('Video Details', {
            'fields': ('id', 'title', 'description', 'author', 'category', 'tags')
        }),
        ('Video File', {
            'fields': ('video_file', 'thumbnail', 'duration')
        }),
        ('Statistics', {
            'fields': ('views_count',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
