"""
Members Filters - Django Filter for Member queryset.
"""

import django_filters

from apps.members.models import Member


class MemberFilter(django_filters.FilterSet):
    """
    Filter members by status, goal, gender, experience, dietary preference,
    membership expiry range, churn risk, and search.
    """

    # Exact match filters
    status = django_filters.ChoiceFilter(choices=Member.Status.choices)
    goal = django_filters.ChoiceFilter(choices=Member.Goal.choices)
    gender = django_filters.ChoiceFilter(choices=Member.Gender.choices)
    experience_level = django_filters.ChoiceFilter(
        choices=Member.ExperienceLevel.choices,
    )
    dietary_preference = django_filters.ChoiceFilter(
        choices=Member.DietaryPreference.choices,
    )

    # Date range filters
    membership_expiry_after = django_filters.DateFilter(
        field_name='membership_expiry',
        lookup_expr='gte',
        label='Expiry After',
    )
    membership_expiry_before = django_filters.DateFilter(
        field_name='membership_expiry',
        lookup_expr='lte',
        label='Expiry Before',
    )
    joined_after = django_filters.DateFilter(
        field_name='join_date',
        lookup_expr='gte',
        label='Joined After',
    )
    joined_before = django_filters.DateFilter(
        field_name='join_date',
        lookup_expr='lte',
        label='Joined Before',
    )

    # Numeric range filters
    churn_risk_min = django_filters.NumberFilter(
        field_name='churn_risk_score',
        lookup_expr='gte',
        label='Min Churn Risk',
    )
    churn_risk_max = django_filters.NumberFilter(
        field_name='churn_risk_score',
        lookup_expr='lte',
        label='Max Churn Risk',
    )

    # Relationship filters
    assigned_trainer = django_filters.UUIDFilter(field_name='assigned_trainer__id')
    membership_plan = django_filters.UUIDFilter(field_name='membership_plan__id')

    class Meta:
        model = Member
        fields = [
            'status', 'goal', 'gender', 'experience_level',
            'dietary_preference', 'assigned_trainer', 'membership_plan',
        ]
