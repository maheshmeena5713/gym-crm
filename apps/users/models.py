"""
Users App - Custom User Model (GymUser)
Phone-based OTP authentication for Indian market.
"""

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.models import ActiveManager


class GymUserManager(BaseUserManager):
    """Custom manager for GymUser with phone-based authentication."""

    def create_user(self, username, phone, name, gym=None, role='trainer', password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        if not phone:
            raise ValueError('Phone number is required')
            
        user = self.model(
            username=username,
            phone=phone,
            name=name,
            gym=gym,
            role=role,
            **extra_fields,
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, phone, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'owner')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, phone, name, password=password, **extra_fields)


class GymUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for gym staff.
    Uses phone number as the primary auth field (OTP login for India).
    NOT gym members — these are people who LOGIN to the dashboard.
    """

    # ── UUID Primary Key ──────────────────────────────────────
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )

    # ── Gym Association ───────────────────────────────────────
    gym = models.ForeignKey(
        'gyms.Gym',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='staff',
        verbose_name="Gym",
        help_text="The gym this user belongs to. Null for super admins.",
    )

    # ── Auth Fields ───────────────────────────────────────────
    phone = models.CharField(
        max_length=20,
        unique=False,  # Changed from True to False for multi-gym support
        verbose_name="Phone Number",
        help_text="Primary phone number for OTP login",
        db_index=True,
    )
    email = models.EmailField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Email",
    )
    username = models.CharField(
        max_length=255,
        unique=True,  # Changed to True for USERNAME_FIELD
        db_index=True,
        verbose_name="Username",
        help_text="Login username (lowercase, 4-255 chars, alphanumeric + underscores)",
        error_messages={
            'unique': "A user with that username already exists.",
        },
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Full Name",
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name="Avatar",
    )

    # ── Enterprise Association ────────────────────────────────
    holding_company = models.ForeignKey(
        'enterprises.HoldingCompany',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff',
        verbose_name="Holding Company"
    )
    brand = models.ForeignKey(
        'enterprises.Brand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff',
        verbose_name="Brand"
    )
    organization = models.ForeignKey(
        'enterprises.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff',
        verbose_name="Organization"
    )

    # ── Multi-Location Access ─────────────────────────────────
    locations = models.ManyToManyField(
        'gyms.Gym',
        blank=True,
        related_name='authorized_users',
        verbose_name="Authorized Locations",
        help_text="Specific locations this user can access. Empty = all locations (for owners)"
    )

    # ── Role-Based Access ─────────────────────────────────────
    class Role(models.TextChoices):
        HOLDING_ADMIN = 'holding_admin', 'Holding Admin'
        BRAND_ADMIN = 'brand_admin', 'Brand Admin'
        ORG_ADMIN = 'org_admin', 'Organization Admin (Super Owner)'
        REGION_MANAGER = 'region_manager', 'Regional Manager'
        OWNER = 'owner', 'Gym Owner (Legacy)'
        MANAGER = 'manager', 'Branch Manager'
        TRAINER = 'trainer', 'Trainer'
        RECEPTIONIST = 'receptionist', 'Front Desk'

    role = models.CharField(
        max_length=50,  # Increased length for new roles
        choices=Role.choices,
        default=Role.TRAINER,
        verbose_name="Role",
    )

    # ── Granular Permissions ──────────────────────────────────
    can_view_revenue = models.BooleanField(
        default=False,
        verbose_name="Can View Revenue",
    )
    can_manage_members = models.BooleanField(
        default=True,
        verbose_name="Can Manage Members",
    )
    can_manage_leads = models.BooleanField(
        default=False,
        verbose_name="Can Manage Leads",
    )
    can_use_ai = models.BooleanField(
        default=True,
        verbose_name="Can Use AI Features",
    )

    # ── Status ────────────────────────────────────────────────
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Is Staff",
        help_text="Designates whether the user can log into the admin site.",
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Is Deleted",
        db_index=True,
    )

    # ── Timestamps ────────────────────────────────────────────
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date Joined",
    )
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last Login",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    # ── Manager ───────────────────────────────────────────────
    objects = GymUserManager()
    active_objects = ActiveManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone', 'name']

    class Meta:
        db_table = 'users_gymuser'
        verbose_name = 'Gym User'
        verbose_name_plural = 'Gym Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gym', 'role'], name='idx_user_gym_role'),
            models.Index(fields=['phone'], name='idx_user_phone'),
            models.Index(fields=['username'], name='idx_user_username'),
        ]
        unique_together = [
            ['gym', 'phone'],
            ['gym', 'username'],
        ]

    def __str__(self):
        return f"{self.name} ({self.get_role_display()}) - {self.phone}"

    def get_short_name(self):
        return self.name.split()[0] if self.name else self.phone

    def get_full_name(self):
        return self.name


class OTPSession(models.Model):
    """
    OTP session tracking for phone-based authentication.
    Stores OTP code, expiry, and verification status.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Phone Number",
        db_index=True,
    )
    otp_code = models.CharField(
        max_length=6,
        verbose_name="OTP Code",
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Is Verified",
    )
    attempts = models.IntegerField(
        default=0,
        verbose_name="Verification Attempts",
    )
    expires_at = models.DateTimeField(
        verbose_name="Expires At",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        db_table = 'users_otpsession'
        verbose_name = 'OTP Session'
        verbose_name_plural = 'OTP Sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone', 'is_verified'], name='idx_otp_phone_verified'),
            models.Index(fields=['phone', 'expires_at'], name='idx_otp_phone_expiry'),
        ]

    def __str__(self):
        return f"OTP for {self.phone} ({'Verified' if self.is_verified else 'Pending'})"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
