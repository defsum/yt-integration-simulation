"""
views for the comments API
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Q, Prefetch

from .models import Comment
from .serializers import (
    CommentListSerializer, CommentDetailSerializer, CommentCreateSerializer,
    AICommentGenerationSerializer, CommentAnalysisSerializer,
    ChannelPromotionalCommentSerializer
)
from apps.videos.models import Video


class CommentViewSet(viewsets.ModelViewSet):
    # viewset for comments with full CRUD operations and custom actions
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['content', 'author_name']
    filterset_fields = ['video', 'author_name', 'is_ai_generated', 'is_approved']
    ordering_fields = ['created_at', 'like_count']
    ordering = ['-created_at']

    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            queryset = Comment.objects.approved()
        else:
            queryset = Comment.objects.all()
        
        if self.action == 'list':
            queryset = queryset.select_related('video', 'parent_comment')
        elif self.action == 'retrieve':
            queryset = queryset.select_related('video', 'parent_comment').prefetch_related(
                Prefetch(
                    'replies',
                    queryset=Comment.objects.approved().order_by('created_at'),
                    to_attr='prefetched_replies'
                )
            )
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return CommentListSerializer
        elif self.action == 'create':
            return CommentCreateSerializer
        elif self.action == 'generate_ai':
            return AICommentGenerationSerializer
        elif self.action == 'analyze_and_reply':
            return CommentAnalysisSerializer
        else:
            return CommentDetailSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return response

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        comment.add_like()
        
        return Response({
            'message': 'Comment liked successfully',
            'like_count': comment.like_count
        })

    @action(detail=False, methods=['post'])
    def generate_user_comments(self, request):
        serializer = AICommentGenerationSerializer(data=request.data)
        if serializer.is_valid():
            video = serializer.validated_data['video_id']
            count = serializer.validated_data['count']
            
            generated_comments = []
            for _ in range(count):
                comment = Comment.generate_user_comment(video=video)
                generated_comments.append(comment)
            
            response_data = CommentListSerializer(generated_comments, many=True).data
            
            return Response({
                'message': f'Generated {count} realistic user comments',
                'comment_type': 'user_simulation',
                'comments': response_data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def analyze_and_reply(self, request):
        serializer = CommentAnalysisSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        video = serializer.validated_data['video_id']
        user_comments = Comment.objects.filter(
            video=video,
            parent_comment__isnull=True
        ).order_by('-created_at')[:10]
        
        results = []
        business_replies = []
        
        for comment in user_comments:
            analysis = Comment.analyze_for_business_opportunity(comment)
            
            result = {
                'comment_id': comment.id,
                'comment_content': comment.content,
                'analysis': analysis
            }
            
            if analysis['should_reply']:
                business_reply = Comment.generate_business_reply(comment)
                if business_reply:
                    result['business_reply'] = {
                        'id': business_reply.id,
                        'content': business_reply.content,
                        'author': business_reply.author_name
                    }
                    business_replies.append(business_reply)
            
            results.append(result)
        
        return Response({
            'message': f'Analyzed {len(user_comments)} comments, generated {len(business_replies)} business replies',
            'techtest_workflow': 'comment_analysis_and_business_engagement',
            'video_title': video.title,
            'analysis_results': results
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def generate_business_engagement(self, request):
        data = request.data.copy()
        data['comment_type'] = 'business_engagement'
        data['include_business_offers'] = True
        
        serializer = AICommentGenerationSerializer(data=data)
        if serializer.is_valid():
            video = serializer.validated_data['video_id']
            sentiment = serializer.validated_data.get('sentiment', 'positive')
            count = serializer.validated_data.get('count', 3)
            parent_comment = serializer.validated_data.get('parent_comment_id')
            
            generated_comments = []
            for _ in range(count):
                comment = Comment.generate_ai_comment(
                    video=video,
                    parent_comment=parent_comment,
                    sentiment=sentiment,
                    include_business_offer=True
                )
                generated_comments.append(comment)
            
            response_data = CommentListSerializer(generated_comments, many=True).data
            
            return Response({
                'message': f'Generated {count} business engagement comments successfully',
                'business_model': 'Youtube AI-powered engagement system',
                'features': [
                    'Contextual promotional offers',
                    'Sentiment-aware responses', 
                    'Business opportunity detection',
                    'Natural engagement patterns'
                ],
                'comments': response_data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def generate_channel_promotion(self, request):
        from .serializers import ChannelPromotionalCommentSerializer
        
        serializer = ChannelPromotionalCommentSerializer(data=request.data)
        if serializer.is_valid():
            video = serializer.validated_data['video_id']
            offer_type = serializer.validated_data.get('offer_type')
            
            promo_comment = Comment.generate_channel_promotional_comment(
                video=video,
                offer_type=offer_type
            )
            
            response_data = CommentListSerializer(promo_comment).data
            
            return Response({
                'message': 'Channel promotional comment generated successfully',
                'comment_type': 'channel_promotion',
                'channel_name': video.channel_name,
                'offer_type': offer_type or 'random',
                'comment': response_data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)