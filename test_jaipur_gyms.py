
import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.users.models import GymUser
from apps.gyms.models import Gym
from apps.users.services import OTPService
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken

def run_test():
    print("🚀 Starting Full Multi-Gym Flow Test (Jaipur Edition)...\n")

    # 1. Setup Data
    phone = "9828012345" # Common Jaipur series
    
    # Cleanup previous test run for this phone
    GymUser.objects.filter(phone=phone).delete()
    Gym.objects.filter(name__in=["Jaipur Fitness Club", "Pink City Strength"]).delete()

    print("📍 Creating 2 New Gyms in Jaipur...")
    gym_1 = Gym.objects.create(name="Jaipur Fitness Club", email="contact@jaipurfitness.com")
    gym_2 = Gym.objects.create(name="Pink City Strength", email="info@pinkcitygym.com")
    print(f"   ✅ Created: {gym_1.name} (ID: {gym_1.id})")
    print(f"   ✅ Created: {gym_2.name} (ID: {gym_2.id})")

    print("\n👤 Creating Staff Member 'Rajesh Meena' at BOTH gyms with same phone...")
    user_1 = GymUser.objects.create(
        gym=gym_1, 
        name="Rajesh Meena", 
        phone=phone, 
        role="owner"
    )
    user_2 = GymUser.objects.create(
        gym=gym_2, 
        name="Rajesh Meena", 
        phone=phone, 
        role="owner"
    )
    print(f"   ✅ User created at {user_1.gym.name} (ID: {user_1.id})")
    print(f"   ✅ User created at {user_2.gym.name} (ID: {user_2.id})")

    # 2. Simulate Login Flow
    print("\n🔐 Step 1: Sending OTP...")
    OTPService.send_otp(phone)
    print("   ✅ OTP Sent")

    print("\n🔐 Step 2: Verifying OTP (Entering '123456')...")
    success, result = OTPService.verify_otp(phone, "123456")

    if not success:
        print(f"   ❌ Verification Failed: {result}")
        return

    if result.get('is_multi_account'):
        print("   ✅ SUCCESS: Multi-Account Detected!")
        accounts = result['accounts']
        print(f"   📋 Found {len(accounts)} accounts linked to {phone}:")
        for i, acc in enumerate(accounts):
            print(f"      [{i}] {acc.gym.name} - {acc.get_role_display()}")
    else:
        print("   ❌ FAILURE: Expected multi-account response, got single user.")
        return

    # 3. Simulate Account Selection
    print("\n👉 Step 3: Selecting 'Jaipur Fitness Club'...")
    selected_account = accounts[0] # Assuming order, identifying by gym name below
    if selected_account.gym.name != "Jaipur Fitness Club":
        selected_account = accounts[1]
    
    # Generate Selection Token (Mocking View Logic)
    selection_token = RefreshToken().for_user(result['accounts'][0])
    selection_token.payload['phone_verification'] = phone
    token_str = str(selection_token)
    print(f"   🎟️  Generated Selection Token")

    print(f"\n🔐 Step 4: Finalizing Login for Account ID {selected_account.id}...")
    
    # Verify Token & Login (Mocking SelectAccountView Logic)
    try:
        decoded = UntypedToken(token_str)
        token_phone = decoded.get('phone_verification')
        
        if token_phone != phone:
             print("   ❌ FAILURE: Token phone mismatch")
             return

        final_user = GymUser.objects.get(id=selected_account.id, phone=token_phone)
        
        refresh = RefreshToken.for_user(final_user)
        access_token = str(refresh.access_token)
        
        print("\n🎉 LOGIN SUCCESSFUL!")
        print(f"   👤 Logged in as: {final_user.name}")
        print(f"   Pk: {final_user.id}")
        print(f"   🏋️  Gym Context: {final_user.gym.name}")
        print(f"   🔑 Access Token Generated: {access_token[:15]}...")
        
    except Exception as e:
        print(f"   ❌ FAILURE: Final Login Error: {e}")

if __name__ == "__main__":
    run_test()
