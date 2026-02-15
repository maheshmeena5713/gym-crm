from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.enterprises.models import HoldingCompany, Organization, RoyaltyLedger
from apps.gyms.models import Gym
from apps.members.models import Member
from apps.enterprises.permissions import IsHoldingAdmin, IsOrgAdmin
from apps.enterprises.services import RoyaltyService
from django.utils import timezone

class HoldingDashboardView(APIView):
    """
    GET /api/v1/enterprises/dashboard/holding/
    Returns consolidated stats for the Holding Company Admin.
    """
    permission_classes = [IsAuthenticated, IsHoldingAdmin]

    def get(self, request):
        holding_company = request.user.holding_company
        if not holding_company:
             return Response({"error": "User not linked to a Holding Company"}, status=400)

        # Get all brands, organizations, and gyms under this holding
        brands = holding_company.brands.all()
        # Flat list of all gyms under this holding
        gyms = Gym.objects.filter(organization__brand__in=brands)
        
        # Aggregated Stats
        total_gyms = gyms.count()
        active_gyms = gyms.filter(is_active=True).count()
        total_members = Member.objects.filter(gym__in=gyms).count()
        active_members = Member.objects.filter(gym__in=gyms, status=Member.Status.ACTIVE).count()
        
        # Revenue (Mocked for now, future Phase 3)
        total_revenue = 0 

        return Response({
            "holding_name": holding_company.name,
            "stats": {
                "total_brands": brands.count(),
                "total_gyms": total_gyms,
                "active_gyms": active_gyms,
                "total_members": total_members,
                "active_members": active_members,
                "total_revenue": total_revenue
            },
            "brands": [{"id": b.id, "name": b.name, "code": b.brand_code} for b in brands]
        })

class OrganizationDashboardView(APIView):
    """
    GET /api/v1/enterprises/dashboard/organization/
    Returns consolidated stats for the Franchise Owner (Organization Admin).
    """
    permission_classes = [IsAuthenticated, IsOrgAdmin]

    def get(self, request):
        organization = request.user.organization
        if not organization:
            return Response({"error": "User not linked to an Organization"}, status=400)

        gyms = organization.locations.all()

        # Aggregated Stats
        total_gyms = gyms.count()
        total_members = Member.objects.filter(gym__in=gyms).count()
        active_members = Member.objects.filter(gym__in=gyms, status=Member.Status.ACTIVE).count()

        return Response({
            "organization_name": organization.name,
            "brand_name": organization.brand.name,
            "stats": {
                "total_locations": total_gyms,
                "total_members": total_members,
                "active_members": active_members,
            },
            "locations": [
                {
                    "id": g.id, 
                    "name": g.name, 
                    "city": g.city, 
                    "members": g.members.count()
                } for g in gyms
            ]
        })

class RoyaltyReportView(APIView):
    """
    GET /api/v1/enterprises/royalties/
    Returns royalty history for the organization.
    Triggers calculation for current month on-the-fly.
    """
    permission_classes = [IsAuthenticated, IsOrgAdmin]

    def get(self, request):
        organization = request.user.organization
        if not organization:
            return Response({"error": "User not linked to an Organization"}, status=400)
        
        # 1. Trigger calculation for current month (Demo purpose)
        today = timezone.now().date()
        RoyaltyService.generate_ledger_for_month(organization, today.year, today.month)
        
        # 2. List all ledgers
        ledgers = RoyaltyLedger.objects.filter(organization=organization).order_by('-month')
        
        return Response({
            "organization": organization.name,
            "brand": organization.brand.name,
            "royalty_terms": {
                "percentage": organization.brand.royalty_percentage,
                "flat_fee": organization.brand.royalty_flat_fee
            },
            "history": [
                {
                    "month": l.month.strftime('%B %Y'),
                    "gross_revenue": l.gross_revenue,
                    "royalty_due": l.calculated_royalty,
                    "is_paid": l.is_paid,
                    "paid_date": l.paid_date
                } for l in ledgers
            ]
        })
