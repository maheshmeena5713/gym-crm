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

    def authenticate(self, request, gym=None, identifier=None, password=None, entity_type=None, entity_id=None, **kwargs):
        if not identifier or not password:
            return None

        user = None

        # 1. Scoped Login (Gym Owner / Staff)
        if gym:
            user = GymUser.objects.filter(
                gym=gym, email__iexact=identifier, is_active=True
            ).first()
            if not user:
                user = GymUser.objects.filter(
                    gym=gym, username__iexact=identifier, is_active=True
                ).first()
            # Finally try phone
            if not user:
                 user = GymUser.objects.filter(
                    gym=gym, phone=identifier, is_active=True
                ).first()

        # 2. Enterprise Entity Scoped Login
        elif entity_type and entity_id:
            # Search global user first
            user = GymUser.objects.filter(email__iexact=identifier, is_active=True).first()
            if not user:
                user = GymUser.objects.filter(username__iexact=identifier, is_active=True).first()
            if not user:
                user = GymUser.objects.filter(phone=identifier, is_active=True).first()
            
            # Verify scoping
            if user:
                if entity_type == 'holding':
                    if str(user.holding_company_id) != str(entity_id) and not user.is_superuser:
                        return None
                elif entity_type == 'brand':
                    if str(user.brand_id) != str(entity_id) and not user.is_superuser:
                        return None
                elif entity_type == 'org':
                    if str(user.organization_id) != str(entity_id) and not user.is_superuser:
                         return None
        
        # 3. Global Login Fallback (e.g. Superuser at /admin/)
        else:
            # Only allow if user is NOT tied to a specific gym (Enterprise Role) OR is Superuser
            user = GymUser.objects.filter(
                email__iexact=identifier, is_active=True
            ).first()
            if not user:
                user = GymUser.objects.filter(
                    username__iexact=identifier, is_active=True
                ).first()
            if not user:
                user = GymUser.objects.filter(
                    phone=identifier, is_active=True
                ).first()
            
            # Additional Check: If authenticating globally without gym context, 
            # ensure they are indeed an Enterprise user or Superuser.
            if user:
                if user.role not in [
                    'holding_admin', 'brand_admin', 'org_admin'
                ] and not user.is_superuser:
                     # Check if we should allow gym users to login globally? 
                     # For now, restrict gym users to gym context login.
                     if user.gym:
                         return None

        if user and user.has_usable_password() and user.check_password(password):
            return user

        return None
        return None

    def get_user(self, user_id):
        try:
            return GymUser.objects.get(pk=user_id)
        except GymUser.DoesNotExist:
            return None
