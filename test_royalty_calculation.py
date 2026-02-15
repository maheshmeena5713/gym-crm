import os
import django
import sys
from datetime import date
from decimal import Decimal

# Setup Django Environment
sys.path.append('/Users/maheshmeena/Downloads/Projects/gym_crm')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from rest_framework.test import APIClient
from apps.users.models import GymUser
from apps.enterprises.models import Organization, RoyaltyLedger
from apps.enterprises.services import RoyaltyService
from apps.members.models import Member
from django.utils import timezone

def run_test():
    print("💰 Starting Royalty Calculation Verification...")

    # 1. Setup Test Data
    # ------------------------------------------------------------------
    org = Organization.objects.get(name='Independent Gyms')
    
    # Configure Brand Royalty for Predictable Results
    brand = org.brand
    brand.royalty_percentage = Decimal('10.00') # 10%
    brand.royalty_flat_fee = Decimal('500.00')  # ₹500
    brand.save()
    
    print(f"✅ Configured '{brand.name}' with 10% Royalty + ₹500 Flat Fee.")

    # Ensure Members Exist (from previous test)
    gyms = org.locations.all()
    # Mock member payments: Update existing members with amount_paid = 1000
    Member.objects.filter(gym__in=gyms).update(amount_paid=1000)
    
    member_count = Member.objects.filter(gym__in=gyms).count()
    expected_revenue = member_count * 1000
    print(f"👥 Found {member_count} members. Expected Gross Revenue: ₹{expected_revenue}")

    # 2. Test Service Calculation
    # ------------------------------------------------------------------
    today = timezone.now().date()
    ledger = RoyaltyService.generate_ledger_for_month(org, today.year, today.month)
    
    print(f"🧾 Ledger Generated: {ledger}")
    print(f"   -> Gross Revenue: ₹{ledger.gross_revenue}")
    print(f"   -> Calculated Royalty: ₹{ledger.calculated_royalty}")

    expected_royalty = (Decimal(expected_revenue) * Decimal('0.10')) + Decimal('500.00')
    
    if ledger.gross_revenue == expected_revenue and ledger.calculated_royalty == expected_royalty:
        print("✅ SERVICE CALCULATION PASSED")
    else:
        print(f"❌ SERVICE CALCULATION FAILED. Expected ₹{expected_royalty}, Got ₹{ledger.calculated_royalty}")

    # 3. Test API Endpoint
    # ------------------------------------------------------------------
    # Setup Franchise Owner User
    user, _ = GymUser.objects.get_or_create(
        phone="9828077777",
        defaults={'name': 'Royalty Tester', 'role': GymUser.Role.ORG_ADMIN}
    )
    user.organization = org
    user.role = GymUser.Role.ORG_ADMIN
    user.save()

    client = APIClient()
    client.force_authenticate(user=user)
    
    url = '/api/v1/enterprises/royalties/'
    print(f"📡 Requesting {url}...")
    response = client.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ API SUCCESS:")
        print(f"   🏢 Organization: {data['organization']}")
        print(f"   📊 Royalty Terms: {data['royalty_terms']}")
        print(f"   📜 History Entries: {len(data['history'])}")
        
        latest = data['history'][0]
        if float(latest['gross_revenue']) == float(expected_revenue):
             print("   ✅ API Data Validation Passed.")
        else:
             print(f"   ⚠️ WARNING: API data mismatch. Got {latest['gross_revenue']}, Expected {expected_revenue}")
    else:
        print(f"❌ API FAILED: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    run_test()
