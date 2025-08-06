"""
API URL configu for videos
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import VideoViewSet, VideoCategoryViewSet

app_name = 'videos_api'

# DRF Router for API endpoints
router = DefaultRouter()
router.register(r'categories', VideoCategoryViewSet)
router.register(r'', VideoViewSet, basename='video')

urlpatterns = [
    path('', include(router.urls)),
]