from django.utils import timezone
from django.db.models import Sum
from datetime import date
from decimal import Decimal

from apps.enterprises.models import RoyaltyLedger, Organization
from apps.members.models import Member
# Assuming a Payment model exists or we use Member.amount_paid for simplicity in Phase 3
# Ideally, we should query a Transaction/Payment model. 
# For now, we will simulate revenue based on Member.amount_paid joined in that month.

class RoyaltyService:
    @staticmethod
    def generate_ledger_for_month(organization, year, month):
        """
        Calculates revenue and generates/updates the RoyaltyLedger for a specific month.
        """
        # 1. Calculate Gross Revenue
        # In a real scenario, filter Payment/Invoice models by date range.
        # Here we mock it or use a simple aggregation if models exist.
        # Let's say we aggregate 'amount_paid' from Members joined in that month specific to this org's gyms.
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        # Gyms under this org
        gyms = organization.locations.all()
        
        # Simple Revenue Calculation: Sum of amount_paid for members joined in this month
        revenue = Member.objects.filter(
            gym__in=gyms,
            join_date__gte=start_date,
            join_date__lt=end_date
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

        # 2. Get Brand Rules
        brand = organization.brand
        royalty_pct = brand.royalty_percentage
        flat_fee = brand.royalty_flat_fee

        # 3. Calculate Royalty
        royalty_from_pct = revenue * (royalty_pct / 100)
        total_royalty = royalty_from_pct + flat_fee

        # 4. Create/Update Ledger
        ledger, created = RoyaltyLedger.objects.update_or_create(
            organization=organization,
            month=start_date,
            defaults={
                'gross_revenue': revenue,
                'royalty_percentage': royalty_pct,
                'royalty_flat_fee': flat_fee,
                'calculated_royalty': total_royalty
            }
        )
        return ledger

    @staticmethod
    def generate_all_ledgers(year, month):
        """
        Batch job to generate ledgers for all active organizations.
        """
        orgs = Organization.active_objects.filter(is_franchise=True)
        results = []
        for org in orgs:
            ledger = RoyaltyService.generate_ledger_for_month(org, year, month)
            results.append(ledger)
        return results
