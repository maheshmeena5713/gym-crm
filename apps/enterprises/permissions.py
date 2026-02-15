from rest_framework import permissions
from apps.users.models import GymUser

class IsHoldingAdmin(permissions.BasePermission):
    """
    Allocates access to Holding Company Admins.
    They can access everything under their holding company.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == GymUser.Role.HOLDING_ADMIN

    def has_object_permission(self, request, view, obj):
        # Logic to check if obj belongs to user.holding_company
        # This requires models to have a path back to HoldingCompany
        return True # Simplified for now, needs robust implementation

class IsBrandAdmin(permissions.BasePermission):
    """
    Access for Brand Admins.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in [GymUser.Role.HOLDING_ADMIN, GymUser.Role.BRAND_ADMIN]

class IsOrgAdmin(permissions.BasePermission):
    """
    Access for Organization Admins (Franchise Owners).
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Higher roles also have permission
        allowed_roles = [
            GymUser.Role.HOLDING_ADMIN, 
            GymUser.Role.BRAND_ADMIN, 
            GymUser.Role.ORG_ADMIN
        ]
        return request.user.role in allowed_roles

class IsLocationManager(permissions.BasePermission):
    """
    Access for Branch Managers and above.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        allowed_roles = [
            GymUser.Role.HOLDING_ADMIN, 
            GymUser.Role.BRAND_ADMIN, 
            GymUser.Role.ORG_ADMIN,
            GymUser.Role.REGION_MANAGER,
            GymUser.Role.OWNER, # Legacy
            GymUser.Role.MANAGER
        ]
        return request.user.role in allowed_roles
