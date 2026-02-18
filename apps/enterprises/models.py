"""
Enterprises App - Core Hierarchy Models
Defines the structure: HoldingCompany -> Brand -> Organization (Franchise/Owner).
"""

from django.db import models
from apps.core.models import BaseModel, ActiveManager


class HoldingCompany(BaseModel):
    """
    Top-level entity (e.g., 'FitGroup Inc').
    Owns multiple brands.
    """
    name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Holding Company Name"
    )
    legal_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Legal Entity Name"
    )
    logo = models.ImageField(
        upload_to='holding_logos/',
        null=True,
        blank=True,
        verbose_name="Logo"
    )
    contact_email = models.EmailField(
        verbose_name="Contact Email"
    )
    contact_phone = models.CharField(
        max_length=20,
        verbose_name="Contact Phone"
    )
    holding_code = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        null=True,  # Null for migration, will populate later
        verbose_name="Holding Code",
        help_text="Unique identifier for login (e.g. HOLD4829)."
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active"
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'enterprises_holdingcompany'
        verbose_name = 'Holding Company'
        verbose_name_plural = 'Holding Companies'
        indexes = [
            models.Index(fields=['holding_code'], name='idx_holding_code'),
        ]

    def __str__(self):
        return self.name

    @staticmethod
    def _generate_holding_code():
        """Generate unique code like HOLD482915."""
        import random, string
        while True:
            code = 'HOLD' + ''.join(random.choices(string.digits, k=6))
            if not HoldingCompany.objects.filter(holding_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.holding_code:
            self.holding_code = self._generate_holding_code()
        super().save(*args, **kwargs)


class Brand(BaseModel):
    """
    A fitness brand under a holding company (e.g., 'Gold\'s Gym').
    Defines royalty structure.
    """
    holding_company = models.ForeignKey(
        HoldingCompany,
        on_delete=models.CASCADE,
        related_name='brands',
        verbose_name="Holding Company"
    )
    name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Brand Name"
    )
    brand_code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="Brand Code",
        help_text="Unique identifier for the brand"
    )
    royalty_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="Royalty (%)",
        help_text="Percentage of gross revenue paid to brand"
    )
    royalty_flat_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Royalty Flat Fee (₹)",
        help_text="Fixed monthly royalty fee"
    )
    logo = models.ImageField(
        upload_to='brand_logos/',
        null=True,
        blank=True,
        verbose_name="Brand Logo"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active"
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'enterprises_brand'
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'
        indexes = [
            models.Index(fields=['holding_company', 'name'], name='idx_brand_holding_name'),
            models.Index(fields=['brand_code'], name='idx_brand_code'),
        ]

    def __str__(self):
        return f"{self.name} ({self.holding_company.name})"


class Organization(BaseModel):
    """
    The legal entity owning one or more locations (e.g., 'Jaipur Franchisee Pvt Ltd').
    This represents the Franchise Owner or Corporate Entity.
    """
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organizations',
        verbose_name="Brand",
        help_text="Optional: Brand if part of enterprise/franchise structure"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Organization Name",
        help_text="Legal name of the franchise/owner entity"
    )
    org_code = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        null=True,  # Null for migration
        verbose_name="Organization Code",
        help_text="Unique identifier for login (e.g. ORG4829)."
    )
    entity_code = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        null=True,  # Null for migration, will be populated
        db_index=True,
        verbose_name="Entity Code",
        help_text="Unified login identifier (e.g. GYM7654321). Used for all user logins."
    )
    owner_name = models.CharField(
        max_length=255,
        verbose_name="Owner Name"
    )
    owner_email = models.EmailField(
        db_index=True,
        verbose_name="Owner Email"
    )
    owner_phone = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name="Owner Phone"
    )
    
    # Franchise Details
    is_franchise = models.BooleanField(
        default=True,
        verbose_name="Is Franchise",
        help_text="True if franchisee-owned, False if corporate-owned"
    )
    franchise_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Franchise Start Date"
    )

    # Subscription (moved from Gym)
    subscription_plan = models.ForeignKey(
        'billing.SubscriptionPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organizations',
        verbose_name="Subscription Plan"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active"
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'enterprises_organization'
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
        indexes = [
            models.Index(fields=['brand', 'owner_email'], name='idx_org_brand_email'),
            models.Index(fields=['owner_phone'], name='idx_org_owner_phone'),
            models.Index(fields=['org_code'], name='idx_org_code'),
            models.Index(fields=['entity_code'], name='idx_entity_code'),
        ]

    def __str__(self):
        if self.brand:
            return f"{self.name} ({self.brand.name})"
        return self.name

    @staticmethod
    def _generate_org_code():
        """Generate unique code like ORG482915."""
        import random, string
        while True:
            code = 'ORG' + ''.join(random.choices(string.digits, k=6))
            if not Organization.objects.filter(org_code=code).exists():
                return code

    @staticmethod
    def _generate_entity_code():
        """Generate unique entity code like GYM7654321."""
        import random, string
        while True:
            code = 'GYM' + ''.join(random.choices(string.digits, k=7))
            if not Organization.objects.filter(entity_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.org_code:
            self.org_code = self._generate_org_code()
        if not self.entity_code:
            self.entity_code = self._generate_entity_code()
        super().save(*args, **kwargs)


class RoyaltyLedger(BaseModel):
    """
    Tracks monthly royalty payments from Organizations to the Brand.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='royalty_ledgers',
        verbose_name="Organization"
    )
    month = models.DateField(
        verbose_name="Month",
        help_text="The first day of the month for this ledger entry"
    )
    gross_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Gross Revenue (₹)"
    )
    royalty_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Royalty % Applied"
    )
    royalty_flat_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Flat Fee Applied (₹)"
    )
    calculated_royalty = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Royalty Due (₹)"
    )
    is_paid = models.BooleanField(
        default=False,
        verbose_name="Is Paid"
    )
    paid_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Paid Date"
    )
    transaction_ref = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Transaction Reference"
    )

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        db_table = 'enterprises_royaltyledger'
        verbose_name = 'Royalty Ledger'
        verbose_name_plural = 'Royalty Ledgers'
        ordering = ['-month', 'organization']
        indexes = [
            models.Index(fields=['organization', 'month'], name='idx_royalty_org_month'),
            models.Index(fields=['is_paid'], name='idx_royalty_paid'),
        ]
        unique_together = ['organization', 'month']

    def __str__(self):
        return f"{self.organization.name} - {self.month.strftime('%b %Y')} - ₹{self.calculated_royalty}"
