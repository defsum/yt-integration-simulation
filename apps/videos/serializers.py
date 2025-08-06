from rest_framework import serializers
from django.utils import timezone
from django.core.validators import URLValidator

from .models import Video, VideoCategory


class VideoCategorySerializer(serializers.ModelSerializer):
    video_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = VideoCategory
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'video_count']
        read_only_fields = ['slug']

    def validate_name(self, value):
        if VideoCategory.objects.filter(name__iexact=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value


class VideoListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    engagement_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'slug', 'description', 'category_name',
            'duration', 'duration_formatted', 'thumbnail_url',
            'channel_name', 'channel_avatar_url', 'view_count',
            'like_count', 'comment_count', 'engagement_rate',
            'published_at', 'status'
        ]


class VideoDetailSerializer(serializers.ModelSerializer):
    category = VideoCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=VideoCategory.objects.filter(is_active=True),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )
    duration_formatted = serializers.CharField(read_only=True)
    engagement_rate = serializers.FloatField(read_only=True)
    like_ratio = serializers.FloatField(read_only=True)
    comments_count = serializers.IntegerField(source='comment_count', read_only=True)
    
    # Validation fields
    tags_count = serializers.SerializerMethodField()
    is_trending = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'slug', 'description', 'category', 'category_id',
            'duration', 'duration_formatted', 'video_url', 'thumbnail_url',
            'status', 'published_at', 'channel_name', 'channel_avatar_url',
            'view_count', 'like_count', 'dislike_count', 'comment_count',
            'comments_count', 'tags', 'tags_count', 'language',
            'engagement_rate', 'like_ratio', 'is_trending',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'slug', 'view_count', 'like_count', 'dislike_count', 
            'comment_count', 'created_at', 'updated_at'
        ]

    def get_tags_count(self, obj):
        return len(obj.tags) if obj.tags else 0

    def get_is_trending(self, obj):
        return obj.trending_records.filter(
            trending_date=timezone.now().date(),
            is_active=True
        ).exists()

    def validate_duration(self, value):
        if value < 1:
            raise serializers.ValidationError("Duration must be at least 1 second.")
        if value > 86400:  # 24 hours
            raise serializers.ValidationError("Duration cannot exceed 24 hours.")
        return value

    def validate_tags(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list.")
        
        if len(value) > 20:
            raise serializers.ValidationError("Cannot have more than 20 tags.")
        
        for tag in value:
            if not isinstance(tag, str):
                raise serializers.ValidationError("All tags must be strings.")
            if len(tag) > 50:
                raise serializers.ValidationError("Individual tags cannot exceed 50 characters.")
        
        return value

    def validate_video_url(self, value):
        if value:
            validator = URLValidator()
            try:
                validator(value)
            except:
                raise serializers.ValidationError("Invalid URL format.")
        return value

    def validate_thumbnail_url(self, value):
        if value:
            validator = URLValidator()
            try:
                validator(value)
            except:
                raise serializers.ValidationError("Invalid URL format.")
        return value

    def validate(self, data):
        if data.get('status') == 'published':
            if not data.get('title'):
                raise serializers.ValidationError("Published videos must have a title.")
            if not data.get('duration'):
                raise serializers.ValidationError("Published videos must have a duration.")
        
        return data


class VideoCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=VideoCategory.objects.filter(is_active=True),
        source='category',
        required=False,
        allow_null=True
    )

    class Meta:
        model = Video
        fields = [
            'title', 'description', 'category_id', 'duration',
            'channel_name', 'tags', 'language', 'status'
        ]

    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        
        if Video.objects.filter(
            title__iexact=value,
            channel_name=self.initial_data.get('channel_name', '')
        ).exists():
            raise serializers.ValidationError(
                "A video with this title already exists on this channel."
            )
        
        return value.strip()

    def create(self, validated_data):
        video = Video.objects.create(**validated_data)
        
        # auto-publish if status is published
        if video.status == 'published' and not video.published_at:
            video.published_at = timezone.now()
            video.save(update_fields=['published_at'])
        
        return video


class VideoUpdateSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=VideoCategory.objects.filter(is_active=True),
        source='category',
        required=False,
        allow_null=True
    )

    class Meta:
        model = Video
        fields = [
            'title', 'description', 'category_id', 'duration',
            'channel_name', 'tags', 'language', 'status'
        ]

    def update(self, instance, validated_data):
        old_status = instance.status
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # handle status changes
        if validated_data.get('status') == 'published' and old_status != 'published':
            if not instance.published_at:
                instance.published_at = timezone.now()
        
        instance.save()
        return instance


class VideoStatsSerializer(serializers.ModelSerializer):
    engagement_rate = serializers.FloatField(read_only=True)
    like_ratio = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'view_count', 'like_count', 
            'dislike_count', 'comment_count', 'engagement_rate', 
            'like_ratio', 'published_at'
        ]