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


class Quote(BaseModel):
    """
    Daily motivational quotes for members.
    """
    content = models.TextField(verbose_name="Quote Content")
    author = models.CharField(max_length=100, blank=True, null=True, verbose_name="Author")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    last_sent = models.DateField(null=True, blank=True, verbose_name="Last Sent Date")

    class Meta:
        db_table = 'communications_quote'
        verbose_name = 'Daily Quote'
        verbose_name_plural = 'Daily Quotes'

    def __str__(self):
        return f"{self.content[:50]}..."


class ContactQuery(BaseModel):
    """
    Contact form submissions from the website.
    Allows potential customers to reach out with questions.
    """
    # Contact information
    name = models.CharField(max_length=200, verbose_name="Full Name")
    email = models.EmailField(verbose_name="Email Address")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Phone Number")
    company = models.CharField(max_length=200, blank=True, verbose_name="Company Name")
    
    # Message details
    subject = models.CharField(max_length=300, verbose_name="Subject")
    message = models.TextField(verbose_name="Message")
    
    # Status tracking
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name="Status"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    
    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'contact_queries'
        verbose_name = 'Contact Query'
        verbose_name_plural = 'Contact Queries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at'], name='idx_contact_created'),
            models.Index(fields=['status'], name='idx_contact_status'),
            models.Index(fields=['email'], name='idx_contact_email'),
        ]

    def __str__(self):
        return f"{self.name} - {self.subject}"


class WhatsAppAutomation(BaseModel):
    """
    Automated WhatsApp messaging rules defined per Gym (Pro plan).
    """
    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        related_name='whatsapp_automations',
        verbose_name="Gym",
    )
    
    class AutomationType(models.TextChoices):
        EXPIRY_REMINDER = 'expiry_reminder', 'Membership Expiry Reminder'
        PAYMENT_PENDING = 'payment_pending', 'Payment Pending'
        INACTIVE_REMINDER = 'inactive_reminder', 'Inactive Member Reminder'
        BIRTHDAY = 'birthday', 'Birthday Wish'
        
    type = models.CharField(
        max_length=50,
        choices=AutomationType.choices,
        verbose_name="Automation Type"
    )
    enabled = models.BooleanField(
        default=False,
        verbose_name="Enabled"
    )
    days_before = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Days Before/After",
        help_text="e.g., 3 days before expiry"
    )
    template = models.TextField(
        verbose_name="Message Template",
        help_text="Supports variables like {{name}}, {{expiry_date}}, {{plan_name}}, {{gym_name}}"
    )
    last_run_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last Run At"
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'communications_whatsappautomation'
        verbose_name = 'WhatsApp Automation'
        verbose_name_plural = 'WhatsApp Automations'
        unique_together = ['gym', 'type']

    def __str__(self):
        return f"{self.gym.name} - {self.get_type_display()}"


class WhatsAppMessageLog(BaseModel):
    """
    Detailed log of all automated and manual broadcast messages sent via WhatsApp.
    This replaces/augments the base WhatsAppMessage for the automation flows.
    """
    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        related_name='whatsapp_message_logs',
        verbose_name="Gym",
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='whatsapp_message_logs',
        verbose_name="Member",
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Phone Number",
    )
    message = models.TextField(
        verbose_name="Message Content",
    )
    
    class DeliveryStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'

    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
        verbose_name="Status",
    )
    response = models.TextField(
        null=True,
        blank=True,
        verbose_name="API Response",
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'communications_whatsappmessagelog'
        verbose_name = 'WhatsApp Message Log'
        verbose_name_plural = 'WhatsApp Message Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gym', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Log to {self.phone} ({self.status})"
