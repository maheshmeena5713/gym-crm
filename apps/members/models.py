"""
Members App - Member & MembershipPlan Models
Gym members and the membership plans gyms sell.
"""

from django.db import models

from apps.core.models import BaseModel, ActiveManager


class MembershipPlan(BaseModel):
    """
    Plans that the GYM sells to THEIR members.
    (Not SaaS pricing — this is the gym's own product.)
    """

    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        related_name='membership_plans',
        verbose_name="Gym",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Plan Name",
        help_text="E.g., '3 Month Basic', 'Annual Premium'",
    )
    duration_months = models.IntegerField(
        verbose_name="Duration (Months)",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Price (₹)",
    )
    includes_trainer = models.BooleanField(
        default=False,
        verbose_name="Includes Personal Trainer",
    )
    includes_diet_plan = models.BooleanField(
        default=False,
        verbose_name="Includes Diet Plan",
    )
    includes_supplements = models.BooleanField(
        default=False,
        verbose_name="Includes Supplements",
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Description",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'members_membershipplan'
        verbose_name = 'Membership Plan'
        verbose_name_plural = 'Membership Plans'
        ordering = ['gym', 'price']
        indexes = [
            models.Index(fields=['gym', 'is_active'], name='idx_mplan_gym_active'),
        ]

    def __str__(self):
        return f"{self.name} - ₹{self.price} ({self.duration_months}mo)"


class Member(BaseModel):
    """
    Gym members — the gym owner's most valuable data.
    Churn prediction and expiry tracking drive the AI value.
    """

    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name="Gym",
    )

    # ── Identity ──────────────────────────────────────────────
    name = models.CharField(
        max_length=255,
        verbose_name="Full Name",
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Phone Number",
    )
    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name="Email",
    )

    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        null=True,
        blank=True,
        verbose_name="Gender",
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date of Birth",
    )
    profile_photo = models.ImageField(
        upload_to='member_photos/',
        null=True,
        blank=True,
        verbose_name="Profile Photo",
    )

    # ── Fitness Profile (AI uses this) ────────────────────────
    class Goal(models.TextChoices):
        FAT_LOSS = 'fat_loss', 'Fat Loss'
        MUSCLE_GAIN = 'muscle_gain', 'Muscle Gain'
        GENERAL_FITNESS = 'general_fitness', 'General Fitness'
        SPORTS = 'sports', 'Sports Performance'
        REHAB = 'rehab', 'Rehabilitation'
        STRENGTH = 'strength', 'Strength Training'
        FLEXIBILITY = 'flexibility', 'Flexibility & Mobility'

    goal = models.CharField(
        max_length=50,
        choices=Goal.choices,
        default=Goal.GENERAL_FITNESS,
        verbose_name="Fitness Goal",
    )

    class ExperienceLevel(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    experience_level = models.CharField(
        max_length=20,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.BEGINNER,
        verbose_name="Experience Level",
    )
    medical_conditions = models.TextField(
        null=True,
        blank=True,
        verbose_name="Medical Conditions",
        help_text="AI will factor these into workout/diet plans",
    )

    class DietaryPreference(models.TextChoices):
        VEG = 'veg', 'Vegetarian'
        NON_VEG = 'non_veg', 'Non-Vegetarian'
        VEGAN = 'vegan', 'Vegan'
        EGGETARIAN = 'eggetarian', 'Eggetarian'
        JAIN = 'jain', 'Jain'

    dietary_preference = models.CharField(
        max_length=30,
        choices=DietaryPreference.choices,
        default=DietaryPreference.VEG,
        verbose_name="Dietary Preference",
    )

    # ── Body Metrics (latest snapshot) ────────────────────────
    height_cm = models.FloatField(null=True, blank=True, verbose_name="Height (cm)")
    weight_kg = models.FloatField(null=True, blank=True, verbose_name="Weight (kg)")
    body_fat_pct = models.FloatField(null=True, blank=True, verbose_name="Body Fat %")
    bmi = models.FloatField(null=True, blank=True, verbose_name="BMI")

    # ── Membership ────────────────────────────────────────────
    membership_plan = models.ForeignKey(
        MembershipPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        verbose_name="Membership Plan",
    )
    join_date = models.DateField(verbose_name="Join Date")
    membership_start = models.DateField(verbose_name="Membership Start Date")
    membership_expiry = models.DateField(verbose_name="Membership Expiry Date")
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Amount Paid (₹)",
    )

    # ── Engagement Tracking ───────────────────────────────────
    assigned_trainer = models.ForeignKey(
        'users.GymUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_members',
        verbose_name="Assigned Trainer",
    )
    attendance_streak = models.IntegerField(
        default=0,
        verbose_name="Attendance Streak",
        help_text="Consecutive days of gym visits",
    )
    last_check_in = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last Check-in",
    )
    churn_risk_score = models.IntegerField(
        default=0,
        verbose_name="Churn Risk Score",
        help_text="AI-predicted score: 0 (safe) to 100 (high risk)",
    )

    # ── Status ────────────────────────────────────────────────
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        EXPIRED = 'expired', 'Expired'
        FROZEN = 'frozen', 'Frozen'
        CANCELLED = 'cancelled', 'Cancelled'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Status",
    )
    emergency_contact = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Emergency Contact",
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'members_member'
        verbose_name = 'Member'
        verbose_name_plural = 'Members'
        ordering = ['-created_at']
        unique_together = ['gym', 'phone']
        indexes = [
            models.Index(fields=['gym', 'status'], name='idx_member_gym_status'),
            models.Index(fields=['gym', 'membership_expiry'], name='idx_member_gym_expiry'),
            models.Index(fields=['gym', 'churn_risk_score'], name='idx_member_gym_churn'),
            models.Index(fields=['gym', 'phone'], name='idx_member_gym_phone'),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone})"
