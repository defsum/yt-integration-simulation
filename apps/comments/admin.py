"""
simple Django admin for comments
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        'content_preview', 'author_name', 'video_link', 
        'is_reply', 'like_count', 'is_ai_generated', 
        'is_approved', 'created_at'
    ]
    list_filter = [
        'is_approved', 'is_ai_generated', 'created_at'
    ]
    search_fields = ['content', 'author_name', 'video__title']
    readonly_fields = ['like_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Content', {
            'fields': ('content', 'video', 'parent_comment')
        }),
        ('Author Info', {
            'fields': ('author_name', 'author_avatar_url')
        }),
        ('Status', {
            'fields': ('is_approved', 'is_ai_generated')
        }),
        ('AI Info', {
            'fields': ('ai_model_used',),
            'classes': ('collapse',)
        }),
        ('Metrics', {
            'fields': ('like_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        preview = obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
        return preview
    content_preview.short_description = "Content"
    
    def video_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            f'/admin/videos/video/{obj.video.id}/change/',
            obj.video.title[:30] + "..." if len(obj.video.title) > 30 else obj.video.title
        )
    video_link.short_description = "Video"
    
    def is_reply(self, obj):
        return obj.parent_comment is not None
    is_reply.boolean = True
    is_reply.short_description = "Is Reply"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('video', 'parent_comment')
    
    actions = ['approve_comments', 'disapprove_comments']
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} comments were approved.')
    approve_comments.short_description = "Approve selected comments"
    
    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} comments were disapproved.')
    disapprove_comments.short_description = "Disapprove selected comments"