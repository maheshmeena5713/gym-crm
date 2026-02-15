import os
import django
import sys
from datetime import timedelta

# Setup Django Environment
sys.path.append('/Users/maheshmeena/Downloads/Projects/gym_crm')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from rest_framework.test import APIClient
from apps.users.models import GymUser
from apps.enterprises.models import HoldingCompany, Brand, Organization
from django.db.models import Q

def run_test():
    print("🚀 Starting Enterprise Dashboard Verification...")

    # 1. Setup Test User (Holding Admin)
    # ------------------------------------------------------------------
    phone = "9828099999"
    holding = HoldingCompany.objects.first()
    
    if not holding:
        print("❌ CRITICAL: No Holding Company found. Run setup first.")
        return

    admin_user, created = GymUser.objects.get_or_create(
        phone=phone,
        defaults={'name': 'Holding Admin', 'role': GymUser.Role.HOLDING_ADMIN}
    )
    admin_user.holding_company = holding
    admin_user.role = GymUser.Role.HOLDING_ADMIN
    admin_user.save()
    
    print(f"👤 Created/Updated Holding Admin: {admin_user.name} ({phone}) linked to {holding.name}")

    # 2. Login & Get Token
    # ------------------------------------------------------------------
    client = APIClient()
    # Force authenticate for simplicity (or simulate OTP flow)
    client.force_authenticate(user=admin_user)
    print("🔑 Authenticated as Holding Admin")

    # 3. Test Holding Dashboard API
    # ------------------------------------------------------------------
    url = '/api/v1/enterprises/dashboard/holding/'
    print(f"📡 Requesting {url}...")
    response = client.get(url)

    if response.status_code == 200:
        data = response.json()
        print("\n✅ HOLDING DASHBOARD SUCCESS:")
        print(f"   🏢 Holding Name: {data['holding_name']}")
        print(f"   📊 Total Brands: {data['stats']['total_brands']}")
        print(f"   🏋️ Total Gyms:   {data['stats']['total_gyms']}")
        print(f"   👥 Total Members:{data['stats']['total_members']}")
        
        # Simple Validation
        if data['stats']['total_gyms'] > 0 and data['stats']['total_members'] > 0:
             print("   ✅ Data Validation Passed: Non-zero stats returned.")
        else:
             print("   ⚠️ WARNING: Zero stats returned. Check test data.")

    else:
        print(f"❌ FAILED: {response.status_code}")
        print(response.json())

    # 4. Test Organization Dashboard (Simulate Franchisee)
    # ------------------------------------------------------------------
    print("\n--- Switching to Organization Admin ---")
    org = Organization.objects.first()
    org_user, _ = GymUser.objects.get_or_create(
        phone="9828088888",
        defaults={'name': 'Franchise Owner', 'role': GymUser.Role.ORG_ADMIN}
    )
    org_user.organization = org
    org_user.role = GymUser.Role.ORG_ADMIN
    org_user.save()

    client.force_authenticate(user=org_user)
    org_url = '/api/v1/enterprises/dashboard/organization/'
    print(f"📡 Requesting {org_url}...")
    response = client.get(org_url)
    
    if response.status_code == 200:
         data = response.json()
         print("\n✅ ORG DASHBOARD SUCCESS:")
         print(f"   🏢 Org Name: {data['organization_name']}")
         print(f"   🏋️ Locations: {data['stats']['total_locations']}")
         print(f"   👥 Members:   {data['stats']['total_members']}")
    else:
         print(f"❌ FAILED: {response.status_code}")
         print(response.json())

if __name__ == "__main__":
    run_test()
