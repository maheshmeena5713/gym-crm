"""
Communications App - WhatsAppMessage Model
India runs on WhatsApp. If you're not on WhatsApp, you don't exist.
"""

from django.db import models

from apps.core.models import BaseModel, ActiveManager


class WhatsAppMessage(BaseModel):
    """
    WhatsApp message log via WATI/AiSensy Business API.
    Tracks all automated and manual messages sent to members/leads.
    """

    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        related_name='whatsapp_messages',
        verbose_name="Gym",
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='whatsapp_messages',
        verbose_name="Member",
    )
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='whatsapp_messages',
        verbose_name="Lead",
    )

    # ── Message Details ───────────────────────────────────────
    class Direction(models.TextChoices):
        INBOUND = 'inbound', 'Inbound'
        OUTBOUND = 'outbound', 'Outbound'

    direction = models.CharField(
        max_length=10,
        choices=Direction.choices,
        default=Direction.OUTBOUND,
        verbose_name="Direction",
    )

    class MessageType(models.TextChoices):
        PAYMENT_REMINDER = 'payment_reminder', 'Payment Reminder'
        WELCOME = 'welcome', 'Welcome Message'
        LEAD_FOLLOW_UP = 'lead_follow_up', 'Lead Follow-up'
        WORKOUT_SHARE = 'workout_share', 'Workout Plan Shared'
        DIET_SHARE = 'diet_share', 'Diet Plan Shared'
        BIRTHDAY = 'birthday', 'Birthday Wish'
        EXPIRY_REMINDER = 'expiry_reminder', 'Membership Expiry Reminder'
        ATTENDANCE_ALERT = 'attendance_alert', 'Missed Attendance Alert'
        PROMOTION = 'promotion', 'Promotional Message'
        CUSTOM = 'custom', 'Custom Message'

    message_type = models.CharField(
        max_length=30,
        choices=MessageType.choices,
        default=MessageType.CUSTOM,
        verbose_name="Message Type",
    )

    # ── Content ───────────────────────────────────────────────
    recipient_phone = models.CharField(
        max_length=20,
        verbose_name="Recipient Phone",
    )
    content = models.TextField(
        verbose_name="Message Content",
    )
    template_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Template Name",
        help_text="WhatsApp approved template name",
    )

    # ── WhatsApp API Response ─────────────────────────────────
    wa_message_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="WhatsApp Message ID",
    )

    class DeliveryStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        READ = 'read', 'Read'
        FAILED = 'failed', 'Failed'

    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
        verbose_name="Delivery Status",
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name="Error Message",
    )

    # ── Cost ──────────────────────────────────────────────────
    cost_inr = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0,
        verbose_name="Cost (₹)",
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'communications_whatsappmessage'
        verbose_name = 'WhatsApp Message'
        verbose_name_plural = 'WhatsApp Messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gym', 'message_type'], name='idx_wa_gym_type'),
            models.Index(fields=['gym', 'status'], name='idx_wa_gym_status'),
            models.Index(fields=['gym', 'created_at'], name='idx_wa_gym_date'),
            models.Index(fields=['recipient_phone'], name='idx_wa_phone'),
        ]

    def __str__(self):
        return f"{self.get_message_type_display()} → {self.recipient_phone} ({self.get_status_display()})"
