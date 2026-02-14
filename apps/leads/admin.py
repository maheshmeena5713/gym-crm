"""
Leads Admin - Lead model with import/export.
"""

from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.leads.models import Lead


class LeadResource(resources.ModelResource):
    class Meta:
        model = Lead
        import_id_fields = ['id']
        fields = (
            'id', 'gym', 'name', 'phone', 'email', 'source', 'goal',
            'budget_range', 'preferred_time', 'status', 'lost_reason',
            'ai_score', 'ai_recommended_action', 'ai_follow_up_date',
            'assigned_to', 'notes', 'follow_up_count', 'created_at',
        )
        export_order = fields
        skip_unchanged = True


@admin.register(Lead)
class LeadAdmin(ImportExportModelAdmin):
    resource_classes = [LeadResource]

    list_display = (
        'name', 'phone', 'gym', 'source', 'status',
        'ai_score', 'assigned_to', 'follow_up_count', 'created_at',
    )
    list_filter = ('status', 'source', 'gym', 'ai_score')
    search_fields = ('name', 'phone', 'email', 'gym__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Contact', {
            'fields': ('id', 'gym', 'name', 'phone', 'email'),
        }),
        ('Lead Intel', {
            'fields': ('source', 'goal', 'budget_range', 'preferred_time'),
        }),
        ('Pipeline', {
            'fields': ('status', 'lost_reason', 'assigned_to', 'notes', 'follow_up_count'),
        }),
        ('AI Scoring', {
            'fields': ('ai_score', 'ai_recommended_action', 'ai_follow_up_date'),
        }),
        ('Conversion', {
            'fields': ('converted_member',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'is_deleted', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )
