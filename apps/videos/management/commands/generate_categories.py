# python manage.py generate_categories

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.videos.models import VideoCategory


class Command(BaseCommand):
    help = 'Generate video categories for the Youtube simulation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories before generating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing categories...')
            VideoCategory.objects.all().delete()

        categories_data = [
            {
                'name': 'Technology',
                'description': 'Tech reviews, tutorials, programming, and innovation'
            },
            {
                'name': 'Entertainment',
                'description': 'Movies, TV shows, celebrity news, and pop culture'
            },
            {
                'name': 'Education',
                'description': 'Learning content, tutorials, and educational videos'
            },
            {
                'name': 'Gaming',
                'description': 'Video game content, reviews, and gameplay'
            },
            {
                'name': 'Music',
                'description': 'Music videos, performances, and music-related content'
            },
            {
                'name': 'Sports',
                'description': 'Sports highlights, analysis, and athletic content'
            },
            {
                'name': 'News',
                'description': 'Current events, journalism, and news analysis'
            },
            {
                'name': 'Comedy',
                'description': 'Funny videos, sketches, and comedic content'
            },
            {
                'name': 'Science',
                'description': 'Scientific content, experiments, and discoveries'
            },
            {
                'name': 'Travel',
                'description': 'Travel vlogs, destination guides, and cultural exploration'
            },
            {
                'name': 'Cooking',
                'description': 'Recipes, cooking tutorials, and food content'
            },
            {
                'name': 'Fitness',
                'description': 'Workout videos, health tips, and wellness content'
            }
        ]

        created_categories = []
        
        with transaction.atomic():
            for category_data in categories_data:
                category, created = VideoCategory.objects.get_or_create(
                    name=category_data['name'],
                    defaults={
                        'description': category_data['description'],
                        'is_active': True
                    }
                )
                if created:
                    created_categories.append(category)
                    self.stdout.write(
                        self.style.SUCCESS(f'Created category: {category.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Category already exists: {category.name}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(created_categories)} new categories'
            )
        )