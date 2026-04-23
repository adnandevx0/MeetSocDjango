from django.contrib import admin
from .models import AccountBanned


@admin.register(AccountBanned)
class AccountBannedAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'reason', 'is_active', 'banned_at']
    list_filter = ['is_active', 'banned_at']
    search_fields = ['user__username', 'user__email', 'reason']
    readonly_fields = ['id', 'banned_at']
    fieldsets = (
        ('Account Information', {
            'fields': ('id', 'user')
        }),
        ('Ban Details', {
            'fields': ('reason', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('banned_at',)
        }),
    )