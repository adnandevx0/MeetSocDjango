from django.contrib import admin
from .models import Page, PageFollower


# Renaming the admin class to avoid conflict with Django's built-in PageAdmin
@admin.register(Page)
class PageAdminView(admin.ModelAdmin):
    list_display = ['id', 'name', 'followers_count', 'verified', 'created_at']
    list_filter = ['verified', 'created_at']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['id', 'followers_count', 'likes_count', 'created_at']
    fieldsets = (
        ('Page Details', {
            'fields': ('id', 'name', 'slug', 'description', 'created_by')
        }),
        ('Contact & Links', {
            'fields': ('website', 'email', 'phone', 'address')
        }),
        ('Media', {
            'fields': ('avatar', 'cover_photo')
        }),
        ('Verification', {
            'fields': ('verified',)
        }),
        ('Category', {
            'fields': ('category',)
        }),
        ('Statistics', {
            'fields': ('followers_count', 'likes_count')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(PageFollower)
class PageFollowerAdmin(admin.ModelAdmin):
    list_display = ['id', 'page', 'user', 'is_liked', 'created_at']
    list_filter = ['is_liked', 'created_at']
    search_fields = ['page__name', 'user__username']
    readonly_fields = ['id', 'created_at']
