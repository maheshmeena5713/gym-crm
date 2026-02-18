"""
Users Serializers - OTP auth and user profile.
"""

import re

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from apps.users.models import GymUser


# ── OTP Serializers ───────────────────────────────────────────

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Send OTP',
            value={'phone': '9876543210'},
            request_only=True,
        ),
    ]
)
class SendOTPSerializer(serializers.Serializer):
    """Validate phone number for OTP dispatch."""
    phone = serializers.CharField(max_length=20)

    def validate_phone(self, value):
        # Strip whitespace and any + prefix
        phone = re.sub(r'\s+', '', value)
        if phone.startswith('+'):
            phone = phone[1:]

        # Validate: 10 digits (India) or 10+ with country code
        if not re.match(r'^\d{10,15}$', phone):
            raise serializers.ValidationError("Invalid phone number. Must be 10-15 digits.")

        return phone


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Verify OTP',
            value={'phone': '9876543210', 'otp': '123456'},
            request_only=True,
        ),
    ]
)
class VerifyOTPSerializer(serializers.Serializer):
    """Validate phone + OTP code."""
    phone = serializers.CharField(max_length=20)
    otp = serializers.CharField(max_length=6, min_length=4)

    def validate_phone(self, value):
        phone = re.sub(r'\s+', '', value)
        if phone.startswith('+'):
            phone = phone[1:]
        if not re.match(r'^\d{10,15}$', phone):
            raise serializers.ValidationError("Invalid phone number.")
        return phone

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric.")
        return value


class AuthTokenSerializer(serializers.Serializer):
    """Response serializer for JWT tokens."""
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    is_new_user = serializers.BooleanField(read_only=True)
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        return UserProfileSerializer(obj['user']).data


# ── User Profile ──────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    """User profile read/update serializer."""
    gym_name = serializers.CharField(source='gym.name', read_only=True, default=None)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = GymUser
        fields = [
            'id', 'phone', 'email', 'name', 'avatar',
            'gym', 'gym_name', 'role', 'role_display',
            'can_view_revenue', 'can_manage_members',
            'can_manage_leads', 'can_use_ai',
            'date_joined', 'last_login',
        ]
        read_only_fields = [
            'id', 'phone', 'role', 'date_joined', 'last_login',
            'can_view_revenue', 'can_manage_members',
            'can_manage_leads', 'can_use_ai',
        ]



class AccountListSerializer(serializers.ModelSerializer):
    """Serializer for list of accounts in multi-login scenario."""
    gym_name = serializers.CharField(source='gym.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = GymUser
        fields = ['id', 'name', 'gym_name', 'role_display', 'role']


class SelectAccountSerializer(serializers.Serializer):
    """Validate account selection token and user ID."""
    account_id = serializers.UUIDField()
    selection_token = serializers.CharField()


class OTPResponseSerializer(serializers.Serializer):
    """Response for send OTP."""
    success = serializers.BooleanField()
    message = serializers.CharField()


# ── Unified Login (Entity Code Based) ────────────────────────

class UnifiedLoginSerializer(serializers.Serializer):
    """Input serializer for entity code based login."""
    entity_code = serializers.CharField(
        max_length=10,
        help_text="Organization entity code (e.g., GYM7654321)"
    )
    username = serializers.CharField(
        max_length=150,
        help_text="User's username"
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="User's password"
    )

    def validate_entity_code(self, value):
        """Normalize entity code to uppercase."""
        return value.strip().upper()

    def validate_username(self, value):
        """Normalize username to lowercase."""
        return value.strip().lower()


class OrganizationSerializer(serializers.Serializer):
    """Organization details in login response."""
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    entity_code = serializers.CharField(read_only=True)
    owner_name = serializers.CharField(read_only=True)


class LocationSerializer(serializers.Serializer):
    """Location (Gym) details in login response."""
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    gym_code = serializers.CharField(read_only=True)


class UserLoginProfileSerializer(serializers.ModelSerializer):
    """Enhanced user profile for login response with organization and locations."""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    organization = serializers.SerializerMethodField()
    locations = serializers.SerializerMethodField()

    class Meta:
        model = GymUser
        fields = [
            'id', 'username', 'name', 'email', 'phone', 'avatar',
            'role', 'role_display', 'organization', 'locations',
            'can_view_revenue', 'can_manage_members',
            'can_manage_leads', 'can_use_ai',
        ]

    def get_organization(self, obj):
        """Get organization details."""
        if obj.organization:
            return OrganizationSerializer(obj.organization).data
        return None

    def get_locations(self, obj):
        """Get accessible locations."""
        # If user has specific locations assigned, return those
        if obj.locations.exists():
            return LocationSerializer(obj.locations.all(), many=True).data
        
        # If owner role and organization set, return all org locations
        if obj.role == 'owner' and obj.organization:
            all_locations = obj.organization.locations.filter(is_active=True)
            return LocationSerializer(all_locations, many=True).data
        
        # Otherwise return empty list
        return []


class PermissionsSerializer(serializers.Serializer):
    """User permissions summary."""
    can_view_all_locations = serializers.BooleanField()
    can_view_revenue = serializers.BooleanField()
    can_manage_members = serializers.BooleanField()
    can_manage_leads = serializers.BooleanField()
    can_use_ai = serializers.BooleanField()


class UnifiedLoginResponseSerializer(serializers.Serializer):
    """Response for successful unified login."""
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = UserLoginProfileSerializer(read_only=True)
    permissions = PermissionsSerializer(read_only=True)
