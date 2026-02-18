"""
GymEdge - URL Configuration
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.shortcuts import redirect
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# Admin site customization
admin.site.site_header = "GymEdge Admin"
admin.site.site_title = "GymEdge"
admin.site.index_title = "Dashboard"

# API v1 routes
api_v1_urlpatterns = [
    path('auth/', include('apps.users.urls')),
    path('members/', include('apps.members.urls')),
    path('membership-plans/', include('apps.members.urls_plans')),
    path('enterprises/', include('apps.enterprises.urls')),
]

urlpatterns = [

    # Admin
    path('admin/', admin.site.urls),

    # Frontend (Template-based)
    path('', include('apps.frontend.urls')),

    # API v1
    path('api/v1/', include((api_v1_urlpatterns, 'api-v1'))),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
