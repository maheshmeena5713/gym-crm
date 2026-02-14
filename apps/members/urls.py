"""
Members URL Configuration - REST Router.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.members.views import MemberViewSet, MembershipPlanViewSet

app_name = 'members'

router = DefaultRouter()
router.register(r'', MemberViewSet, basename='member')

# Nested under /api/v1/membership-plans/
plan_router = DefaultRouter()
plan_router.register(r'', MembershipPlanViewSet, basename='membership-plan')

urlpatterns = [
    path('', include(router.urls)),
]

plan_urlpatterns = [
    path('', include(plan_router.urls)),
]
