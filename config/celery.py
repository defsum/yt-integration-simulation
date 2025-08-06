import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('yt_integration')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone=settings.TIME_ZONE,
    enable_utc=True,
    task_routes={
        'apps.comments.tasks.generate_ai_comments': {'queue': 'ai_generation'},
        'apps.videos.tasks.update_video_stats': {'queue': 'analytics'},
        'apps.analytics.tasks.calculate_engagement_metrics': {'queue': 'analytics'},
    },
    beat_schedule={
        'generate-ai-comments-every-5-minutes': {
            'task': 'apps.comments.tasks.generate_ai_comments_for_popular_videos',
            'schedule': 300.0,
        },
        'update-video-statistics-every-10-minutes': {
            'task': 'apps.videos.tasks.update_video_statistics',
            'schedule': 600.0,
        },
        'calculate-engagement-metrics-hourly': {
            'task': 'apps.analytics.tasks.calculate_engagement_metrics',
            'schedule': 3600.0,
        },
        'generate-trending-videos-daily': {
            'task': 'apps.videos.tasks.update_trending_videos',
            'schedule': 86400.0,
        },
    },
)


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')