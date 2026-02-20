import os
import sys
import random
from datetime import timedelta
from django.utils import timezone

# Adjust if necessary to point to the correct settings module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from apps.gyms.models import Gym
from apps.users.models import GymUser
from apps.billing.models import SubscriptionPlan, GymSubscription
from apps.members.models import Member, MembershipPlan

FIRST_NAMES = [
    "Rahul", "Amit", "Priya", "Neha", "Ravi", "Suresh", "Ramesh", "Anjali", "Pooja", "Vikram",
    "Sanjay", "Rajesh", "Kavita", "Sunita", "Arun", "Manoj", "Kiran", "Meena", "Geeta", "Rekha",
    "Anil", "Sunil", "Dinesh", "Deepak", "Rakesh", "Vijay", "Aarti", "Jyoti", "Lata", "Usha",
    "Ashok", "Gopal", "Prakash", "Manish", "Nitin", "Nisha", "Swati", "Sonali", "Sneha", "Rohit",
    "Mohit", "Akash", "Vishal", "Gaurav", "Saurabh", "Prashant", "Vivek", "Tarun", "Varun", "Karan"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Kumar", "Singh", "Yadav", "Patel", "Meena", "Choudhary", "Jain",
    "Agarwal", "Bansal", "Mishra", "Tiwari", "Pandey", "Dixit", "Dubey", "Joshy", "Bhatt", "Rao",
    "Reddy", "Nair", "Iyer", "Khanna", "Kapoor", "Chopra", "Malhotra", "Ahuja", "Bhatia", "Sethi",
    "Jha", "Sinha", "Das", "Bose", "Ghosh", "Dutta", "Sen", "Nandi", "Mukherjee", "Banerjee"
]

GYM_DATA = [
    {"name": "Iron Core Fitness Jaipur", "city": "Jaipur", "address": "Raja Park, Jaipur", "type": "Starter"},
    {"name": "Pink City Muscle", "city": "Jaipur", "address": "Vaishali Nagar, Jaipur", "type": "Starter"},
    {"name": "The Flex Studio Jaipur", "city": "Jaipur", "address": "Malviya Nagar, Jaipur", "type": "Growth"},
    {"name": "Urban Fit Gym", "city": "Jaipur", "address": "Mansarovar, Jaipur", "type": "Growth"},
    {"name": "Elite Fitness Club", "city": "Jaipur", "address": "C-Scheme, Jaipur", "type": "Pro"},
    {"name": "Royal Gym & Spa", "city": "Jaipur", "address": "Jagatpura, Jaipur", "type": "Pro"}
]

def generate_phone():
    return "+91" + "".join([str(random.randint(0, 9)) for _ in range(10)])

def seed_data():
    print("Starting data seeding...")

    # 1. Ensure Subscription Plans exist
    plans = {
        "Starter": SubscriptionPlan.objects.get_or_create(
            slug="starter",
            defaults={"name": "Starter", "price_monthly": 799, "price_yearly": 7990, "display_order": 1}
        )[0],
        "Growth": SubscriptionPlan.objects.get_or_create(
            slug="growth",
            defaults={"name": "Growth", "price_monthly": 1299, "price_yearly": 12990, "display_order": 2, "has_lead_management": True}
        )[0],
        "Pro": SubscriptionPlan.objects.get_or_create(
            slug="pro",
            defaults={"name": "Pro", "price_monthly": 1999, "price_yearly": 19990, "display_order": 3, "has_lead_management": True, "has_ai_diet": True}
        )[0]
    }

    # Clean existing data to avoid conflicts on re-run (optional: could be skipped if appending instead)
    # We will just append or skip if exists to be safe. Since users are unique by username, we will use a unique prefix.
    suffix = str(random.randint(1000, 9999))

    for gym_info in GYM_DATA:
        plan = plans[gym_info["type"]]
        
        # Create Gym
        gym = Gym.objects.create(
            name=gym_info["name"],
            city=gym_info["city"],
            address=gym_info["address"],
            state="Rajasthan",
            owner_name="Owner " + gym_info["name"].split()[0],
            owner_phone=generate_phone(),
            email=f"owner_{suffix}_{gym_info['name'].replace(' ', '').lower()}@gymedge.com",
            subscription_plan=plan,
            subscription_status=Gym.SubscriptionStatus.ACTIVE
        )
        print(f"Created Gym: {gym.name} (Plan: {plan.name})")

        # Create Gym Subscription
        GymSubscription.objects.create(
            gym=gym,
            plan=plan,
            billing_cycle='monthly',
            amount=plan.price_monthly,
            status='active',
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30)
        )

        # Create Owner User
        owner_username = f"admin_{gym.slug.replace('-', '_')}"
        # Ensure username isn't too long
        owner_username = owner_username[:30]
        
        # In case the exact username is taken from a previous run
        if GymUser.objects.filter(username=owner_username).exists():
           owner_username = owner_username[:25] + suffix
           
        owner = GymUser.objects.create_user(
            username=owner_username,
            phone=gym.owner_phone,
            name=gym.owner_name,
            gym=gym,
            role=GymUser.Role.OWNER,
            password="Qwerty@123",
            email=gym.email
        )
        print(f"  Owner: {owner_username} / Qwerty@123")

        # Create Membership Plans for the gym
        m_plans = [
            MembershipPlan.objects.create(gym=gym, name="1 Month Basic", duration_months=1, price=1500),
            MembershipPlan.objects.create(gym=gym, name="3 Month Standard", duration_months=3, price=4000),
            MembershipPlan.objects.create(gym=gym, name="Annual Premium", duration_months=12, price=12000, includes_trainer=True)
        ]

        # Create 100 Members
        print(f"  Creating 100 members for {gym.name}...")
        members_to_create = []
        for i in range(100):
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            m_plan = random.choice(m_plans)
            
            # Scatter joining dates anywhere from 1 year ago to today
            days_ago = random.randint(0, 365)
            join_date = (timezone.now() - timedelta(days=days_ago)).date()
            
            # Scatter statuses (Mostly active, some expired or frozen)
            status_choice = random.choices(
                [Member.Status.ACTIVE, Member.Status.EXPIRED, Member.Status.FROZEN],
                weights=[70, 20, 10], k=1
            )[0]
            
            if status_choice == Member.Status.ACTIVE:
                membership_expiry = (timezone.now() + timedelta(days=random.randint(10, 100))).date()
            elif status_choice == Member.Status.EXPIRED:
                membership_expiry = (timezone.now() - timedelta(days=random.randint(1, 60))).date()
            else:
                membership_expiry = (timezone.now() + timedelta(days=30)).date()

            members_to_create.append(
                Member(
                    gym=gym,
                    name=name,
                    phone=generate_phone(),
                    gender=random.choice([Member.Gender.MALE, Member.Gender.FEMALE]),
                    goal=random.choice(Member.Goal.choices)[0],
                    experience_level=random.choice(Member.ExperienceLevel.choices)[0],
                    membership_plan=m_plan,
                    join_date=join_date,
                    membership_start=join_date,
                    membership_expiry=membership_expiry,
                    amount_paid=m_plan.price,
                    status=status_choice,
                    churn_risk_score=random.randint(0, 100) if status_choice == Member.Status.ACTIVE else 0
                )
            )
        Member.objects.bulk_create(members_to_create)
        print(f"  Done creating members for {gym.name}.\n")

    print("\nSeeding complete! Admin passwords are 'Qwerty@123'.")

if __name__ == "__main__":
    seed_data()
