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

    def __str__(self):
        return self.name


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
        on_delete=models.CASCADE,
        related_name='organizations',
        verbose_name="Brand"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Organization Name",
        help_text="Legal name of the franchise/owner entity"
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
        ]

    def __str__(self):
        return f"{self.name} ({self.brand.name})"


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
