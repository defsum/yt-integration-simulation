"""
Celery tasks for video statistics and management
"""

import random
from celery import shared_task
from django.db.models import F
from django.utils import timezone

from .models import Video, VideoCategory
from apps.comments.models import Comment


@shared_task(bind=True)
def update_video_statistics(self):
    try:
        videos = Video.objects.filter(status='published')
        updated_videos = []
        
        for video in videos:
            new_views = random.randint(0, 20)
            video.view_count = F('view_count') + new_views
            
            new_likes = random.randint(0, 3)
            video.like_count = F('like_count') + new_likes
            
            actual_comment_count = video.comments.count()
            video.comment_count = actual_comment_count
            
            video.save(update_fields=['view_count', 'like_count', 'comment_count'])
            
            updated_videos.append({
                'video_id': video.id,
                'title': video.title,
                'new_views': new_views,
                'new_likes': new_likes,
            })
        
        return {
            'task': 'update_video_statistics',
            'status': 'completed',
            'videos_updated': len(updated_videos),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task
def generate_new_video_content(category_name=None, count=1):
    try:
        from .management.commands.generate_videos import Command as GenerateVideosCommand
        
        category = None
        if category_name:
            try:
                category = VideoCategory.objects.get(name__icontains=category_name)
            except VideoCategory.DoesNotExist:
                pass
        
        generated_videos = []
        
        for _ in range(count):
            command = GenerateVideosCommand()
            categories = [category] if category else list(VideoCategory.objects.filter(is_active=True))
            
            if categories:
                video_data = command.generate_video_data(categories)
                video = Video.objects.create(**video_data)
                
                generated_videos.append({
                    'id': video.id,
                    'title': video.title,
                    'category': video.category.name if video.category else None,
                    'channel_name': video.channel_name
                })
        
        return {
            'task': 'generate_new_video_content',
            'status': 'completed',
            'generated_count': len(generated_videos),
            'videos': generated_videos,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        raise exc