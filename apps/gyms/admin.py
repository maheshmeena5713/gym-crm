"""
Gyms Admin - Gym model with import/export.
"""

from datetime import timedelta
from django.utils import timezone
from django.contrib import admin, messages
from django.utils.html import format_html
from django.core.mail import send_mail
from django.conf import settings
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.gyms.models import Gym, GymRegistrationRequest
from apps.users.models import GymUser
from apps.billing.models import SubscriptionPlan
from apps.communications.services import WhatsAppService
from apps.communications.models import EmailMessageLog


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


@admin.register(GymRegistrationRequest)
class GymRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ('gym_name', 'owner_name', 'email', 'phone', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('gym_name', 'owner_name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_requests', 'reject_requests']

    def _process_approval(self, request, req):
        """Helper to process a single valid approval."""
        if req.status != GymRegistrationRequest.StatusChoices.PENDING:
            return False
            
        wa_service = WhatsAppService()

        # Get plan
        plan = SubscriptionPlan.objects.filter(slug=req.plan_slug).first()
        if not plan:
            plan = SubscriptionPlan.objects.filter(slug='starter').first()
        
        # Create Gym
        gym = Gym.objects.create(
            name=req.gym_name,
            owner_name=req.owner_name,
            owner_phone=req.phone,
            email=req.email,
            city=req.city,
            subscription_plan=plan,
            subscription_status=Gym.SubscriptionStatus.TRIAL,
            trial_ends_at=timezone.now() + timedelta(days=30),
            is_active=True,
        )
        
        # Create User
        user = GymUser.objects.create(
            gym=gym,
            name=req.owner_name,
            email=req.email,
            username=req.username,
            phone=req.phone,
            role=GymUser.Role.OWNER,
            can_view_revenue=True,
            can_manage_members=True,
            can_manage_leads=True,
            can_use_ai=True,
        )
        user.password = req.password_hash
        user.save()

        # Mark as approved
        req.status = GymRegistrationRequest.StatusChoices.APPROVED
        req.save()

        # Trigger email
        try:
            login_url = request.build_absolute_uri('/login/')
            subject = "Your Gym Registration is Approved"
            msg_content = f"Hi {req.owner_name},\\n\\nYour registration for {req.gym_name} has been approved.\\nYou can login at {login_url} using your username '{req.username}'.\\n\\nThanks,\\nGym Team"
            
            # create log
            email_log = EmailMessageLog.objects.create(
                gym=gym,
                email=req.email,
                subject=subject,
                message=msg_content,
                status=EmailMessageLog.DeliveryStatus.PENDING
            )
            
            send_mail(
                subject=subject,
                message=msg_content,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gym.com'),
                recipient_list=[req.email],
                fail_silently=False,
            )
            
            # update log success
            email_log.status = EmailMessageLog.DeliveryStatus.SENT
            email_log.response = "OK"
            email_log.save()
            
        except Exception as e:
            if 'email_log' in locals():
                email_log.status = EmailMessageLog.DeliveryStatus.FAILED
                email_log.response = str(e)
                email_log.save()

        # Trigger WhatsApp
        wa_service.send_whatsapp_message(
            phone=req.phone,
            message=f"Hi {req.owner_name}, your registration for {req.gym_name} has been approved! You can now login to your dashboard.",
            gym=gym,
        )
        return True

    @admin.action(description="Approve selected registration requests")
    def approve_requests(self, request, queryset):
        pending_requests = queryset.filter(status=GymRegistrationRequest.StatusChoices.PENDING)
        approved_count = 0

        for req in pending_requests:
            if self._process_approval(request, req):
                approved_count += 1

        self.message_user(request, f"Successfully approved {approved_count} requests.", messages.SUCCESS)

    @admin.action(description="Reject selected registration requests")
    def reject_requests(self, request, queryset):
        updated = queryset.filter(status=GymRegistrationRequest.StatusChoices.PENDING).update(
            status=GymRegistrationRequest.StatusChoices.REJECTED
        )
        self.message_user(request, f"Rejected {updated} requests.", messages.WARNING)

    def save_model(self, request, obj, form, change):
        """Intercept manual saves in the admin form."""
        if change:
            # Check if status was changed to APPROVED from PENDING
            if 'status' in form.changed_data and obj.status == GymRegistrationRequest.StatusChoices.APPROVED:
                # Temporarily revert status to process the approval helper (which expects PENDING)
                obj.status = GymRegistrationRequest.StatusChoices.PENDING
                success = self._process_approval(request, obj)
                if not success:
                    # If it somehow fails or isn't actually pending, set it back
                    obj.status = GymRegistrationRequest.StatusChoices.APPROVED
                    super().save_model(request, obj, form, change)
                return  # _process_approval calls the save() already
                
        super().save_model(request, obj, form, change)
