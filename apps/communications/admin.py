"""
Communications Admin - WhatsAppMessage with import/export.
"""

from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.communications.models import WhatsAppMessage


class WhatsAppMessageResource(resources.ModelResource):
    class Meta:
        model = WhatsAppMessage
        import_id_fields = ['id']
        fields = (
            'id', 'gym', 'member', 'lead', 'direction',
            'message_type', 'recipient_phone', 'content',
            'template_name', 'wa_message_id', 'status',
            'cost_inr', 'created_at',
        )
        export_order = fields


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(ImportExportModelAdmin):
    resource_classes = [WhatsAppMessageResource]

    list_display = (
        'recipient_phone', 'gym', 'direction', 'message_type',
        'status', 'cost_inr', 'created_at',
    )
    list_filter = ('direction', 'message_type', 'status', 'gym')
    search_fields = ('recipient_phone', 'content', 'gym__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 50
    date_hierarchy = 'created_at'


from apps.communications.models import Quote

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('content', 'author', 'is_active', 'last_sent')
    list_filter = ('is_active',)
    search_fields = ('content', 'author')
