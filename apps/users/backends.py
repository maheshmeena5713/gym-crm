"""
Custom authentication backends for multi-method login.
Supports: Phone+OTP (default Django), Email+Password, Username+Password.
"""

from django.contrib.auth.backends import BaseBackend

from apps.users.models import GymUser


class GymPasswordBackend(BaseBackend):
    """
    Authenticate by email or username + password, scoped to a gym.
    Used for the 'Password Login' tab in the login flow.
    """

    def authenticate(self, request, gym=None, identifier=None, password=None, **kwargs):
        if not gym or not identifier or not password:
            return None

        # Try email first (case-insensitive)
        user = GymUser.objects.filter(
            gym=gym, email__iexact=identifier, is_active=True
        ).first()

        # Then try username (case-insensitive)
        if not user:
            user = GymUser.objects.filter(
                gym=gym, username__iexact=identifier, is_active=True
            ).first()

        if user and user.has_usable_password() and user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        try:
            return GymUser.objects.get(pk=user_id)
        except GymUser.DoesNotExist:
            return None
