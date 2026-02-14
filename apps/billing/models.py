"""
Billing App - SubscriptionPlan, GymSubscription, Payment
This is how the SaaS makes money. Razorpay integration.
"""

from django.db import models

from apps.core.models import BaseModel, ActiveManager


class SubscriptionPlan(BaseModel):
    """
    SaaS pricing tiers (Starter, Pro, Enterprise).
    Feature flags on this model control what each gym can access.
    """

    name = models.CharField(
        max_length=100,
        verbose_name="Plan Name",
        help_text="E.g., 'Starter', 'Pro', 'Enterprise'",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="Slug",
    )

    # ── Pricing ───────────────────────────────────────────────
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monthly Price (₹)",
    )
    price_yearly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Yearly Price (₹)",
    )
    discount_pct = models.IntegerField(
        default=0,
        verbose_name="Yearly Discount %",
    )

    # ── Usage Limits (drive upgrades) ─────────────────────────
    max_members = models.IntegerField(default=100, verbose_name="Max Members")
    max_ai_queries_per_month = models.IntegerField(default=100, verbose_name="Max AI Queries/Month")
    max_staff_accounts = models.IntegerField(default=3, verbose_name="Max Staff Accounts")
    max_leads = models.IntegerField(default=50, verbose_name="Max Leads")

    # ── Feature Flags ─────────────────────────────────────────
    has_lead_management = models.BooleanField(default=False, verbose_name="Lead Management")
    has_ai_workout = models.BooleanField(default=True, verbose_name="AI Workout Plans")
    has_ai_diet = models.BooleanField(default=False, verbose_name="AI Diet Plans")
    has_ai_lead_scoring = models.BooleanField(default=False, verbose_name="AI Lead Scoring")
    has_whatsapp_integration = models.BooleanField(default=False, verbose_name="WhatsApp Integration")
    has_instagram_content = models.BooleanField(default=False, verbose_name="Instagram Content AI")
    has_analytics_dashboard = models.BooleanField(default=False, verbose_name="Analytics Dashboard")
    has_white_label = models.BooleanField(default=False, verbose_name="White Label")
    has_api_access = models.BooleanField(default=False, verbose_name="API Access")

    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    display_order = models.IntegerField(default=0, verbose_name="Display Order")

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'billing_subscriptionplan'
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'
        ordering = ['display_order', 'price_monthly']

    def __str__(self):
        return f"{self.name} - ₹{self.price_monthly}/mo"


class GymSubscription(BaseModel):
    """
    Active subscription for each gym. Your revenue backbone.
    Links gym to their plan and Razorpay billing.
    """

    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name="Gym",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name="Plan",
    )

    # ── Billing Cycle ─────────────────────────────────────────
    class BillingCycle(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        YEARLY = 'yearly', 'Yearly'

    billing_cycle = models.CharField(
        max_length=10,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
        verbose_name="Billing Cycle",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Amount (₹)",
    )

    # ── Razorpay ──────────────────────────────────────────────
    razorpay_subscription_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Razorpay Subscription ID",
    )
    razorpay_customer_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Razorpay Customer ID",
    )

    # ── Status ────────────────────────────────────────────────
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PAST_DUE = 'past_due', 'Past Due'
        CANCELLED = 'cancelled', 'Cancelled'
        PAUSED = 'paused', 'Paused'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Status",
    )
    current_period_start = models.DateTimeField(verbose_name="Current Period Start")
    current_period_end = models.DateTimeField(verbose_name="Current Period End")
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="Cancelled At")

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'billing_gymsubscription'
        verbose_name = 'Gym Subscription'
        verbose_name_plural = 'Gym Subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gym', 'status'], name='idx_gsub_gym_status'),
            models.Index(fields=['status', 'current_period_end'], name='idx_gsub_status_end'),
        ]

    def __str__(self):
        return f"{self.gym.name} - {self.plan.name} ({self.get_status_display()})"


class Payment(BaseModel):
    """
    Individual payment records. Required for GST compliance in India.
    """

    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="Gym",
    )
    subscription = models.ForeignKey(
        GymSubscription,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="Subscription",
    )

    # ── Razorpay ──────────────────────────────────────────────
    razorpay_payment_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Razorpay Payment ID",
    )
    razorpay_order_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Razorpay Order ID",
    )
    razorpay_signature = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Razorpay Signature",
    )

    # ── Payment Details ───────────────────────────────────────
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Amount (₹)",
    )
    currency = models.CharField(
        max_length=3,
        default='INR',
        verbose_name="Currency",
    )

    class PaymentStatus(models.TextChoices):
        CAPTURED = 'captured', 'Captured'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'
        PENDING = 'pending', 'Pending'

    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="Status",
    )
    payment_method = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Payment Method",
        help_text="E.g., upi, card, netbanking",
    )

    # ── Invoice / GST ─────────────────────────────────────────
    invoice_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        unique=True,
        verbose_name="Invoice Number",
    )
    gst_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="GST Amount (₹)",
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Paid At",
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'billing_payment'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gym', 'status'], name='idx_pay_gym_status'),
            models.Index(fields=['paid_at'], name='idx_pay_paid_at'),
        ]

    def __str__(self):
        return f"{self.gym.name} - ₹{self.amount} ({self.get_status_display()})"
