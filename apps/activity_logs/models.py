"""
Activity Logs App - Centralized Logging Models
Contains logs for WhatsApp, Emails, Progress, and AI Usage.
"""

from django.db import models

from apps.core.models import BaseModel, ActiveManager


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
        db_table = 'activity_logs_whatsappmessagelog'
        verbose_name = 'WhatsApp Message Log'
        verbose_name_plural = 'WhatsApp Message Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gym', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Log to {self.phone} ({self.status})"


class EmailMessageLog(BaseModel):
    """
    Detailed log of all emails sent out for tracking and auditing purposes.
    Similar to WhatsAppMessageLog but for emails (welcome, approval, generic notifications).
    """
    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        related_name='email_message_logs',
        verbose_name="Gym",
        null=True,
        blank=True,
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='email_message_logs',
        verbose_name="Member",
    )
    email = models.CharField(
        max_length=254,
        verbose_name="Email Address",
    )
    subject = models.CharField(
        max_length=300,
        verbose_name="Subject",
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
        verbose_name="API/SMTP Response",
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'activity_logs_emailmessagelog'
        verbose_name = 'Email Message Log'
        verbose_name_plural = 'Email Message Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gym', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Email to {self.email} ({self.status})"


class ProgressLog(BaseModel):
    """
    Body measurement history.
    Visual progress charts = member retention.
    """

    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        related_name='progress_logs',
        verbose_name="Gym",
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='progress_logs',
        verbose_name="Member",
    )
    recorded_by = models.ForeignKey(
        'users.GymUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_progress',
        verbose_name="Recorded By",
    )

    # ── Metrics ───────────────────────────────────────────────
    date = models.DateField(verbose_name="Date")
    weight_kg = models.FloatField(null=True, blank=True, verbose_name="Weight (kg)")
    body_fat_pct = models.FloatField(null=True, blank=True, verbose_name="Body Fat %")
    muscle_mass_kg = models.FloatField(null=True, blank=True, verbose_name="Muscle Mass (kg)")
    bmi = models.FloatField(null=True, blank=True, verbose_name="BMI")

    # ── Measurements (cm) ────────────────────────────────────
    chest_cm = models.FloatField(null=True, blank=True, verbose_name="Chest (cm)")
    waist_cm = models.FloatField(null=True, blank=True, verbose_name="Waist (cm)")
    hips_cm = models.FloatField(null=True, blank=True, verbose_name="Hips (cm)")
    biceps_cm = models.FloatField(null=True, blank=True, verbose_name="Biceps (cm)")
    thighs_cm = models.FloatField(null=True, blank=True, verbose_name="Thighs (cm)")

    # ── Progress Photos ───────────────────────────────────────
    front_photo = models.ImageField(
        upload_to='progress_photos/',
        null=True,
        blank=True,
        verbose_name="Front Photo",
    )
    side_photo = models.ImageField(
        upload_to='progress_photos/',
        null=True,
        blank=True,
        verbose_name="Side Photo",
    )
    back_photo = models.ImageField(
        upload_to='progress_photos/',
        null=True,
        blank=True,
        verbose_name="Back Photo",
    )
    notes = models.TextField(null=True, blank=True, verbose_name="Notes")

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'activity_logs_progresslog'
        verbose_name = 'Progress Log'
        verbose_name_plural = 'Progress Logs'
        ordering = ['-date']
        unique_together = ['member', 'date']
        indexes = [
            models.Index(fields=['gym', 'member', 'date'], name='idx_actprog_gym_member_date'),
        ]

    def __str__(self):
        return f"{self.member.name} - {self.date}"


class AIUsageLog(BaseModel):
    """
    Logs every AI API call per gym.
    Use gpt-4o-mini for 90% of tasks (₹0.01/query).
    Monthly AI cost per gym should be < ₹50.
    """

    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        related_name='ai_usage_logs',
        verbose_name="Gym",
    )
    user = models.ForeignKey(
        'users.GymUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_usage_logs',
        verbose_name="User",
    )

    # ── What Was Generated ────────────────────────────────────
    class Feature(models.TextChoices):
        WORKOUT_PLAN = 'workout_plan', 'Workout Plan'
        DIET_PLAN = 'diet_plan', 'Diet Plan'
        LEAD_SCORING = 'lead_scoring', 'Lead Scoring'
        INSTAGRAM_CONTENT = 'instagram_content', 'Instagram Content'
        WHATSAPP_REPLY = 'whatsapp_reply', 'WhatsApp Auto-Reply'
        CHURN_PREDICTION = 'churn_prediction', 'Churn Prediction'
        MEMBER_INSIGHT = 'member_insight', 'Member Insight'
        CONTENT_GENERATION = 'content_generation', 'Content Generation'

    feature = models.CharField(
        max_length=50,
        choices=Feature.choices,
        verbose_name="Feature",
    )

    # ── Cost Tracking ─────────────────────────────────────────
    model_used = models.CharField(
        max_length=50,
        default='gpt-4o-mini',
        verbose_name="AI Model Used",
    )
    prompt_tokens = models.IntegerField(default=0, verbose_name="Prompt Tokens")
    completion_tokens = models.IntegerField(default=0, verbose_name="Completion Tokens")
    total_tokens = models.IntegerField(default=0, verbose_name="Total Tokens")
    cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        verbose_name="Cost (USD)",
    )

    # ── Performance ───────────────────────────────────────────
    response_time_ms = models.IntegerField(
        default=0,
        verbose_name="Response Time (ms)",
    )
    was_cached = models.BooleanField(
        default=False,
        verbose_name="Was Cached",
    )
    was_successful = models.BooleanField(
        default=True,
        verbose_name="Was Successful",
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name="Error Message",
    )

    # ── Request/Response (for debugging) ──────────────────────
    prompt_summary = models.TextField(
        null=True,
        blank=True,
        verbose_name="Prompt Summary",
        help_text="Short summary of what was asked (not the full prompt for privacy)",
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'activity_logs_aiusagelog'
        verbose_name = 'AI Usage Log'
        verbose_name_plural = 'AI Usage Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gym', 'feature', 'created_at'], name='idx_actai_gym_feat_date'),
            models.Index(fields=['gym', 'created_at'], name='idx_actai_gym_date'),
            models.Index(fields=['model_used'], name='idx_actai_model'),
        ]

    def __str__(self):
        return f"{self.gym.name} - {self.get_feature_display()} ({self.model_used})"

    def save(self, *args, **kwargs):
        self.total_tokens = self.prompt_tokens + self.completion_tokens
        super().save(*args, **kwargs)
