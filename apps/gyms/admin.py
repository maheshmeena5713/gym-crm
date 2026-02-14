"""
Gyms Admin - Gym model with import/export.
"""

from django.contrib import admin
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.gyms.models import Gym


class GymResource(resources.ModelResource):
    """Import/Export resource for Gym model."""

    class Meta:
        model = Gym
        import_id_fields = ['id']
        fields = (
            'id', 'name', 'gym_code', 'slug', 'owner_name', 'owner_phone', 'email',
            'address', 'city', 'state', 'pincode', 'gym_type',
            'member_capacity', 'subscription_status', 'is_active',
            'onboarded_by', 'referral_source', 'created_at',
        )
        export_order = fields


@admin.register(Gym)
class GymAdmin(ImportExportModelAdmin):
    resource_classes = [GymResource]

    list_display = (
        'name', 'gym_code', 'city', 'owner_name', 'owner_phone',
        'subscription_plan', 'subscription_status_badge', 'is_active', 'created_at',
    )
    list_filter = (
        'subscription_status', 'gym_type', 'city', 'state',
        'is_active', 'is_deleted',
    )
    search_fields = ('name', 'gym_code', 'owner_name', 'owner_phone', 'email', 'city')
    readonly_fields = (
        'id', 'gym_code', 'slug',
        'created_at', 'updated_at',
    )
    list_per_page = 25

    fieldsets = (
        ('Identity', {
            'fields': ('id', 'name', 'gym_code', 'slug', 'logo'),
        }),
        ('Owner', {
            'fields': ('owner_name', 'owner_phone', 'email'),
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'pincode', 'latitude', 'longitude'),
        }),
        ('Business', {
            'fields': ('gym_type', 'member_capacity', 'monthly_revenue_range'),
        }),
        ('Subscription', {
            'fields': ('subscription_plan', 'subscription_status', 'trial_ends_at'),
        }),
        ('Branding', {
            'fields': ('brand_color', 'font_family'),
            'classes': ('collapse',),
        }),
        ('Tracking', {
            'fields': ('is_active', 'onboarded_by', 'referral_source'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'is_deleted', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Status', ordering='subscription_status')
    def subscription_status_badge(self, obj):
        colors = {
            'active': '#22c55e',
            'trial': '#6366f1',
            'expired': '#ef4444',
            'cancelled': '#94a3b8',
        }
        color = colors.get(obj.subscription_status, '#94a3b8')
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 10px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            color, obj.get_subscription_status_display(),
        )
