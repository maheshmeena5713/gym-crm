"""
Fitness App - WorkoutPlan, DietPlan, Attendance, ProgressLog
AI-generated plans + tracking = the core product value.
"""

from django.db import models

from apps.core.models import BaseModel, ActiveManager


class WorkoutPlan(BaseModel):
    """
    AI-generated workout plans. Stored as structured JSON.
    Replaces expensive personal trainer plan creation.
    """

    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        related_name='workout_plans',
        verbose_name="Gym",
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='workout_plans',
        verbose_name="Member",
    )
    created_by = models.ForeignKey(
        'users.GymUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_workout_plans',
        verbose_name="Created By",
    )

    # ── Plan Details ──────────────────────────────────────────
    title = models.CharField(
        max_length=255,
        verbose_name="Title",
        help_text="E.g., '12-Week Fat Loss Program'",
    )
    goal = models.CharField(max_length=50, verbose_name="Goal")
    duration_weeks = models.IntegerField(default=4, verbose_name="Duration (Weeks)")

    class Difficulty(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.BEGINNER,
        verbose_name="Difficulty",
    )

    # ── AI-Generated Content ──────────────────────────────────
    plan_data = models.JSONField(
        verbose_name="Plan Data (JSON)",
        help_text='Structure: {"weeks": [{"days": [{"exercises": [...]}]}]}',
    )

    # ── AI Cost Tracking ──────────────────────────────────────
    ai_model_used = models.CharField(max_length=50, default='gpt-4o-mini', verbose_name="AI Model")
    ai_prompt_tokens = models.IntegerField(default=0, verbose_name="Prompt Tokens")
    ai_completion_tokens = models.IntegerField(default=0, verbose_name="Completion Tokens")

    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'fitness_workoutplan'
        verbose_name = 'Workout Plan'
        verbose_name_plural = 'Workout Plans'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gym', 'member'], name='idx_wplan_gym_member'),
            models.Index(fields=['member', 'is_active'], name='idx_wplan_member_active'),
        ]

    def __str__(self):
        return f"{self.title} - {self.member.name}"


class DietPlan(BaseModel):
    """
    AI-generated diet plans with Indian food focus.
    Dal-chawal, paneer, roti-based diets = massive differentiator.
    """

    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        related_name='diet_plans',
        verbose_name="Gym",
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='diet_plans',
        verbose_name="Member",
    )
    created_by = models.ForeignKey(
        'users.GymUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_diet_plans',
        verbose_name="Created By",
    )

    # ── Plan Details ──────────────────────────────────────────
    title = models.CharField(max_length=255, verbose_name="Title")
    goal = models.CharField(max_length=50, verbose_name="Goal")
    dietary_preference = models.CharField(max_length=30, verbose_name="Dietary Preference")
    daily_calories = models.IntegerField(verbose_name="Daily Calories Target")
    daily_protein_g = models.IntegerField(null=True, blank=True, verbose_name="Daily Protein (g)")
    daily_carbs_g = models.IntegerField(null=True, blank=True, verbose_name="Daily Carbs (g)")
    daily_fat_g = models.IntegerField(null=True, blank=True, verbose_name="Daily Fat (g)")

    # ── AI-Generated Content ──────────────────────────────────
    plan_data = models.JSONField(
        verbose_name="Plan Data (JSON)",
        help_text='Structure: {"days": [{"meals": [{"name", "items", "macros"}]}]}',
    )

    # ── AI Cost Tracking ──────────────────────────────────────
    ai_model_used = models.CharField(max_length=50, default='gpt-4o-mini', verbose_name="AI Model")
    ai_prompt_tokens = models.IntegerField(default=0, verbose_name="Prompt Tokens")
    ai_completion_tokens = models.IntegerField(default=0, verbose_name="Completion Tokens")

    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'fitness_dietplan'
        verbose_name = 'Diet Plan'
        verbose_name_plural = 'Diet Plans'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gym', 'member'], name='idx_dplan_gym_member'),
            models.Index(fields=['member', 'is_active'], name='idx_dplan_member_active'),
        ]

    def __str__(self):
        return f"{self.title} - {self.member.name}"


class Attendance(BaseModel):
    """
    Check-in/check-out records.
    Drives churn prediction AI — missed days = churn risk.
    """

    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name="Gym",
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name="Member",
    )
    check_in = models.DateTimeField(verbose_name="Check-in Time")
    check_out = models.DateTimeField(null=True, blank=True, verbose_name="Check-out Time")
    duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Duration (Minutes)",
    )
    notes = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Notes",
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'fitness_attendance'
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        ordering = ['-check_in']
        indexes = [
            models.Index(fields=['gym', 'member', 'check_in'], name='idx_att_gym_member_in'),
            models.Index(fields=['gym', 'check_in'], name='idx_att_gym_checkin'),
        ]

    def __str__(self):
        return f"{self.member.name} - {self.check_in.strftime('%Y-%m-%d %H:%M')}"


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
        db_table = 'fitness_progresslog'
        verbose_name = 'Progress Log'
        verbose_name_plural = 'Progress Logs'
        ordering = ['-date']
        unique_together = ['member', 'date']
        indexes = [
            models.Index(fields=['gym', 'member', 'date'], name='idx_prog_gym_member_date'),
        ]

    def __str__(self):
        return f"{self.member.name} - {self.date}"
