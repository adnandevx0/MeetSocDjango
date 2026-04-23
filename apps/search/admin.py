from django.contrib import admin
from .models import TrendingTopic


@admin.register(TrendingTopic)
class TrendingTopicAdmin(admin.ModelAdmin):
    list_display = ['id', 'tag', 'score', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['tag']
    readonly_fields = ['id', 'updated_at']
    fieldsets = (
        ('Topic Details', {
            'fields': ('id', 'tag', 'score')
        }),
        ('Timestamps', {
            'fields': ('updated_at',)
        }),
    )
