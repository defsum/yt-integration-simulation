"""
Celery tasks for comment generation and management
"""

import random
from celery import shared_task
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Comment
from .ai_engine import youtube_ai_engine
from apps.videos.models import Video


@shared_task(bind=True)
def generate_ai_comments_for_popular_videos(self):
    try:
        recent_threshold = timezone.now() - timedelta(hours=1)
        
        popular_videos = Video.objects.filter(
            status='published',
            published_at__lte=timezone.now(),
        ).annotate(
            recent_comments=Count(
                'comments', 
                filter=Q(comments__created_at__gte=recent_threshold)
            )
        ).filter(
            Q(view_count__gt=100) | Q(recent_comments__gt=0)
        ).order_by('-view_count', '-recent_comments')[:5]
        
        total_generated = 0
        results = []
        
        for video in popular_videos:
            comment_count = random.randint(1, 3)
            
            for _ in range(comment_count):
                user_comment = youtube_ai_engine.generate_user_comment(video=video)
                if user_comment:
                    total_generated += 1
                    
                    # 30% chance to generate a business reply
                    if random.random() < 0.3:
                        analysis = youtube_ai_engine.analyze_comment_for_business_opportunity(user_comment)
                        if analysis['should_reply']:
                            business_reply = youtube_ai_engine.generate_business_reply(user_comment, analysis)
                            if business_reply:
                                total_generated += 1
            
            # 20% chance to generate a channel promotional comment
            if random.random() < 0.2:
                promo_comment = youtube_ai_engine.generate_channel_promotional_comment(
                    video=video, 
                    offer_type=random.choice(['techmaster', 'marketing_bundle'])
                )
                if promo_comment:
                    total_generated += 1
            
            results.append({
                'video_id': video.id,
                'video_title': video.title,
                'comments_generated': comment_count
            })
        
        return {
            'task': 'generate_ai_comments_for_popular_videos',
            'status': 'completed',
            'total_comments_generated': total_generated,
            'videos_processed': len(results),
            'results': results,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(bind=True)
def analyze_and_reply_to_recent_comments(self):
    try:
        recent_threshold = timezone.now() - timedelta(minutes=30)
        
        recent_comments = Comment.objects.filter(
            created_at__gte=recent_threshold,
            is_ai_generated=False,
            parent_comment__isnull=True,
            replies__isnull=True
        ).select_related('video').order_by('-like_count', '-created_at')[:10]
        
        replies_generated = 0
        results = []
        
        for comment in recent_comments:
            analysis = youtube_ai_engine.analyze_comment_for_business_opportunity(comment)
            
            if analysis['should_reply']:
                business_reply = youtube_ai_engine.generate_business_reply(comment, analysis)
                if business_reply:
                    replies_generated += 1
                    results.append({
                        'original_comment_id': comment.id,
                        'reply_id': business_reply.id,
                        'reply_type': analysis['reply_type'],
                        'video_title': comment.video.title
                    })
        
        return {
            'task': 'analyze_and_reply_to_recent_comments',
            'status': 'completed',
            'replies_generated': replies_generated,
            'comments_analyzed': len(recent_comments),
            'results': results,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(bind=True)
def cleanup_old_ai_comments(self):
    try:
        old_threshold = timezone.now() - timedelta(days=30)
        
        old_comments = Comment.objects.filter(
            is_ai_generated=True,
            created_at__lt=old_threshold
        )
        
        deleted_count = old_comments.count()
        old_comments.delete()
        
        return {
            'task': 'cleanup_old_ai_comments',
            'status': 'completed',
            'deleted_comments': deleted_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task
def generate_user_comments_batch(video_id, count=5):
    try:
        video = Video.objects.get(id=video_id)
        generated_comments = []
        
        for _ in range(count):
            comment = youtube_ai_engine.generate_user_comment(video=video)
            if comment:
                generated_comments.append({
                    'id': comment.id,
                    'content': comment.content,
                    'author': comment.author_name
                })
        
        return {
            'task': 'generate_user_comments_batch',
            'status': 'completed',
            'video_id': video_id,
            'video_title': video.title,
            'generated_count': len(generated_comments),
            'comments': generated_comments,
            'timestamp': timezone.now().isoformat()
        }
        
    except Video.DoesNotExist:
        return {
            'task': 'generate_user_comments_batch',
            'status': 'error',
            'error': f'Video with id {video_id} does not exist'
        }
    except Exception as exc:
        raise exc