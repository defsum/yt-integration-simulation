import random
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.conf import settings

from apps.core.models import TimeStampedModel, SoftDeleteModel


class VideoCategory(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Video Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class VideoManager(models.Manager):
    def published(self):
        return self.filter(status='published')

    def popular(self):
        return self.annotate(
            engagement_score=models.F('like_count') + models.F('comment_count')
        ).order_by('-engagement_score')

    def trending(self):
        from django.utils import timezone
        from datetime import timedelta
        
        recent_date = timezone.now() - timedelta(days=7)
        return self.filter(
            created_at__gte=recent_date
        ).annotate(
            engagement_score=models.F('like_count') + models.F('comment_count')
        ).order_by('-engagement_score')


class Video(SoftDeleteModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('unlisted', 'Unlisted'),
        ('private', 'Private'),
    ]

    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        VideoCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='videos'
    )
    
    duration = models.PositiveIntegerField(
        help_text="Duration in seconds",
        validators=[MinValueValidator(1), MaxValueValidator(86400)]
    )
    video_url = models.URLField(
        help_text="Mock URL for video file",
        blank=True
    )
    thumbnail_url = models.URLField(
        help_text="Mock URL for video thumbnail",
        blank=True
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    published_at = models.DateTimeField(null=True, blank=True)
    
    channel_name = models.CharField(max_length=100, db_index=True)
    channel_avatar_url = models.URLField(blank=True)
    
    view_count = models.PositiveIntegerField(default=0, db_index=True)
    like_count = models.PositiveIntegerField(default=0)
    dislike_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    
    tags = models.JSONField(default=list, blank=True)
    language = models.CharField(max_length=10, default='en')
    
    objects = VideoManager()

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['channel_name', 'status']),
            models.Index(fields=['-view_count']),
            models.Index(fields=['-like_count']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        
        # generate mock URLs if not provided (just for fun)
        if not self.video_url:
            self.video_url = f"https://mock-video-storage.com/videos/{self.slug}.mp4"
        if not self.thumbnail_url:
            self.thumbnail_url = f"https://mock-video-storage.com/thumbnails/{self.slug}.jpg"
        
        super().save(*args, **kwargs)

    # def get_absolute_url(self):
    #     return reverse('videos:detail', kwargs={'slug': self.slug})

    @property
    def duration_formatted(self):
        minutes = self.duration // 60
        seconds = self.duration % 60
        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @property
    def engagement_rate(self):
        if self.view_count == 0:
            return 0
        return (self.like_count / self.view_count) * 100

    @property
    def like_ratio(self):
        total_reactions = self.like_count + self.dislike_count
        if total_reactions == 0:
            return 0
        return (self.like_count / total_reactions) * 100

    def increment_view_count(self):
        Video.objects.filter(pk=self.pk).update(view_count=models.F('view_count') + 1)
        self.refresh_from_db(fields=['view_count'])

    def add_like(self):
        Video.objects.filter(pk=self.pk).update(like_count=models.F('like_count') + 1)
        self.refresh_from_db(fields=['like_count'])

    def add_dislike(self):
        Video.objects.filter(pk=self.pk).update(dislike_count=models.F('dislike_count') + 1)
        self.refresh_from_db(fields=['dislike_count'])

    def update_comment_count(self):
        count = self.comments.filter(is_approved=True).count()
        Video.objects.filter(pk=self.pk).update(comment_count=count)
        self.refresh_from_db(fields=['comment_count'])

    @classmethod
    def get_random_trending(cls, limit=10):
        trending_videos = list(cls.objects.trending()[:limit * 2])
        return random.sample(trending_videos, min(limit, len(trending_videos)))