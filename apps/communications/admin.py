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


from apps.communications.models import ContactQuery

@admin.register(ContactQuery)
class ContactQueryAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'email', 'subject', 'status', 
        'created_at', 'company'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'phone', 'company', 'subject', 'message')
    readonly_fields = ('id', 'created_at', 'updated_at', 'ip_address', 'user_agent')
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'company')
        }),
        ('Message', {
            'fields': ('subject', 'message')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_in_progress', 'mark_as_resolved', 'mark_as_closed']
    
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} queries marked as in progress.')
    mark_as_in_progress.short_description = "Mark as in progress"
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status='resolved')
        self.message_user(request, f'{updated} queries marked as resolved.')
    mark_as_resolved.short_description = "Mark as resolved"
    
    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status='closed')
        self.message_user(request, f'{updated} queries marked as closed.')
    mark_as_closed.short_description = "Mark as closed"
