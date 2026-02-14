"""
Members Serializers - Member and MembershipPlan CRUD.
"""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from apps.members.models import Member, MembershipPlan


class MembershipPlanSerializer(serializers.ModelSerializer):
    """Full serializer for MembershipPlan CRUD."""

    class Meta:
        model = MembershipPlan
        fields = [
            'id', 'name', 'duration_months', 'price',
            'includes_trainer', 'includes_diet_plan', 'includes_supplements',
            'description', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MemberListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for member list views."""
    membership_plan_name = serializers.CharField(
        source='membership_plan.name', read_only=True, default=None,
    )
    assigned_trainer_name = serializers.CharField(
        source='assigned_trainer.name', read_only=True, default=None,
    )
    goal_display = serializers.CharField(source='get_goal_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Member
        fields = [
            'id', 'name', 'phone', 'gender', 'goal', 'goal_display',
            'status', 'status_display', 'experience_level',
            'membership_plan', 'membership_plan_name',
            'membership_expiry', 'assigned_trainer', 'assigned_trainer_name',
            'attendance_streak', 'churn_risk_score',
            'weight_kg', 'created_at',
        ]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Create Member',
            value={
                'name': 'Raj Patel',
                'phone': '9876543210',
                'gender': 'male',
                'goal': 'muscle_gain',
                'experience_level': 'beginner',
                'dietary_preference': 'veg',
                'height_cm': 175,
                'weight_kg': 72,
                'join_date': '2026-02-13',
                'membership_start': '2026-02-13',
                'membership_expiry': '2026-05-13',
                'amount_paid': 5000,
            },
            request_only=True,
        ),
    ]
)
class MemberSerializer(serializers.ModelSerializer):
    """Full serializer for Member CRUD."""
    membership_plan_name = serializers.CharField(
        source='membership_plan.name', read_only=True, default=None,
    )
    assigned_trainer_name = serializers.CharField(
        source='assigned_trainer.name', read_only=True, default=None,
    )
    goal_display = serializers.CharField(source='get_goal_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    experience_display = serializers.CharField(
        source='get_experience_level_display', read_only=True,
    )
    diet_display = serializers.CharField(
        source='get_dietary_preference_display', read_only=True,
    )

    class Meta:
        model = Member
        fields = [
            'id', 'name', 'phone', 'email', 'gender', 'date_of_birth',
            'profile_photo',
            # Fitness
            'goal', 'goal_display', 'experience_level', 'experience_display',
            'medical_conditions', 'dietary_preference', 'diet_display',
            # Body
            'height_cm', 'weight_kg', 'body_fat_pct', 'bmi',
            # Membership
            'membership_plan', 'membership_plan_name',
            'join_date', 'membership_start', 'membership_expiry',
            'amount_paid', 'status', 'status_display',
            # Engagement
            'assigned_trainer', 'assigned_trainer_name',
            'attendance_streak', 'last_check_in', 'churn_risk_score',
            'emergency_contact',
            # Timestamps
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'attendance_streak', 'last_check_in',
            'churn_risk_score', 'bmi', 'created_at', 'updated_at',
        ]

    def validate_phone(self, value):
        """Ensure phone is unique within the gym."""
        gym = self.context['request'].user.gym
        qs = Member.objects.filter(gym=gym, phone=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A member with this phone number already exists in your gym."
            )
        return value
