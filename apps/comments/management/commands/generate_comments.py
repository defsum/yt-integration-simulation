import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from apps.comments.models import Comment
from apps.videos.models import Video


class Command(BaseCommand):
    help = 'Generate realistic comments for videos' 
    # python manage.py generate_comments --count 500

    def add_arguments(self, parser): # arguments for the command
        parser.add_argument(
            '--count',
            type=int,
            default=200,
            help='Number of comments to generate (default: 200)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing comments before generating new ones',
        )
        parser.add_argument(
            '--video-id',
            type=int,
            help='Generate comments for a specific video ID',
        )
        parser.add_argument(
            '--ai-ratio',
            type=float,
            default=0.3,
            help='Ratio of AI-generated comments (0.0-1.0, default: 0.3)',
        )
        parser.add_argument(
            '--replies-ratio',
            type=float,
            default=0.2,
            help='Ratio of comments that are replies (0.0-1.0, default: 0.2)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing comments...')
            Comment.objects.all().delete()

        # get videos to comment on
        if options['video_id']:
            videos = Video.objects.filter(id=options['video_id'], status='published')
            if not videos.exists():
                self.stdout.write(
                    self.style.ERROR(f'Video with ID {options["video_id"]} not found or not published')
                )
                return
        else:
            videos = Video.objects.published().annotate(
                comment_count_actual=Count('comments')
            ).order_by('comment_count_actual')

        if not videos.exists():
            self.stdout.write(
                self.style.ERROR('No published videos found. Run generate_videos first.')
            )
            return

        count = options['count']
        ai_ratio = options['ai_ratio']
        replies_ratio = options['replies_ratio']
        
        self.stdout.write(f'Generating {count} comments...')
        self.stdout.write(f'AI comment ratio: {ai_ratio:.1%}')
        self.stdout.write(f'Reply ratio: {replies_ratio:.1%}')
        
        comments_created = 0
        replies_created = 0

        with transaction.atomic():
            for i in range(count):
                # select video (favor videos with fewer comments)
                video = self.select_video_weighted(videos)
                
                # decide if this should be a reply
                is_reply = random.random() < replies_ratio
                parent_comment = None
                
                if is_reply:
                    # Get existing top-level comments for this video
                    top_level_comments = Comment.objects.filter(
                        video=video,
                        parent_comment__isnull=True,
                        is_approved=True
                    )
                    
                    if top_level_comments.exists():
                        parent_comment = random.choice(top_level_comments)

                is_ai = random.random() < ai_ratio
                
                if is_ai and not parent_comment:  # AI only generates top-level comments
                    comment = Comment.generate_user_comment(video)
                else:
                    comment = self.generate_human_comment(video, parent_comment)

                if parent_comment:
                    replies_created += 1
                else:
                    comments_created += 1
                
                if i % 50 == 0:
                    self.stdout.write(f'Generated {i} comments...')

        self.stdout.write('Updating video comment counts...')
        for video in videos:
            video.update_comment_count()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated {comments_created} TOP-LEVEL comments '
                f'and {replies_created} replies'
            )
        )

    def select_video_weighted(self, videos):
        videos_list = list(videos[:50])
        
        if not videos_list:
            return random.choice(videos)
        
        # Weight inversely to comment count (videos with fewer comments get higher weight)
        max_comments = max(v.comment_count_actual for v in videos_list)
        weights = []
        
        for video in videos_list:
            # and inverse weight: videos with fewer comments get higher probability
            weight = max_comments - video.comment_count_actual + 1
            weights.append(weight)
        
        return random.choices(videos_list, weights=weights)[0]

    def generate_human_comment(self, video, parent_comment=None):
        from faker import Faker
        fake = Faker()
        
        if parent_comment:
            # parent comment is not null
            reply_templates = [
                "Great point! I totally agree.",
                "Thanks for sharing this perspective.",
                "I had the same experience!",
                "Interesting take on this topic.",
                "Can you elaborate on that?",
                "This helped me understand better.",
                "I disagree, but I respect your opinion.",
                "Thanks for the detailed explanation!",
                "This is exactly what I was looking for.",
                "Have you tried the method mentioned in the video?",
            ]
            content = random.choice(reply_templates)
        else:
            # generate main comment based on video category
            if video.category:
                content = self.generate_category_comment(video.category.name, video.title)
            else:
                content = self.generate_generic_comment(video.title)
        
        # some emojis to make it more fun :D
        if random.random() < 0.1:  # 10% chance to add emoji
            emojis = ['👍', '😊', '🔥', '💯', '👌', '🙌', '❤️', '😍']
            content += f" {random.choice(emojis)}"
        
        comment = Comment.objects.create(
            video=video,
            parent_comment=parent_comment,
            content=content,
            author_name=fake.name(),
            is_ai_generated=False,
            is_approved=True,
            like_count=random.randint(0, 20)
        )
        
        return comment

    def generate_category_comment(self, category, title):
        category_templates = {
            'Technology': [
                "This technology looks promising!",
                "Great tutorial, very clear explanations.",
                "When will this be available for production use?",
                "I've been waiting for something like this.",
                "The documentation could be better, but this is a good start.",
                "Performance looks impressive in the demos.",
            ],
            'Gaming': [
                "Epic gameplay! How did you get so good?",
                "What's your setup for recording?",
                "This game looks amazing, definitely trying it.",
                "Your commentary is hilarious!",
                "Can you do a tutorial on that combo?",
                "The graphics in this game are incredible.",
            ],
            'Education': [
                "Thank you for this clear explanation!",
                "This helped me understand the concept finally.",
                "Could you make a video about advanced topics?",
                "Perfect timing, I have an exam next week!",
                "Your teaching style is really effective.",
                "Any recommended books on this topic?",
            ],
            'Entertainment': [
                "This made my day! So funny!",
                "I can't stop laughing at this part.",
                "Please make more content like this!",
                "Your editing skills are on point.",
                "This deserves way more views.",
                "I've watched this 5 times already.",
            ],
            'Music': [
                "This song is stuck in my head now!",
                "Amazing vocals and production quality.",
                "When is the full album coming out?",
                "This gives me chills every time.",
                "The lyrics are so meaningful.",
                "Perfect song for my playlist.",
            ],
        }
        
        templates = category_templates.get(category, [
            "Great content!",
            "Thanks for sharing this.",
            "Really enjoyed watching this.",
            "Keep up the good work!",
            "This was very informative.",
        ])
        
        return random.choice(templates)

    def generate_generic_comment(self, title):
        generic_templates = [
            "Excellent video! Very informative.",
            "Thanks for sharing this content.",
            "I learned something new today.",
            "Great work on this video!",
            "This deserves more views.",
            "Keep creating amazing content!",
            "Very well explained, thank you.",
            "This helped me a lot.",
            "Looking forward to more videos like this.",
            "Subscribed after watching this!",
        ]
        
        return random.choice(generic_templates)