"""
AI Engine App - AIUsageLog Model
Track every AI call per gym. Critical for cost control and billing.
"""

from django.db import models

from apps.core.models import BaseModel, ActiveManager


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
        db_table = 'ai_engine_aiusagelog'
        verbose_name = 'AI Usage Log'
        verbose_name_plural = 'AI Usage Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gym', 'feature', 'created_at'], name='idx_ai_gym_feat_date'),
            models.Index(fields=['gym', 'created_at'], name='idx_ai_gym_date'),
            models.Index(fields=['model_used'], name='idx_ai_model'),
        ]

    def __str__(self):
        return f"{self.gym.name} - {self.get_feature_display()} ({self.model_used})"

    def save(self, *args, **kwargs):
        self.total_tokens = self.prompt_tokens + self.completion_tokens
        super().save(*args, **kwargs)
