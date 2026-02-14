"""
Gyms App - Gym (Tenant) Model
The Gym is the customer who pays for the SaaS. Everything else belongs to a Gym.
"""

import random
import string

from django.db import models
from django.utils.text import slugify

from apps.core.models import BaseModel, ActiveManager


# Font choices for gym branding
FONT_CHOICES = [
    ('Inter', 'Inter'),
    ('Outfit', 'Outfit'),
    ('Poppins', 'Poppins'),
    ('Raleway', 'Raleway'),
    ('Nunito', 'Nunito'),
    ('Roboto', 'Roboto'),
]


class Gym(BaseModel):
    """
    The Gym is the tenant/customer of the SaaS platform.
    This is who subscribes and pays. All other data is gym-scoped.
    """

    # ── Tenant Identification ─────────────────────────────────
    gym_code = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        verbose_name="Gym Code",
        help_text="Auto-generated tenant ID (e.g. GYM4829156). Used for login.",
    )

    # ── Identity ──────────────────────────────────────────────
    name = models.CharField(
        max_length=255,
        verbose_name="Gym Name",
        help_text="Official gym/fitness center name",
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name="Slug",
        help_text="URL-safe identifier (e.g., for subdomain: mygym.gymai.in)",
    )
    logo = models.ImageField(
        upload_to='gym_logos/',
        null=True,
        blank=True,
        verbose_name="Logo",
        help_text="Gym logo image",
    )

    # ── Branding ──────────────────────────────────────────────
    logo_base64 = models.TextField(
        null=True,
        blank=True,
        verbose_name="Logo (Base64)",
        help_text="Base64-encoded logo image for fast rendering, no file storage needed",
    )
    brand_color = models.CharField(
        max_length=7,
        default='#6366f1',
        verbose_name="Brand Color",
        help_text="Primary hex color for the gym's dashboard theme",
    )
    font_family = models.CharField(
        max_length=30,
        choices=FONT_CHOICES,
        default='Inter',
        verbose_name="Font Family",
        help_text="Google Font used across the gym's dashboard",
    )

    # ── Owner Info ────────────────────────────────────────────
    owner_name = models.CharField(
        max_length=255,
        verbose_name="Owner Name",
    )
    owner_phone = models.CharField(
        max_length=20,
        verbose_name="Owner Phone",
        help_text="Primary contact number of the gym owner",
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Email",
        help_text="Primary email address (used for login and billing)",
    )

    # ── Location ──────────────────────────────────────────────
    address = models.TextField(
        blank=True,
        default='',
        verbose_name="Address",
        help_text="Full street address",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        default='',
        db_index=True,
        verbose_name="City",
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name="State",
    )
    pincode = models.CharField(
        max_length=10,
        blank=True,
        default='',
        verbose_name="PIN Code",
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Latitude",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Longitude",
    )

    # ── Business Info ─────────────────────────────────────────
    class GymType(models.TextChoices):
        STANDARD = 'standard', 'Standard Gym'
        CROSSFIT = 'crossfit', 'CrossFit Box'
        YOGA = 'yoga', 'Yoga Studio'
        MARTIAL_ARTS = 'martial_arts', 'Martial Arts'
        MULTI = 'multi', 'Multi-Sport'
        PERSONAL_TRAINING = 'personal_training', 'Personal Training Studio'

    gym_type = models.CharField(
        max_length=50,
        choices=GymType.choices,
        default=GymType.STANDARD,
        verbose_name="Gym Type",
    )
    member_capacity = models.IntegerField(
        default=100,
        verbose_name="Member Capacity",
        help_text="Maximum number of members the gym can handle",
    )
    monthly_revenue_range = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Monthly Revenue Range",
        help_text="Self-reported revenue range (for segmentation)",
    )

    # ── SaaS Subscription ─────────────────────────────────────
    class SubscriptionStatus(models.TextChoices):
        TRIAL = 'trial', 'Free Trial'
        ACTIVE = 'active', 'Active'
        PAST_DUE = 'past_due', 'Past Due'
        CHURNED = 'churned', 'Churned'
        CANCELLED = 'cancelled', 'Cancelled'

    subscription_plan = models.ForeignKey(
        'billing.SubscriptionPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gyms',
        verbose_name="Subscription Plan",
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIAL,
        db_index=True,
        verbose_name="Subscription Status",
    )
    trial_ends_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Trial End Date",
    )

    # ── Tracking ──────────────────────────────────────────────
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
    )
    onboarded_by = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Onboarded By",
        help_text="Sales rep or referral source who onboarded this gym",
    )
    referral_source = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Referral Source",
        help_text="How did this gym find us?",
    )

    # ── Managers ──────────────────────────────────────────────
    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'gyms_gym'
        verbose_name = 'Gym'
        verbose_name_plural = 'Gyms'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['city', 'is_active'], name='idx_gym_city_active'),
            models.Index(fields=['subscription_status'], name='idx_gym_sub_status'),
            models.Index(fields=['owner_phone'], name='idx_gym_owner_phone'),
            models.Index(fields=['gym_code'], name='idx_gym_code'),
        ]

    def __str__(self):
        return f"{self.name} ({self.city})"

    @staticmethod
    def _generate_gym_code():
        """Generate a unique gym code like GYM4829156."""
        while True:
            code = 'GYM' + ''.join(random.choices(string.digits, k=7))
            if not Gym.objects.filter(gym_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.gym_code:
            self.gym_code = self._generate_gym_code()
        if not self.slug:
            base_slug = slugify(self.name) or 'gym'
            slug = base_slug
            counter = 1
            while Gym.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def logo_data_uri(self):
        """Return the complete data:image URI for embedding in <img> tags."""
        if not self.logo_base64:
            return None
        # Auto-detect image format from base64 header
        if self.logo_base64.startswith('data:'):
            return self.logo_base64
        # Default to PNG if raw base64
        return f"data:image/png;base64,{self.logo_base64}"

