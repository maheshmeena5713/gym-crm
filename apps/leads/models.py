"""
Leads App - Lead Model
Lead management is the #1 selling point for gym owners.
"""

from django.db import models

from apps.core.models import BaseModel, ActiveManager


class Lead(BaseModel):
    """
    Potential gym members. AI-scored lead pipeline.
    Showing a gym owner 5 extra conversions/month = their ₹1,500 fee is a no-brainer.
    """

    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        related_name='leads',
        verbose_name="Gym",
    )

    # ── Contact ───────────────────────────────────────────────
    name = models.CharField(max_length=255, verbose_name="Name")
    phone = models.CharField(max_length=20, verbose_name="Phone")
    email = models.EmailField(null=True, blank=True, verbose_name="Email")

    # ── Lead Intel ────────────────────────────────────────────
    class Source(models.TextChoices):
        INSTAGRAM = 'instagram', 'Instagram'
        FACEBOOK = 'facebook', 'Facebook'
        GOOGLE = 'google', 'Google'
        WALKIN = 'walkin', 'Walk-in'
        REFERRAL = 'referral', 'Referral'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        JUSTDIAL = 'justdial', 'JustDial'
        WEBSITE = 'website', 'Website'
        SULEKHA = 'sulekha', 'Sulekha'
        OTHER = 'other', 'Other'

    source = models.CharField(
        max_length=50,
        choices=Source.choices,
        default=Source.WALKIN,
        verbose_name="Lead Source",
    )
    goal = models.CharField(
        max_length=50,
        verbose_name="Fitness Goal",
    )
    budget_range = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Budget Range",
        help_text="E.g., '2000-5000'",
    )
    preferred_time = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Preferred Time",
        help_text="E.g., 'morning', 'evening'",
    )

    # ── Lead Pipeline ─────────────────────────────────────────
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        CONTACTED = 'contacted', 'Contacted'
        INTERESTED = 'interested', 'Interested'
        TRIAL_BOOKED = 'trial_booked', 'Trial Booked'
        TRIAL_DONE = 'trial_done', 'Trial Completed'
        NEGOTIATING = 'negotiating', 'Negotiating'
        CONVERTED = 'converted', 'Converted'
        LOST = 'lost', 'Lost'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name="Status",
    )
    lost_reason = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Lost Reason",
        help_text="Why was this lead lost?",
    )

    # ── AI Scoring (the secret sauce) ─────────────────────────
    ai_score = models.IntegerField(
        default=0,
        verbose_name="AI Score",
        help_text="0-100, higher = more likely to convert",
    )
    ai_recommended_action = models.TextField(
        null=True,
        blank=True,
        verbose_name="AI Recommended Action",
        help_text="E.g., 'Call today, offer 10% off'",
    )
    ai_follow_up_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="AI Follow-up Date",
    )

    # ── Manual Tracking ───────────────────────────────────────
    last_contacted_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last Contacted",
    )
    next_followup_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Next Follow-up",
        help_text="Manual follow-up date set by staff",
    )
    trial_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Trial Date",
    )
    converted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Converted At",
    )

    # ── Assignment & Notes ────────────────────────────────────
    assigned_to = models.ForeignKey(
        'users.GymUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads',
        verbose_name="Assigned To",
    )
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name="Notes",
    )
    converted_member = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_lead',
        verbose_name="Converted Member",
        help_text="If converted, link to the Member record",
    )
    follow_up_count = models.IntegerField(
        default=0,
        verbose_name="Follow-up Count",
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'leads_lead'
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gym', 'status'], name='idx_lead_gym_status'),
            models.Index(fields=['gym', 'ai_score'], name='idx_lead_gym_score'),
            models.Index(fields=['gym', 'source'], name='idx_lead_gym_source'),
            models.Index(fields=['gym', 'created_at'], name='idx_lead_gym_created'),
            models.Index(fields=['gym', 'ai_follow_up_date'], name='idx_lead_gym_followup'),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()}) - Score: {self.ai_score}"
