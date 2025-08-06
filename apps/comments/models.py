from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class CommentManager(models.Manager):
    def approved(self):
        return self.filter(is_approved=True)

    def top_level(self):
        return self.filter(parent_comment__isnull=True)


class Comment(TimeStampedModel):
    
    # core fields
    video = models.ForeignKey(
        'videos.Video',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    content = models.TextField(max_length=1000)  # Reduced from 10000
    
    # author info
    author_name = models.CharField(max_length=100)
    author_avatar_url = models.URLField(blank=True)
    
    # simple metrics
    like_count = models.PositiveIntegerField(default=0)
    
    # basic flags
    is_approved = models.BooleanField(default=True)
    is_ai_generated = models.BooleanField(default=False)
    
    # simple AI tracking
    ai_model_used = models.CharField(max_length=50, blank=True)
    
    objects = CommentManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['video', 'is_approved']),
            models.Index(fields=['is_ai_generated']),
        ]

    def __str__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.author_name}: {preview}"

    def save(self, *args, **kwargs):
        # auto-generate avatar if not provided
        if not self.author_avatar_url:
            self.author_avatar_url = f"https://ui-avatars.com/api/?name={self.author_name}&background=random"
        
        super().save(*args, **kwargs)
        
        # update video comment count
        self.video.update_comment_count()

    @property
    def is_reply(self):
        return self.parent_comment is not None

    def add_like(self):
        self.like_count += 1
        self.save(update_fields=['like_count'])

    # class methods for AI functionality
    @classmethod
    def generate_user_comment(cls, video):
        from .ai_engine import youtube_ai_engine
        return youtube_ai_engine.generate_user_comment(video)

    @classmethod
    def analyze_for_business_opportunity(cls, comment):
        from .ai_engine import youtube_ai_engine
        return youtube_ai_engine.analyze_comment_for_business_opportunity(comment)

    @classmethod
    def generate_business_reply(cls, user_comment, analysis=None):
        from .ai_engine import youtube_ai_engine
        if analysis is None:
            analysis = cls.analyze_for_business_opportunity(user_comment)
        return youtube_ai_engine.generate_business_reply(user_comment, analysis)

    @classmethod
    def generate_channel_promotional_comment(cls, video, offer_type=None):
        from .ai_engine import youtube_ai_engine
        return youtube_ai_engine.generate_channel_promotional_comment(video, offer_type)