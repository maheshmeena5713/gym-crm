"""
Membership Plans URL Configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.members.views import MembershipPlanViewSet

app_name = 'membership-plans'

router = DefaultRouter()
router.register(r'', MembershipPlanViewSet, basename='membership-plan')

urlpatterns = [
    path('', include(router.urls)),
]
