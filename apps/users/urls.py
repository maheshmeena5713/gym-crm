"""
Users URL Configuration - Auth routes.
"""

from django.urls import path

from apps.users.views import SendOTPView, VerifyOTPView, UserProfileView, SelectAccountView

app_name = 'users'

urlpatterns = [
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('select-account/', SelectAccountView.as_view(), name='select-account'),
    path('profile/', UserProfileView.as_view(), name='profile'),
]
