from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.comments.tasks import (
    generate_ai_comments_for_popular_videos,
    analyze_and_reply_to_recent_comments,
    generate_user_comments_batch
)
from apps.videos.tasks import (
    update_video_statistics,
    generate_new_video_content
)


class Command(BaseCommand):
    help = 'Test Celery tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            help='Specific task to run',
            choices=[
                'ai_comments',
                'reply_comments',
                'video_stats',
                'all'
            ],
            default='all'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run tasks asynchronously (requires Celery worker)'
        )

    def handle(self, *args, **options):
        task_name = options['task']
        run_async = options['async']
        
        self.stdout.write(
            self.style.SUCCESS(f'Testing Celery tasks - Mode: {"Async" if run_async else "Sync"}')
        )
        
        if task_name in ['ai_comments', 'all']:
            self.run_task(
                'AI Comment Generation',
                generate_ai_comments_for_popular_videos,
                run_async
            )
        
        if task_name in ['reply_comments', 'all']:
            self.run_task(
                'Comment Analysis & Reply',
                analyze_and_reply_to_recent_comments,
                run_async
            )
        
        if task_name in ['video_stats', 'all']:
            self.run_task(
                'Video Statistics Update',
                update_video_statistics,
                run_async
            )
        
        
        self.stdout.write(
            self.style.SUCCESS('All requested tasks completed!')
        )

    def run_task(self, task_name, task_func, run_async):
        self.stdout.write(f'\nRunning: {task_name}')
        
        try:
            if run_async:
                result = task_func.delay()
                self.stdout.write(f'Task ID: {result.id}')
                self.stdout.write('Status: Queued for async execution')
            else:
                start_time = timezone.now()
                result = task_func()
                end_time = timezone.now()
                duration = (end_time - start_time).total_seconds()
                
                if isinstance(result, dict):
                    # maybe add more details later, idk
                    self.stdout.write(f'Status: {result.get("status", "Unknown")}')
                    
                    if 'total_comments_generated' in result:
                        self.stdout.write(f'Comments Generated: {result["total_comments_generated"]}')
                    if 'videos_updated' in result:
                        self.stdout.write(f'Videos Updated: {result["videos_updated"]}')
                    if 'replies_generated' in result:
                        self.stdout.write(f'Replies Generated: {result["replies_generated"]}')
                    if 'analytics_created' in result:
                        self.stdout.write(f'   Analytics Created: {result["analytics_created"]}')
                else:
                    self.stdout.write(f'Result: {result}')
                
                self.stdout.write(f'Duration: {duration:.2f}s')
            
            self.stdout.write(self.style.SUCCESS(f'{task_name} completed'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'{task_name} failed: {str(e)}')
            )