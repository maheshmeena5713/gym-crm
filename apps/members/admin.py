"""
Members Admin - Member & MembershipPlan with import/export.
"""

from django.contrib import admin
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.members.models import Member, MembershipPlan


# ── MembershipPlan ────────────────────────────────────────────

class MembershipPlanResource(resources.ModelResource):
    class Meta:
        model = MembershipPlan
        import_id_fields = ['id']
        fields = (
            'id', 'gym', 'name', 'duration_months', 'price',
            'includes_trainer', 'includes_diet_plan', 'includes_supplements',
            'is_active', 'created_at',
        )
        export_order = fields


@admin.register(MembershipPlan)
class MembershipPlanAdmin(ImportExportModelAdmin):
    resource_classes = [MembershipPlanResource]

    list_display = (
        'name', 'gym', 'duration_months', 'price',
        'includes_trainer', 'includes_diet_plan', 'is_active',
    )
    list_filter = ('gym', 'duration_months', 'includes_trainer', 'is_active')
    search_fields = ('name', 'gym__name', 'gym__gym_code')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 25


# ── Member ────────────────────────────────────────────────────

class MemberResource(resources.ModelResource):
    class Meta:
        model = Member
        import_id_fields = ['id']
        fields = (
            'id', 'gym', 'name', 'phone', 'email', 'gender',
            'goal', 'experience_level', 'dietary_preference',
            'height_cm', 'weight_kg', 'body_fat_pct', 'bmi',
            'membership_plan', 'join_date', 'membership_start',
            'membership_expiry', 'amount_paid', 'status',
            'assigned_trainer', 'attendance_streak', 'churn_risk_score',
            'created_at',
        )
        export_order = fields
        skip_unchanged = True


@admin.register(Member)
class MemberAdmin(ImportExportModelAdmin):
    resource_classes = [MemberResource]

    list_display = (
        'name', 'phone', 'gym', 'goal',
        'status_badge', 'membership_expiry',
        'attendance_streak', 'churn_risk_display',
    )
    list_filter = (
        'status', 'goal', 'experience_level', 'gender',
        'dietary_preference', 'gym',
    )
    search_fields = ('name', 'phone', 'email', 'gym__name', 'gym__gym_code')
    readonly_fields = (
        'id', 'bmi',
        'created_at', 'updated_at',
    )
    list_per_page = 25
    date_hierarchy = 'join_date'

    fieldsets = (
        ('Identity', {
            'fields': ('id', 'gym', 'name', 'phone', 'email', 'gender', 'date_of_birth', 'profile_photo'),
        }),
        ('Fitness Profile', {
            'fields': ('goal', 'experience_level', 'medical_conditions', 'dietary_preference'),
        }),
        ('Body Metrics', {
            'fields': ('height_cm', 'weight_kg', 'body_fat_pct', 'bmi'),
            'description': 'BMI is auto-calculated from height and weight.',
        }),
        ('Membership', {
            'fields': (
                'membership_plan', 'join_date', 'membership_start',
                'membership_expiry', 'amount_paid', 'status',
            ),
        }),
        ('Engagement', {
            'fields': (
                'assigned_trainer', 'attendance_streak',
                'last_check_in', 'churn_risk_score', 'emergency_contact',
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'is_deleted', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        colors = {
            'active': '#22c55e',
            'expired': '#ef4444',
            'frozen': '#3b82f6',
            'cancelled': '#94a3b8',
        }
        color = colors.get(obj.status, '#94a3b8')
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 10px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            color, obj.get_status_display(),
        )

    @admin.display(description='Churn Risk', ordering='churn_risk_score')
    def churn_risk_display(self, obj):
        score = obj.churn_risk_score or 0
        if score >= 60:
            color = '#ef4444'
        elif score >= 30:
            color = '#f59e0b'
        else:
            color = '#22c55e'
        return format_html(
            '<span style="color:{}; font-weight:600;">{}%</span>',
            color, score,
        )
