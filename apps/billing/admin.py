"""
Billing Admin - SubscriptionPlan, GymSubscription, Payment with import/export.
"""

from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.billing.models import SubscriptionPlan, GymSubscription, Payment


# ── SubscriptionPlan ──────────────────────────────────────────

class SubscriptionPlanResource(resources.ModelResource):
    class Meta:
        model = SubscriptionPlan
        import_id_fields = ['id']
        fields = (
            'id', 'name', 'slug', 'price_monthly', 'price_yearly',
            'discount_pct', 'max_members', 'max_ai_queries_per_month',
            'max_staff_accounts', 'max_leads',
            'has_lead_management', 'has_ai_workout', 'has_ai_diet',
            'has_ai_lead_scoring', 'has_whatsapp_integration',
            'has_instagram_content', 'has_analytics_dashboard',
            'has_white_label', 'has_api_access',
            'is_active', 'display_order', 'created_at',
        )
        export_order = fields


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(ImportExportModelAdmin):
    resource_classes = [SubscriptionPlanResource]

    list_display = (
        'name', 'price_monthly', 'price_yearly', 'max_members',
        'max_ai_queries_per_month', 'is_active', 'display_order',
    )
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 10

    fieldsets = (
        ('Plan', {
            'fields': ('id', 'name', 'slug', 'display_order'),
        }),
        ('Pricing', {
            'fields': ('price_monthly', 'price_yearly', 'discount_pct'),
        }),
        ('Limits', {
            'fields': ('max_members', 'max_ai_queries_per_month', 'max_staff_accounts', 'max_leads'),
        }),
        ('Features', {
            'fields': (
                'has_lead_management', 'has_ai_workout', 'has_ai_diet',
                'has_ai_lead_scoring', 'has_whatsapp_integration',
                'has_instagram_content', 'has_analytics_dashboard',
                'has_white_label', 'has_api_access',
            ),
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# ── GymSubscription ──────────────────────────────────────────

class GymSubscriptionResource(resources.ModelResource):
    class Meta:
        model = GymSubscription
        import_id_fields = ['id']
        fields = (
            'id', 'gym', 'plan', 'billing_cycle', 'amount',
            'razorpay_subscription_id', 'status',
            'current_period_start', 'current_period_end',
            'cancelled_at', 'created_at',
        )
        export_order = fields


@admin.register(GymSubscription)
class GymSubscriptionAdmin(ImportExportModelAdmin):
    resource_classes = [GymSubscriptionResource]

    list_display = (
        'gym', 'plan', 'billing_cycle', 'amount',
        'status', 'current_period_end', 'created_at',
    )
    list_filter = ('status', 'billing_cycle', 'plan')
    search_fields = ('gym__name', 'razorpay_subscription_id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 25


# ── Payment ───────────────────────────────────────────────────

class PaymentResource(resources.ModelResource):
    class Meta:
        model = Payment
        import_id_fields = ['id']
        fields = (
            'id', 'gym', 'subscription', 'razorpay_payment_id',
            'razorpay_order_id', 'amount', 'currency', 'status',
            'payment_method', 'invoice_number', 'gst_amount',
            'paid_at', 'created_at',
        )
        export_order = fields


@admin.register(Payment)
class PaymentAdmin(ImportExportModelAdmin):
    resource_classes = [PaymentResource]

    list_display = (
        'gym', 'amount', 'currency', 'status',
        'payment_method', 'invoice_number', 'paid_at',
    )
    list_filter = ('status', 'payment_method', 'currency')
    search_fields = (
        'gym__name', 'razorpay_payment_id',
        'razorpay_order_id', 'invoice_number',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 25
    date_hierarchy = 'paid_at'
