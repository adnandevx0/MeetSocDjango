from django.contrib import admin
from .models import Memory


@admin.register(Memory)
class MemoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'year', 'post', 'created_at']
    list_filter = ['year', 'created_at']
    search_fields = ['user__username', 'summary']
    readonly_fields = ['id', 'created_at']
    fieldsets = (
        ('Memory Details', {
            'fields': ('id', 'user', 'post', 'summary')
        }),
        ('Date Information', {
            'fields': ('year',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
