from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Video, VideoCategory
from .serializers import (
    VideoListSerializer, VideoDetailSerializer, VideoCreateSerializer,
    VideoCategorySerializer
)


class VideoCategoryViewSet(viewsets.ModelViewSet):
    queryset = VideoCategory.objects.all()
    serializer_class = VideoCategorySerializer
    search_fields = ['name', 'description']
    filterset_fields = ['is_active']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.select_related('category').prefetch_related('comments')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'channel_name']
    filterset_fields = ['category', 'status', 'language']
    ordering_fields = ['created_at', 'published_at', 'view_count', 'like_count']
    ordering = ['-published_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return VideoListSerializer
        elif self.action == 'create':
            return VideoCreateSerializer
        else:
            return VideoDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # public users only see published videos
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='published')
        
        return queryset

    @action(detail=True, methods=['post'])
    def toggle_like(self, request, pk=None):
        video = self.get_object()
        video.like_count += 1
        video.save(update_fields=['like_count'])
        
        return Response({
            'message': 'Video liked successfully',
            'like_count': video.like_count
        })

    @action(detail=True, methods=['post'])
    def toggle_dislike(self, request, pk=None):
        video = self.get_object()
        video.dislike_count += 1
        video.save(update_fields=['dislike_count'])
        
        return Response({
            'message': 'Video disliked',
            'dislike_count': video.dislike_count
        })

    @action(detail=False, methods=['get'])
    def trending(self, request):
        trending_videos = self.get_queryset().filter(
            status='published'
        ).order_by('-view_count', '-like_count')[:10]
        
        serializer = self.get_serializer(trending_videos, many=True)
        return Response({
            'message': 'Trending videos retrieved successfully',
            'count': len(trending_videos),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response(
                {'error': 'category_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            category = VideoCategory.objects.get(id=category_id)
        except VideoCategory.DoesNotExist:
            return Response(
                {'error': 'Category not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        videos = self.get_queryset().filter(category=category)
        page = self.paginate_queryset(videos)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(videos, many=True)
        return Response({
            'category': category.name,
            'count': videos.count(),
            'results': serializer.data
        })