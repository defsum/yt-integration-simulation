"""
template views for the simple video UI
"""

from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from django.core.paginator import Paginator

from .models import Video, VideoCategory
from apps.comments.models import Comment


def video_list_view(request):
    category_id = request.GET.get('category')
    search = request.GET.get('search', '')
    
    videos = Video.objects.filter(status='published').select_related('category').annotate(
        total_comments=Count('comments', filter=Q(comments__is_approved=True))
    ).order_by('-published_at')
    
    if category_id:
        videos = videos.filter(category_id=category_id)
    
    if search:
        videos = videos.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(channel_name__icontains=search)
        )
    
    paginator = Paginator(videos, 12)
    page_number = request.GET.get('page')
    videos_page = paginator.get_page(page_number)
    
    categories = VideoCategory.objects.filter(is_active=True)
    
    context = {
        'videos': videos_page,
        'categories': categories,
        'current_category': category_id,
        'search_query': search,
        'total_videos': videos.count(),
    }
    
    return render(request, 'videos/video_list.html', context)


def video_detail_view(request, video_id):
    video = get_object_or_404(
        Video.objects.select_related('category').annotate(
            total_comments=Count('comments', filter=Q(comments__is_approved=True))
        ), 
        id=video_id, 
        status='published'
    )
    
    comments = Comment.objects.filter(
        video=video,
        parent_comment__isnull=True,
        is_approved=True
    ).select_related('parent_comment').prefetch_related(
        'replies__replies'
    ).order_by('-created_at')
    
    paginator = Paginator(comments, 20)
    page_number = request.GET.get('page')
    comments_page = paginator.get_page(page_number)
    
    comment_stats = {
        'total_comments': video.total_comments,
        'ai_comments': Comment.objects.filter(
            video=video, 
            is_ai_generated=True,
            is_approved=True
        ).count(),
        'user_comments': Comment.objects.filter(
            video=video, 
            is_ai_generated=False,
            is_approved=True
        ).count(),
        'approved_comments': Comment.objects.filter(
            video=video, 
            is_approved=True
        ).count(),
    }
    
    related_videos = Video.objects.filter(
        category=video.category,
        status='published'
    ).exclude(id=video.id).annotate(
        total_comments=Count('comments', filter=Q(comments__is_approved=True))
    ).order_by('-view_count')[:6]
    
    context = {
        'video': video,
        'comments': comments_page,
        'comment_stats': comment_stats,
        'related_videos': related_videos,
    }
    
    return render(request, 'videos/video_detail.html', context)