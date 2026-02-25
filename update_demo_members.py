import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# Ensure django is setup if run standalone
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.gyms.models import Gym
from apps.members.models import Member, MembershipPlan

# Ensure django is setup if run standalone
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def populate_demo_data():
    try:
        gym = Gym.objects.get(gym_code='GYM6807272')
    except Gym.DoesNotExist:
        print("Gym GYM6807272 not found!")
        return

    # Clear existing members for a clean slate using HARD DELETE
    # because BaseModel uses soft delete by default which leaves the phone number uniqueness constraint active.
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM members_member WHERE gym_id = %s", [str(gym.id)])

    # Ensure at least one membership plan exists
    plan, _ = MembershipPlan.objects.get_or_create(
        gym=gym,
        name='Standard Monthly',
        defaults={
            'duration_months': 1,
            'price': 1500.00,
            'includes_trainer': False,
            'description': 'Standard monthly plan'
        }
    )

    now = timezone.now()
    today = now.date()

    real_names = [
        "John Smith", "Emma Johnson", "Michael Brown", "Sophia Davis", 
        "James Wilson", "Olivia Taylor", "William Anderson", "Ava Thomas", 
        "Alexander Jackson", "Mia White", "Daniel Harris", "Charlotte Martin", 
        "Matthew Thompson", "Amelia Garcia", "Joseph Martinez", "Chloe Robinson",
        "David Clark", "Emily Rodriguez", "Andrew Lewis", "Isabella Lee",
        "Joshua Walker", "Grace Hall", "Christopher Allen", "Lily Young"
    ]

    # Helper to generate phones safely
    phone_counter = 10000000
    def gen_phone():
        nonlocal phone_counter
        phone_counter += 1
        return f"+9198{phone_counter}"

    # We want varied profiles to make the dashboard look active:
    # 1. 10 Active & Healthy
    # 2. 5 Expiring Soon (within 7 days)
    # 3. 5 At Risk (high churn score, strict no attendance)
    # 4. 4 Expired

    members_to_create = []

    # 1. Active & Healthy (Expiry in 30-90 days, recent check-in, low churn)
    for i in range(10):
        name = real_names.pop(0)
        members_to_create.append(Member(
            gym=gym,
            name=name,
            phone=gen_phone(),
            email=f"{name.split()[0].lower()}@example.com",
            gender=random.choice(['male', 'female']),
            goal=random.choice(Member.Goal.values),
            experience_level=random.choice(Member.ExperienceLevel.values),
            membership_plan=plan,
            join_date=today - timedelta(days=random.randint(30, 180)),
            membership_start=today - timedelta(days=15),
            membership_expiry=today + timedelta(days=random.randint(15, 90)),
            status='active',
            last_check_in=now - timedelta(days=random.randint(0, 2)),
            churn_risk_score=random.randint(5, 20)
        ))

    # 2. Expiring Soon (within 7 days)
    for i in range(5):
        name = real_names.pop(0)
        members_to_create.append(Member(
            gym=gym,
            name=name,
            phone=gen_phone(),
            email=f"{name.split()[0].lower()}@example.com",
            gender=random.choice(['male', 'female']),
            goal=random.choice(Member.Goal.values),
            experience_level=random.choice(Member.ExperienceLevel.values),
            membership_plan=plan,
            join_date=today - timedelta(days=random.randint(30, 180)),
            membership_start=today - timedelta(days=28),
            membership_expiry=today + timedelta(days=random.randint(1, 6)),
            status='active',
            last_check_in=now - timedelta(days=random.randint(1, 5)),
            churn_risk_score=random.randint(30, 50)
        ))

    # 3. At Risk (No attendance in 10+ days, high churn score > 80)
    for i in range(5):
        name = real_names.pop(0)
        members_to_create.append(Member(
            gym=gym,
            name=name,
            phone=gen_phone(),
            email=f"{name.split()[0].lower()}@example.com",
            gender=random.choice(['male', 'female']),
            goal=random.choice(Member.Goal.values),
            experience_level=random.choice(Member.ExperienceLevel.values),
            membership_plan=plan,
            join_date=today - timedelta(days=random.randint(60, 180)),
            membership_start=today - timedelta(days=45),
            membership_expiry=today + timedelta(days=random.randint(15, 30)),
            status='active',
            last_check_in=now - timedelta(days=random.randint(12, 25)),
            churn_risk_score=random.randint(85, 99)
        ))

    # 4. Expired
    for i in range(4):
        name = real_names.pop(0)
        members_to_create.append(Member(
            gym=gym,
            name=name,
            phone=gen_phone(),
            email=f"{name.split()[0].lower()}@example.com",
            gender=random.choice(['male', 'female']),
            goal=random.choice(Member.Goal.values),
            experience_level=random.choice(Member.ExperienceLevel.values),
            membership_plan=plan,
            join_date=today - timedelta(days=random.randint(90, 180)),
            membership_start=today - timedelta(days=60),
            membership_expiry=today - timedelta(days=random.randint(2, 20)),
            status='expired',
            last_check_in=now - timedelta(days=random.randint(30, 60)),
            churn_risk_score=100
        ))

    Member.objects.bulk_create(members_to_create)
    print(f"Successfully populated {len(members_to_create)} demo members for {gym.name}.")

if __name__ == '__main__':
    populate_demo_data()
