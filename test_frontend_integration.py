import os
import django
import sys
from django.test import Client

# Setup Django Environment
sys.path.append('/Users/maheshmeena/Downloads/Projects/gym_crm')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.users.models import GymUser
from apps.enterprises.models import HoldingCompany, Organization
from apps.gyms.models import Gym

def run_test():
    print("🖥️ Starting Frontend Integration Verification...")
    client = Client()

    # 1. Test Holding Admin (Should see Enterprise Dashboard)
    # ------------------------------------------------------------------
    admin_user = GymUser.objects.filter(role=GymUser.Role.HOLDING_ADMIN).first()
    if not admin_user:
        print("❌ No Holding Admin found. Run previous tests first.")
        return

    client.force_login(admin_user)
    print(f"🔑 Logged in as {admin_user.name} ({admin_user.role})")
    
    response = client.get('/dashboard/')
    content = response.content.decode()
    
    if response.status_code == 200 and "Enterprise Dashboard" in content:
        print("✅ HOLDING ADMIN: Redirected to Enterprise Dashboard.")
    else:
        print(f"❌ HOLDING ADMIN FAILED. Status: {response.status_code}")
        if "Enterprise Dashboard" not in content:
             print("   ⚠️ Content mismatch. Expected 'Enterprise Dashboard'.")

    client.logout()

    # 2. Test Org Admin (Should see Enterprise Dashboard)
    # ------------------------------------------------------------------
    org_user = GymUser.objects.filter(role=GymUser.Role.ORG_ADMIN).first()
    if org_user:
        client.force_login(org_user)
        print(f"🔑 Logged in as {org_user.name} ({org_user.role})")
        response = client.get('/dashboard/')
        content = response.content.decode()
        
        if response.status_code == 200 and "Enterprise Dashboard" in content:
            print("✅ ORG ADMIN: Redirected to Enterprise Dashboard.")
        else:
            print(f"❌ ORG ADMIN FAILED.")
        client.logout()

    # 3. Test Gym Owner (Should see Standard Dashboard)
    # ------------------------------------------------------------------
    # Create or get a standard gym owner
    gym = Gym.objects.first()
    owner, _ = GymUser.objects.get_or_create(
        phone='9812345678',
        defaults={'name': 'Standard Owner', 'role': 'owner', 'gym': gym}
    )
    owner.role = 'owner'
    owner.gym = gym
    owner.save()

    client.force_login(owner)
    print(f"🔑 Logged in as {owner.name} (owner)")
    response = client.get('/dashboard/')
    content = response.content.decode()
    
    # Standard dashboard usually has "My Gym" or similar unique text. 
    # Or we check that it does NOT have "Enterprise Dashboard".
    if response.status_code == 200 and "Enterprise Dashboard" not in content:
        print("✅ GYM OWNER: Saw Standard Dashboard (Not Enterprise).")
    else:
        print(f"❌ GYM OWNER FAILED. Saw Enterprise Dashboard?")

if __name__ == "__main__":
    run_test()
