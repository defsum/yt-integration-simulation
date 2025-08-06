"""
core views
"""

from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.videos.models import Video, VideoCategory
from apps.comments.models import Comment


def home_view(request):
    stats = {
        'total_videos': Video.objects.count(),
        'published_videos': Video.objects.published().count(),
        'total_comments': Comment.objects.count(),
        'total_categories': VideoCategory.objects.count(),
    }
    
    context = {
        'title': 'Youtube Integration Simulation',
        'description': 'Small Django project that simulates a Youtube integration',
        'stats': stats,
        'api_endpoints': [
            {
                'name': 'Videos',
                'url': '/api/v1/videos/'
            },
            {
                'name': 'Comments', 
                'url': '/api/v1/comments/'
            },
            {
                'name': 'Docs',
                'url': '/api/docs/'
            },
            {
                'name': 'Admin Panel',
                'url': '/admin/'
            }
        ]
    }
    
    return render(request, 'home.html', context)


@api_view(['GET'])
def api_status(request):
    stats = {
        'status': 'operational',
        'database': {
            'videos': Video.objects.count(),
            'published_videos': Video.objects.published().count(),
            'comments': Comment.objects.count(),
            'categories': VideoCategory.objects.count(),
    
        },
        'features': {
            'video_management': True,
            'comment_system': True,
            'ai_comment_generation': True,
            'engagement_tracking': True,
            'api_documentation': True,
        },
        'api_version': '1.0.0'
    }
    
    return Response(stats)


@api_view(['GET'])
def health_check(request):
    return Response({
        'status': 'healthy',
        'timestamp': request.META.get('HTTP_DATE', 'unknown')
    })