"""
Users Admin - GymUser and OTPSession with import/export.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.users.models import GymUser, OTPSession


class GymUserResource(resources.ModelResource):
    """Import/Export resource for GymUser model."""

    class Meta:
        model = GymUser
        import_id_fields = ['id']
        fields = (
            'id', 'gym', 'phone', 'email', 'name', 'role',
            'can_view_revenue', 'can_manage_members', 'can_manage_leads',
            'can_use_ai', 'is_active', 'is_staff', 'date_joined',
        )
        export_order = fields
        skip_unchanged = True


@admin.register(GymUser)
class GymUserAdmin(ImportExportModelAdmin, BaseUserAdmin):
    resource_classes = [GymUserResource]

    list_display = (
        'name', 'phone', 'gym', 'gym_code_display', 'email', 'username',
        'role_badge', 'is_active', 'last_login', 'created_at',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'gym')
    search_fields = ('name', 'phone', 'email', 'gym__gym_code', 'gym__name')
    readonly_fields = (
        'id', 'phone',
        'created_at', 'updated_at', 'last_login', 'date_joined',
    )
    list_per_page = 25
    ordering = ('-created_at',)

    fieldsets = (
        ('Identity', {
            'fields': ('id', 'phone', 'name', 'email', 'username', 'avatar'),
        }),
        ('Gym & Role', {
            'fields': ('gym', 'role'),
        }),
        ('Permissions', {
            'fields': (
                'can_view_revenue', 'can_manage_members',
                'can_manage_leads', 'can_use_ai',
            ),
        }),
        ('Django Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('date_joined', 'last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'name', 'password1', 'password2', 'gym', 'role'),
        }),
    )

    filter_horizontal = ('groups', 'user_permissions',)

    @admin.display(description='Gym Code', ordering='gym__gym_code')
    def gym_code_display(self, obj):
        if obj.gym:
            return obj.gym.gym_code
        return '-'

    @admin.display(description='Role', ordering='role')
    def role_badge(self, obj):
        colors = {
            'owner': '#6366f1',
            'manager': '#8b5cf6',
            'trainer': '#22c55e',
            'receptionist': '#f59e0b',
            'staff': '#94a3b8',
        }
        color = colors.get(obj.role, '#94a3b8')
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 10px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            color, obj.get_role_display(),
        )


# ── OTPSession Admin ──────────────────────────────────────────

class OTPSessionResource(resources.ModelResource):
    class Meta:
        model = OTPSession
        import_id_fields = ['id']
        fields = (
            'id', 'phone', 'otp_code', 'is_verified',
            'attempts', 'expires_at', 'created_at',
        )
        export_order = fields


@admin.register(OTPSession)
class OTPSessionAdmin(ImportExportModelAdmin):
    resource_classes = [OTPSessionResource]

    list_display = (
        'phone', 'otp_code', 'is_verified', 'attempts',
        'expires_at', 'created_at',
    )
    list_filter = ('is_verified',)
    search_fields = ('phone',)
    readonly_fields = ('id', 'phone', 'otp_code', 'is_verified', 'attempts', 'expires_at', 'created_at')
    list_per_page = 50
    date_hierarchy = 'created_at'
