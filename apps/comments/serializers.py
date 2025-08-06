"""
simple serializers for comment API endpoints
"""

from rest_framework import serializers
from .models import Comment
from apps.videos.models import Video


class CommentListSerializer(serializers.ModelSerializer):
    video_title = serializers.CharField(source='video.title', read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'author_name', 'video_title',
            'like_count', 'is_ai_generated', 'created_at'
        ]


class CommentDetailSerializer(serializers.ModelSerializer):
    video_title = serializers.CharField(source='video.title', read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'author_name', 'author_avatar_url',
            'video_title', 'like_count', 'replies', 'is_ai_generated',
            'created_at', 'updated_at'
        ]
    
    def get_replies(self, obj):
        replies = obj.replies.filter(is_approved=True)[:10]  # Limit replies
        return CommentListSerializer(replies, many=True).data


class CommentCreateSerializer(serializers.ModelSerializer):
    video_id = serializers.PrimaryKeyRelatedField(
        queryset=Video.objects.all(),
        source='video',
        write_only=True
    )
    
    class Meta:
        model = Comment
        fields = ['content', 'author_name', 'video_id']
    
    def create(self, validated_data):
        validated_data['is_ai_generated'] = False
        validated_data['is_approved'] = True
        return super().create(validated_data)


class AICommentGenerationSerializer(serializers.Serializer):
    video_id = serializers.PrimaryKeyRelatedField(queryset=Video.objects.all())
    count = serializers.IntegerField(min_value=1, max_value=20, default=5)


class CommentAnalysisSerializer(serializers.Serializer):
    video_id = serializers.PrimaryKeyRelatedField(queryset=Video.objects.all())


class ChannelPromotionalCommentSerializer(serializers.Serializer):
    video_id = serializers.PrimaryKeyRelatedField(queryset=Video.objects.all())
    offer_type = serializers.CharField(required=False, allow_blank=True)