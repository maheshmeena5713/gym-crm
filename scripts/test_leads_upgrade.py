
import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.gyms.models import Gym
from apps.users.models import GymUser
from apps.leads.models import Lead
from apps.leads.services import LeadService
from apps.members.models import Member
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.leads.api.views import LeadViewSet

def run_test():
    print("🚀 Starting Leads Upgrade Verification...")

    # 1. Setup Test Data
    gym, _ = Gym.objects.get_or_create(
        name="Test Gym Leads",
        slug="test-gym-leads",
        defaults={'email': 'leads@test.com'}
    )
    
    owner, _ = GymUser.objects.get_or_create(
        username="lead_owner",
        defaults={'email': 'owner@leads.com', 'role': GymUser.Role.OWNER, 'gym': gym}
    )

    # Clean up existing data
    Lead.objects.filter(gym=gym).delete()
    Member.objects.filter(gym=gym, phone__startswith="999").delete()

    print("✅ Test Environment Setup")

    # 2. Create Leads
    lead1 = Lead.objects.create(
        gym=gym,
        name="Lead One",
        phone="9990000001",
        status=Lead.Status.NEW
    )
    
    lead2 = Lead.objects.create(
        gym=gym,
        name="Lead Two",
        phone="9990000002",
        status=Lead.Status.TRIAL_BOOKED
    )
    print(f"✅ Created Leads: {lead1.id}, {lead2.id}")

    # 3. Test Summary Service
    stats = LeadService.get_lead_summary(gym)
    print(f"📊 Initial Stats: {stats}")
    assert stats['total'] == 2
    assert stats['trials'] == 1
    assert stats['converted_total'] == 0

    # 4. Test Conversion API
    factory = APIRequestFactory()
    view = LeadViewSet.as_view({'post': 'convert'})
    
    request = factory.post(f'/api/v1/leads/{lead1.id}/convert/')
    force_authenticate(request, user=owner)
    request.user = owner # Explicitly set user for creating member
    
    response = view(request, pk=lead1.id)
    print(f"🔄 Conversion Response: {response.status_code} - {response.data}")

    if response.status_code == 200:
        lead1.refresh_from_db()
        print(f"✅ Lead Status: {lead1.status}")
        print(f"✅ Converted At: {lead1.converted_at}")
        
        member = Member.objects.get(phone="9990000001", gym=gym)
        print(f"✅ Created Member: {member.name} ({member.status})")
        
        assert lead1.status == Lead.Status.CONVERTED
        assert lead1.converted_member == member
    else:
        print("❌ Conversion API Failed")

    # 5. Test Summary after Conversion
    stats = LeadService.get_lead_summary(gym)
    print(f"📊 Final Stats: {stats}")
    assert stats['converted_total'] == 1
    assert stats['trials'] == 1
    assert stats['conversion_rate'] > 0

    print("🎉 All Tests Passed!")

if __name__ == '__main__':
    try:
        run_test()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
