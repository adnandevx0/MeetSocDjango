from django.contrib import admin
from .models import Group, GroupMembership, GroupInvite


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'privacy', 'members_count', 'created_at']
    list_filter = ['privacy', 'created_at']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['id', 'members_count', 'posts_count', 'created_at']
    fieldsets = (
        ('Group Details', {
            'fields': ('id', 'name', 'slug', 'description', 'created_by', 'privacy')
        }),
        ('Cover', {
            'fields': ('cover_photo',)
        }),
        ('Settings', {
            'fields': ('category', 'rules')
        }),
        ('Statistics', {
            'fields': ('members_count', 'posts_count')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'user', 'role', 'status', 'joined_at']
    list_filter = ['role', 'status', 'joined_at']
    search_fields = ['group__name', 'user__username']
    readonly_fields = ['id', 'joined_at']


@admin.register(GroupInvite)
class GroupInviteAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'invited_user', 'invited_by', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['group__name', 'invited_user__username', 'invited_by__username']
    readonly_fields = ['id', 'created_at']
