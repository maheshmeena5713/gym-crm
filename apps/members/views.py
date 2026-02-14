"""
Members Views - Member and MembershipPlan CRUD ViewSets.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.members.models import Member, MembershipPlan
from apps.members.serializers import (
    MemberSerializer,
    MemberListSerializer,
    MembershipPlanSerializer,
)
from apps.members.filters import MemberFilter
from apps.core.permissions import (
    IsGymStaff,
    CanManageMembers,
    GymScopedMixin,
)


@extend_schema_view(
    list=extend_schema(
        tags=['Members'],
        summary="List Members",
        description="Get all members in your gym. Trainers only see their assigned members.",
    ),
    create=extend_schema(
        tags=['Members'],
        summary="Add Member",
        description="Add a new member to your gym.",
    ),
    retrieve=extend_schema(
        tags=['Members'],
        summary="Get Member Details",
    ),
    update=extend_schema(
        tags=['Members'],
        summary="Update Member",
    ),
    partial_update=extend_schema(
        tags=['Members'],
        summary="Partial Update Member",
    ),
    destroy=extend_schema(
        tags=['Members'],
        summary="Delete Member (Soft)",
        description="Soft-delete a member. This marks them as deleted, not actually removed.",
    ),
)
class MemberViewSet(GymScopedMixin, viewsets.ModelViewSet):
    """
    Full CRUD for gym members.

    - **Owner/Manager**: sees all members in their gym
    - **Trainer**: sees only members assigned to them
    - **Search**: name, phone, email
    - **Filters**: status, goal, gender, experience, diet, expiry range, churn risk
    - **Ordering**: name, join_date, membership_expiry, churn_risk_score, created_at
    """

    queryset = Member.objects.select_related(
        'gym', 'membership_plan', 'assigned_trainer',
    ).filter(is_deleted=False)
    permission_classes = [IsAuthenticated, IsGymStaff, CanManageMembers]
    filterset_class = MemberFilter
    search_fields = ['name', 'phone', 'email']
    ordering_fields = [
        'name', 'join_date', 'membership_expiry',
        'churn_risk_score', 'attendance_streak', 'created_at',
    ]
    ordering = ['-created_at']

    # Trainer scoping: trainers only see assigned members
    trainer_scope_field = 'assigned_trainer'

    def get_serializer_class(self):
        if self.action == 'list':
            return MemberListSerializer
        return MemberSerializer

    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])

    @extend_schema(
        tags=['Members'],
        summary="Get Member Stats",
        description="Get aggregate stats for your gym members.",
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """GET /api/v1/members/stats/ — Aggregate member stats."""
        qs = self.get_queryset()
        total = qs.count()
        active = qs.filter(status='active').count()
        expired = qs.filter(status='expired').count()
        high_churn = qs.filter(churn_risk_score__gte=70).count()

        return Response({
            'total_members': total,
            'active': active,
            'expired': expired,
            'frozen': qs.filter(status='frozen').count(),
            'cancelled': qs.filter(status='cancelled').count(),
            'high_churn_risk': high_churn,
        })


@extend_schema_view(
    list=extend_schema(
        tags=['Membership Plans'],
        summary="List Plans",
        description="Get all membership plans for your gym.",
    ),
    create=extend_schema(
        tags=['Membership Plans'],
        summary="Create Plan",
    ),
    retrieve=extend_schema(
        tags=['Membership Plans'],
        summary="Get Plan Details",
    ),
    update=extend_schema(
        tags=['Membership Plans'],
        summary="Update Plan",
    ),
    partial_update=extend_schema(
        tags=['Membership Plans'],
        summary="Partial Update Plan",
    ),
    destroy=extend_schema(tags=['Membership Plans'], summary="Delete Plan"),
)
class MembershipPlanViewSet(GymScopedMixin, viewsets.ModelViewSet):
    """
    CRUD for gym membership plans.
    Only owners/managers can create/update plans.
    """

    queryset = MembershipPlan.objects.filter(is_deleted=False)
    serializer_class = MembershipPlanSerializer
    permission_classes = [IsAuthenticated, IsGymStaff]
    search_fields = ['name']
    ordering_fields = ['price', 'duration_months', 'created_at']
    ordering = ['price']
