"""
Core Permissions - Role-based access control for Gym AI SaaS.
"""

from rest_framework.permissions import BasePermission


class IsGymStaff(BasePermission):
    """
    Allow any authenticated user who is assigned to a gym.
    Denies access if the user has no gym association.
    """
    message = "You must be associated with a gym to access this resource."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.gym is not None
        )


class IsGymOwner(BasePermission):
    """
    Allow only gym owners.
    Owners can see/manage everything within their gym.
    """
    message = "Only gym owners can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.gym is not None
            and request.user.role == 'owner'
        )


class IsGymOwnerOrManager(BasePermission):
    """
    Allow gym owners and managers.
    """
    message = "Only gym owners or managers can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.gym is not None
            and request.user.role in ('owner', 'manager')
        )


class IsGymTrainer(BasePermission):
    """
    Allow gym trainers (and above).
    Trainers can only see members assigned to them (enforced via queryset filtering).
    """
    message = "Only trainers can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.gym is not None
            and request.user.role in ('owner', 'manager', 'trainer')
        )


class CanManageMembers(BasePermission):
    """
    Check if the user has the can_manage_members flag.
    """
    message = "You do not have permission to manage members."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.can_manage_members
        )


class CanManageLeads(BasePermission):
    """
    Check if the user has the can_manage_leads flag.
    """
    message = "You do not have permission to manage leads."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.can_manage_leads
        )


class GymScopedMixin:
    """
    Mixin for ViewSets that auto-scopes querysets to the user's gym.
    Also handles trainer-level scoping (only assigned members).
    """

    gym_field = 'gym'  # FK field name on the model
    trainer_scope_field = None  # Set to 'assigned_trainer' for Member

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated or not user.gym:
            return qs.none()

        # Scope to user's gym
        qs = qs.filter(**{self.gym_field: user.gym})

        # Extra scope for trainers: only see assigned members
        if (
            self.trainer_scope_field
            and user.role == 'trainer'
        ):
            qs = qs.filter(**{self.trainer_scope_field: user})

        return qs

    def perform_create(self, serializer):
        """Auto-set gym on creation."""
        serializer.save(**{self.gym_field: self.request.user.gym})
