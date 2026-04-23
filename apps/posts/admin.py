from django.contrib import admin

from .models import ContentCategory, ContentTag, Post, PostMedia, PostView, Story, StoryView


@admin.register(ContentCategory)
class ContentCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "sort_order", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["sort_order", "name"]


@admin.register(ContentTag)
class ContentTagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'post_type', 'privacy', 'category', 'comments_count', 'created_at']
    list_filter = ['post_type', 'privacy', 'category', 'created_at', 'is_edited']
    search_fields = ['author__username', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at', 'reactions_count', 'comments_count', 'shares_count', 'views_count']
    fieldsets = (
        ('Post Content', {
            'fields': ('id', 'author', 'content', 'post_type', 'privacy', 'category', 'tags')
        }),
        ('Location & Feeling', {
            'fields': ('feeling', 'location')
        }),
        ('Link Preview', {
            'fields': ('link_preview',)
        }),
        ('Tagged & Shared', {
            'fields': ('tagged_users', 'shared_post', 'group', 'page')
        }),
        ('Engagement Stats', {
            'fields': ('reactions_count', 'comments_count', 'shares_count', 'views_count', 'is_edited')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    filter_horizontal = ['tagged_users', 'tags']


@admin.register(PostMedia)
class PostMediaAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'file', 'order']
    list_filter = ['order']
    search_fields = ['post__id', 'post__author__username']
    readonly_fields = ['id']


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'privacy', 'expires_at', 'views_count', 'created_at']
    list_filter = ['privacy', 'created_at', 'expires_at']
    search_fields = ['author__username', 'text_content']
    readonly_fields = ['id', 'views_count', 'created_at']


@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = ['id', 'story', 'viewer', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['story__author__username', 'viewer__username']
    readonly_fields = ['id', 'viewed_at']


@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'viewer', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['post__author__username', 'viewer__username']
    readonly_fields = ['id', 'viewed_at']
