"""
AI Engine Admin - AIUsageLog with import/export.
"""

from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.ai_engine.models import AIUsageLog


class AIUsageLogResource(resources.ModelResource):
    class Meta:
        model = AIUsageLog
        import_id_fields = ['id']
        fields = (
            'id', 'gym', 'user', 'feature', 'model_used',
            'prompt_tokens', 'completion_tokens', 'total_tokens',
            'cost_usd', 'response_time_ms', 'was_cached',
            'was_successful', 'created_at',
        )
        export_order = fields


@admin.register(AIUsageLog)
class AIUsageLogAdmin(ImportExportModelAdmin):
    resource_classes = [AIUsageLogResource]

    list_display = (
        'gym', 'feature', 'model_used', 'total_tokens',
        'cost_usd', 'response_time_ms', 'was_successful', 'created_at',
    )
    list_filter = ('feature', 'model_used', 'was_successful', 'was_cached', 'gym')
    search_fields = ('gym__name', 'user__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 50
    date_hierarchy = 'created_at'
