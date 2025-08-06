"""
Django admin config for videos
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Video, VideoCategory


@admin.register(VideoCategory)
class VideoCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'video_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    def video_count(self, obj):
        count = obj.videos.filter(status='published').count()
        if count > 0:
            url = reverse('admin:videos_video_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{} videos</a>', url, count)
        return '0 videos'
    video_count.short_description = 'Published Videos'


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'channel_name', 'category', 'status', 
        'view_count', 'like_count', 'comment_count', 
        'engagement_rate_display', 'published_at'
    ]
    list_filter = [
        'status', 'category', 'language', 'created_at', 'published_at'
    ]
    search_fields = ['title', 'description', 'channel_name', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'view_count', 'like_count', 'dislike_count', 
        'comment_count', 'engagement_rate', 'like_ratio',
        'created_at', 'updated_at', 'video_url', 'thumbnail_url'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'category')
        }),
        ('Content Details', {
            'fields': ('duration', 'video_url', 'thumbnail_url', 'tags', 'language')
        }),
        ('Channel Information', {
            'fields': ('channel_name', 'channel_avatar_url')
        }),
        ('Publishing', {
            'fields': ('status', 'published_at')
        }),
        ('Engagement Metrics', {
            'fields': (
                'view_count', 'like_count', 'dislike_count', 
                'comment_count', 'engagement_rate', 'like_ratio'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_published', 'mark_as_draft', 'update_comment_counts']
    
    def engagement_rate_display(self, obj):
        rate = obj.engagement_rate
        if rate > 5:
            color = 'green'
        elif rate > 2:
            color = 'orange'
        else:
            color = 'red'
        formatted_rate = f"{rate:.2f}%"
        return format_html(
            '<span style="color: {};">{}</span>', 
            color, formatted_rate
        )
    engagement_rate_display.short_description = 'Engagement Rate'
    engagement_rate_display.admin_order_field = 'engagement_rate'
    
    def mark_as_published(self, request, queryset):
        count = queryset.update(status='published')
        self.message_user(
            request, 
            f'{count} video(s) marked as published.'
        )
    mark_as_published.short_description = 'Mark selected videos as published'
    
    def mark_as_draft(self, request, queryset):
        count = queryset.update(status='draft')
        self.message_user(
            request, 
            f'{count} video(s) marked as draft.'
        )
    mark_as_draft.short_description = 'Mark selected videos as draft'
    
    def update_comment_counts(self, request, queryset):
        count = 0
        for video in queryset:
            video.update_comment_count()
            count += 1
        self.message_user(
            request, 
            f'Updated comment counts for {count} video(s).'
        )
    update_comment_counts.short_description = 'Update comment counts'