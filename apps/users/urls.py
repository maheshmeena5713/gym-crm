"""
Users URL Configuration - Auth routes.
"""

from django.urls import path

from apps.users.views import (
    SendOTPView,
    VerifyOTPView,
    UserProfileView,
    SelectAccountView,
    UnifiedLoginView,
)

app_name = 'users'

urlpatterns = [
    # Unified Login (Primary)
    path('login/', UnifiedLoginView.as_view(), name='login'),
    
    # OTP-based Login (Alternative)
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('select-account/', SelectAccountView.as_view(), name='select-account'),
    
    # User Profile
    path('profile/', UserProfileView.as_view(), name='profile'),
]

