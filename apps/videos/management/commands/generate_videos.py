import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from apps.videos.models import Video, VideoCategory

#python manage.py generate_videos --count 100

class Command(BaseCommand):
    help = 'Generate realistic video data for the Youtube simulation'

    def __init__(self):
        super().__init__()
        self.fake = Faker()

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of videos to generate (default: 50)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing videos before generating new ones',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for bulk operations (default: 100)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing videos...')
            Video.objects.all().delete()

        categories = list(VideoCategory.objects.filter(is_active=True))
        if not categories:
            self.stdout.write(
                self.style.ERROR('No active categories found. Run generate_categories first.')
            )
            return

        count = options['count']
        batch_size = options['batch_size']
        
        self.stdout.write(f'Generating {count} videos...')
        
        videos_created = 0
        batch = []

        for i in range(count):
            video_data = self.generate_video_data(categories)
            batch.append(Video(**video_data))
            
            if len(batch) >= batch_size or i == count - 1:
                with transaction.atomic():
                    Video.objects.bulk_create(batch, ignore_conflicts=True)
                
                videos_created += len(batch)
                self.stdout.write(f'Created batch of {len(batch)} videos...')
                batch = []

        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated {videos_created} videos')
        )

    def generate_video_data(self, categories):
        category = random.choice(categories)
        
        title = self.generate_title_by_category(category.name)
        
        days_old = random.randint(1, 365)
        published_at = timezone.now() - timedelta(days=days_old)
        
        base_views = random.randint(100, 10000)
        if days_old > 30:
            base_views += random.randint(1000, 50000)
        if days_old > 180:
            base_views += random.randint(5000, 100000)
        
        view_count = base_views
        like_count = int(view_count * random.uniform(0.01, 0.1))
        dislike_count = int(like_count * random.uniform(0.05, 0.3))
        
        duration = self.generate_duration_by_category(category.name)
        
        tags = self.generate_tags_by_category(category.name)
        
        channel_name = self.generate_channel_name(category.name)
        
        return {
            'title': title,
            'description': self.generate_description(title, category.name),
            'category': category,
            'duration': duration,
            'channel_name': channel_name,
            'status': 'published',
            'published_at': published_at,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'comment_count': random.randint(0, max(1, int(view_count * 0.01))),
            'tags': tags,
            'language': 'en',
        }

    def generate_title_by_category(self, category):
        title_templates = {
            'Technology': [
                'The Future of {tech} in 2024',
                'Why {tech} is Changing Everything',
                'Top 10 {tech} Tips You Need to Know',
                'Complete {tech} Tutorial for Beginners',
                'React vs Vue vs Angular: Ultimate Comparison',
                'Building {tech} Apps in 2024',
                'AI Revolution: How {tech} Works',
            ],
            'Gaming': [
                '{game} - Full Gameplay Walkthrough',
                'Top 10 {game} Tips and Tricks',
                '{game} Review: Is It Worth Playing?',
                'Epic {game} Moments Compilation',
                'How to Master {game} in 30 Days',
                '{game} vs {game}: Which is Better?',
            ],
            'Education': [
                'Learn {subject} in 10 Minutes',
                'Complete {subject} Course for Beginners',
                'Why {subject} is Important in 2024',
                '{subject} Explained Simply',
                'Master {subject} with These Tips',
            ],
            'Entertainment': [
                'Top 10 {movie} Moments',
                '{celebrity} Interview: Shocking Revelations',
                'Behind the Scenes: {movie}',
                'Funniest {show} Compilation',
                'Celebrity News: {celebrity} Updates',
            ]
        }
        
        templates = title_templates.get(category, [
            'Amazing {topic} You Need to See',
            'The Ultimate Guide to {topic}',
            'Why {topic} Matters in 2024',
            'Top 10 {topic} Facts',
            'Everything You Need to Know About {topic}',
        ])
        
        template = random.choice(templates)
        
        if '{tech}' in template:
            tech_terms = ['AI', 'Machine Learning', 'Python', 'React', 'JavaScript', 'Docker', 'Kubernetes']
            template = template.format(tech=random.choice(tech_terms))
        elif '{game}' in template:
            games = ['Minecraft', 'Fortnite', 'Call of Duty', 'FIFA', 'League of Legends', 'Valorant']
            template = template.format(game=random.choice(games))
        elif '{subject}' in template:
            subjects = ['Mathematics', 'Physics', 'Chemistry', 'History', 'Biology', 'English']
            template = template.format(subject=random.choice(subjects))
        elif '{movie}' in template:
            movies = ['Marvel', 'Star Wars', 'Lord of the Rings', 'Harry Potter', 'DC Comics']
            template = template.format(movie=random.choice(movies))
        elif '{celebrity}' in template:
            template = template.format(celebrity=self.fake.name())
        elif '{show}' in template:
            shows = ['Friends', 'The Office', 'Game of Thrones', 'Breaking Bad', 'Stranger Things']
            template = template.format(show=random.choice(shows))
        elif '{topic}' in template:
            topics = ['Innovation', 'Success', 'Productivity', 'Health', 'Travel', 'Cooking']
            template = template.format(topic=random.choice(topics))
        
        return template

    def generate_description(self, title, category):
        descriptions = [
            f"In this video, we explore {title.lower()}. Don't forget to like and subscribe!",
            f"Welcome back to our channel! Today we're diving into {category.lower()} content.",
            f"This comprehensive guide covers everything about {title.lower()}.",
            f"Join us as we discuss the latest in {category.lower()}. Hit the notification bell!",
            f"Thanks for watching! Check out our other {category.lower()} videos in the playlist.",
        ]
        
        return random.choice(descriptions) + f"\n\n{self.fake.text(max_nb_chars=200)}"

    def generate_duration_by_category(self, category):
        duration_ranges = {
            'Music': (180, 300),
            'Comedy': (60, 600),
            'Education': (600, 3600),
            'Gaming': (1200, 7200),
            'Technology': (300, 1800),
            'News': (120, 600),
        }
        
        min_duration, max_duration = duration_ranges.get(category, (300, 1800))
        return random.randint(min_duration, max_duration)

    def generate_tags_by_category(self, category):
        tag_sets = {
            'Technology': ['tech', 'programming', 'tutorial', 'coding', 'software', 'developer'],
            'Gaming': ['gaming', 'gameplay', 'review', 'walkthrough', 'tips', 'strategy'],
            'Education': ['education', 'learning', 'tutorial', 'guide', 'howto', 'tips'],
            'Entertainment': ['entertainment', 'funny', 'comedy', 'viral', 'trending'],
            'Music': ['music', 'song', 'artist', 'album', 'concert', 'performance'],
            'Sports': ['sports', 'fitness', 'workout', 'training', 'athlete', 'competition'],
        }
        
        base_tags = tag_sets.get(category, ['video', 'content', 'Youtube'])
        selected_tags = random.sample(base_tags, min(4, len(base_tags)))
        
        general_tags = ['2024', 'new', 'best', 'top', 'amazing', 'must-watch']
        selected_tags.extend(random.sample(general_tags, 2))
        
        return selected_tags

    def generate_channel_name(self, category):
        channel_patterns = {
            'Technology': ['{name} Tech', 'Code with {name}', '{name} Dev', 'Tech {name}'],
            'Gaming': ['{name} Gaming', 'Gamer {name}', '{name} Plays', 'Gaming with {name}'],
            'Education': ['{name} Academy', 'Learn with {name}', '{name} Explains', 'Prof {name}'],
            'Entertainment': ['{name} Entertainment', 'Fun with {name}', '{name} Show'],
        }
        
        patterns = channel_patterns.get(category, ['{name} Channel', '{name} TV', '{name} Videos'])
        pattern = random.choice(patterns)
        name = self.fake.first_name()
        
        return pattern.format(name=name)