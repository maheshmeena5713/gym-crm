"""
Management command to seed demo data for Ryan's Gym & Fitness Club.
Creates the gym, owner, trainers, membership plans, and 25 realistic members.
"""

import base64
import os
import random
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.gyms.models import Gym
from apps.users.models import GymUser
from apps.members.models import MembershipPlan, Member
from apps.billing.models import SubscriptionPlan


class Command(BaseCommand):
    help = "Seed demo data: Ryan's Gym, staff, plans, and 25 members"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n🏋️  Seeding Ryan's Gym & Fitness Club...\n"))

        # ── 1. Load logo as base64 ────────────────────────────
        logo_b64 = None
        logo_dir = os.path.join(settings.BASE_DIR, '..', '.gemini', 'antigravity', 'brain')
        # Search for generated logo file
        for root, dirs, files in os.walk(logo_dir):
            for f in files:
                if 'ryans_gym_logo' in f and f.endswith('.png'):
                    logo_path = os.path.join(root, f)
                    with open(logo_path, 'rb') as img:
                        logo_b64 = f"data:image/png;base64,{base64.b64encode(img.read()).decode()}"
                    self.stdout.write(f"  Logo loaded from: {f}")
                    break
            if logo_b64:
                break

        # ── 2. Create Gym ────────────────────────────────────
        gym_defaults = dict(
            name="Ryan's Gym & Fitness Club",
            owner_name="Sunil Sharma",
            owner_phone="+919928122572",
            email="ryangym.jaipur@gmail.com",
            address="22 B-2, Haldighati Marg E, near NRI Colony, Pratap Nagar, Jaipur, Rajasthan 302015, India",
            city="Jaipur",
            state="Rajasthan",
            pincode="302015",
            latitude=Decimal("26.8559"),
            longitude=Decimal("75.7620"),
            gym_type="standard",
            member_capacity=200,
            monthly_revenue_range="₹2-5 Lakh",
            subscription_status="active",
            is_active=True,
            onboarded_by="Direct",
            referral_source="Instagram",
            # Branding
            brand_color="#ef4444",
            font_family="Outfit",
        )
        if logo_b64:
            gym_defaults['logo_base64'] = logo_b64

        gym, created = Gym.objects.update_or_create(
            slug='ryans-gym-jaipur',
            defaults=gym_defaults,
        )
        self.stdout.write(f"  {'Created' if created else 'Updated'} gym: {gym.name}")
        self.stdout.write(f"  Gym Code: {gym.gym_code}")

        # ── 2. Create Owner + Trainers ───────────────────────
        owner, _ = GymUser.objects.update_or_create(
            phone="9928122572",
            defaults=dict(
                name="Sunil Sharma",
                gym=gym,
                role="owner",
                email="sunil@ryangym.in",
                can_view_revenue=True,
                can_manage_members=True,
                can_manage_leads=True,
                can_use_ai=True,
                is_active=True,
            ),
        )
        owner.set_unusable_password()
        owner.save()
        self.stdout.write(f"  Owner: {owner.name} ({owner.phone})")

        trainers_data = [
            {"name": "Vikram Singh", "phone": "9876501001", "email": "vikram@ryangym.in"},
            {"name": "Priya Meena", "phone": "9876501002", "email": "priya@ryangym.in"},
            {"name": "Rohit Yadav", "phone": "9876501003", "email": "rohit@ryangym.in"},
        ]
        trainers = []
        for td in trainers_data:
            t, _ = GymUser.objects.update_or_create(
                phone=td["phone"],
                defaults=dict(
                    name=td["name"],
                    gym=gym,
                    role="trainer",
                    email=td["email"],
                    can_manage_members=True,
                    can_use_ai=True,
                    is_active=True,
                ),
            )
            t.set_unusable_password()
            t.save()
            trainers.append(t)
            self.stdout.write(f"  Trainer: {t.name}")

        receptionist, _ = GymUser.objects.update_or_create(
            phone="9876501004",
            defaults=dict(
                name="Kavita Joshi",
                gym=gym,
                role="receptionist",
                email="kavita@ryangym.in",
                can_manage_members=True,
                is_active=True,
            ),
        )
        receptionist.set_unusable_password()
        receptionist.save()
        self.stdout.write(f"  Receptionist: {receptionist.name}")

        manager, _ = GymUser.objects.update_or_create(
            phone="9876501005",
            defaults=dict(
                name="Amit Rathore",
                gym=gym,
                role="manager",
                email="amit@ryangym.in",
                can_view_revenue=True,
                can_manage_members=True,
                can_manage_leads=True,
                can_use_ai=True,
                is_active=True,
            ),
        )
        manager.set_unusable_password()
        manager.save()
        self.stdout.write(f"  Manager: {manager.name}")

        # ── 3. Membership Plans ──────────────────────────────
        plans_data = [
            {"name": "Monthly Basic", "months": 1, "price": 1500, "trainer": False, "diet": False, "desc": "Basic gym access with all equipment"},
            {"name": "Quarterly Standard", "months": 3, "price": 4000, "trainer": False, "diet": True, "desc": "3-month access with personalized diet plan"},
            {"name": "Half-Yearly Premium", "months": 6, "price": 7000, "trainer": True, "diet": True, "desc": "6 months with personal trainer + diet plan"},
            {"name": "Annual Gold", "months": 12, "price": 12000, "trainer": True, "diet": True, "desc": "Full year with trainer, diet plan & supplements guidance"},
            {"name": "Personal Training", "months": 1, "price": 5000, "trainer": True, "diet": True, "desc": "1-on-1 personal training sessions (monthly)"},
        ]
        plans = []
        for pd in plans_data:
            p, _ = MembershipPlan.objects.update_or_create(
                gym=gym, name=pd["name"],
                defaults=dict(
                    duration_months=pd["months"],
                    price=Decimal(str(pd["price"])),
                    includes_trainer=pd["trainer"],
                    includes_diet_plan=pd["diet"],
                    description=pd["desc"],
                    is_active=True,
                ),
            )
            plans.append(p)
        self.stdout.write(f"  Plans: {len(plans)} created/updated")

        # ── 4. Members (25 realistic Jaipur members) ─────────
        today = date.today()
        members_data = [
            # Active members — diverse goals, plans, trainers
            {"name": "Arjun Rathore", "phone": "9829100001", "email": "arjun.rathore@gmail.com", "gender": "male", "dob": date(1995, 3, 15), "goal": "muscle_gain", "exp": "intermediate", "diet": "non_veg", "h": 178, "w": 82, "bf": 18, "plan_idx": 3, "trainer_idx": 0, "status": "active", "joined_ago": 280, "streak": 45, "churn": 5},
            {"name": "Sneha Gupta", "phone": "9829100002", "email": "sneha.g@gmail.com", "gender": "female", "dob": date(1998, 7, 22), "goal": "fat_loss", "exp": "beginner", "diet": "veg", "h": 162, "w": 68, "bf": 28, "plan_idx": 2, "trainer_idx": 1, "status": "active", "joined_ago": 150, "streak": 12, "churn": 15},
            {"name": "Rajesh Sharma", "phone": "9829100003", "email": "rajesh.sharma88@gmail.com", "gender": "male", "dob": date(1988, 11, 5), "goal": "strength", "exp": "advanced", "diet": "eggetarian", "h": 175, "w": 90, "bf": 15, "plan_idx": 4, "trainer_idx": 0, "status": "active", "joined_ago": 365, "streak": 60, "churn": 2},
            {"name": "Pooja Meena", "phone": "9829100004", "email": None, "gender": "female", "dob": date(2000, 1, 10), "goal": "general_fitness", "exp": "beginner", "diet": "veg", "h": 158, "w": 55, "bf": 22, "plan_idx": 1, "trainer_idx": 1, "status": "active", "joined_ago": 90, "streak": 20, "churn": 10},
            {"name": "Vikrant Choudhary", "phone": "9829100005", "email": "vikrant.c@yahoo.com", "gender": "male", "dob": date(1992, 5, 28), "goal": "muscle_gain", "exp": "intermediate", "diet": "non_veg", "h": 182, "w": 88, "bf": 16, "plan_idx": 3, "trainer_idx": 2, "status": "active", "joined_ago": 200, "streak": 30, "churn": 8},
            {"name": "Nisha Agarwal", "phone": "9829100006", "email": "nisha.a@gmail.com", "gender": "female", "dob": date(1996, 9, 14), "goal": "flexibility", "exp": "intermediate", "diet": "jain", "h": 165, "w": 58, "bf": 21, "plan_idx": 2, "trainer_idx": 1, "status": "active", "joined_ago": 120, "streak": 25, "churn": 12},
            {"name": "Deepak Verma", "phone": "9829100007", "email": None, "gender": "male", "dob": date(1985, 4, 3), "goal": "fat_loss", "exp": "beginner", "diet": "veg", "h": 170, "w": 95, "bf": 32, "plan_idx": 0, "trainer_idx": None, "status": "active", "joined_ago": 45, "streak": 8, "churn": 35},
            {"name": "Manisha Saini", "phone": "9829100008", "email": "manisha.s@gmail.com", "gender": "female", "dob": date(1999, 12, 30), "goal": "general_fitness", "exp": "beginner", "diet": "veg", "h": 160, "w": 52, "bf": 20, "plan_idx": 1, "trainer_idx": 1, "status": "active", "joined_ago": 60, "streak": 15, "churn": 18},
            {"name": "Karan Panwar", "phone": "9829100009", "email": "karan.p@hotmail.com", "gender": "male", "dob": date(1993, 8, 17), "goal": "sports", "exp": "advanced", "diet": "non_veg", "h": 180, "w": 78, "bf": 12, "plan_idx": 4, "trainer_idx": 2, "status": "active", "joined_ago": 320, "streak": 55, "churn": 3},
            {"name": "Ritu Kumari", "phone": "9829100010", "email": None, "gender": "female", "dob": date(1997, 6, 25), "goal": "fat_loss", "exp": "beginner", "diet": "veg", "h": 155, "w": 72, "bf": 30, "plan_idx": 2, "trainer_idx": 1, "status": "active", "joined_ago": 100, "streak": 10, "churn": 22},
            {"name": "Saurabh Jain", "phone": "9829100011", "email": "saurabh.j@gmail.com", "gender": "male", "dob": date(1990, 2, 8), "goal": "strength", "exp": "advanced", "diet": "jain", "h": 174, "w": 85, "bf": 14, "plan_idx": 3, "trainer_idx": 0, "status": "active", "joined_ago": 400, "streak": 70, "churn": 1},
            {"name": "Ananya Pareek", "phone": "9829100012", "email": "ananya.p@outlook.com", "gender": "female", "dob": date(2001, 11, 19), "goal": "general_fitness", "exp": "beginner", "diet": "veg", "h": 163, "w": 56, "bf": 23, "plan_idx": 0, "trainer_idx": None, "status": "active", "joined_ago": 30, "streak": 6, "churn": 25},
            {"name": "Mohit Mittal", "phone": "9829100013", "email": None, "gender": "male", "dob": date(1994, 7, 2), "goal": "muscle_gain", "exp": "intermediate", "diet": "eggetarian", "h": 176, "w": 80, "bf": 17, "plan_idx": 2, "trainer_idx": 2, "status": "active", "joined_ago": 180, "streak": 22, "churn": 14},
            {"name": "Swati Rajawat", "phone": "9829100014", "email": "swati.r@gmail.com", "gender": "female", "dob": date(1998, 3, 9), "goal": "flexibility", "exp": "intermediate", "diet": "veg", "h": 168, "w": 60, "bf": 24, "plan_idx": 1, "trainer_idx": 1, "status": "active", "joined_ago": 75, "streak": 18, "churn": 20},

            # Expired members
            {"name": "Hemant Soni", "phone": "9829100015", "email": None, "gender": "male", "dob": date(1987, 10, 12), "goal": "fat_loss", "exp": "beginner", "diet": "veg", "h": 168, "w": 100, "bf": 35, "plan_idx": 0, "trainer_idx": None, "status": "expired", "joined_ago": 300, "streak": 0, "churn": 85},
            {"name": "Sunita Meghwal", "phone": "9829100016", "email": "sunita.m@gmail.com", "gender": "female", "dob": date(1991, 5, 20), "goal": "general_fitness", "exp": "beginner", "diet": "veg", "h": 157, "w": 65, "bf": 27, "plan_idx": 1, "trainer_idx": None, "status": "expired", "joined_ago": 250, "streak": 0, "churn": 78},
            {"name": "Pankaj Kumawat", "phone": "9829100017", "email": None, "gender": "male", "dob": date(1989, 1, 30), "goal": "strength", "exp": "intermediate", "diet": "non_veg", "h": 172, "w": 88, "bf": 20, "plan_idx": 2, "trainer_idx": None, "status": "expired", "joined_ago": 400, "streak": 0, "churn": 92},
            {"name": "Komal Sharma", "phone": "9829100018", "email": "komal.s@gmail.com", "gender": "female", "dob": date(2002, 8, 5), "goal": "fat_loss", "exp": "beginner", "diet": "veg", "h": 160, "w": 70, "bf": 29, "plan_idx": 0, "trainer_idx": None, "status": "expired", "joined_ago": 200, "streak": 0, "churn": 70},
            {"name": "Rakesh Yadav", "phone": "9829100019", "email": None, "gender": "male", "dob": date(1986, 12, 18), "goal": "general_fitness", "exp": "beginner", "diet": "non_veg", "h": 165, "w": 78, "bf": 25, "plan_idx": 1, "trainer_idx": None, "status": "expired", "joined_ago": 350, "streak": 0, "churn": 88},

            # Frozen members
            {"name": "Deepika Kanwar", "phone": "9829100020", "email": "deepika.k@gmail.com", "gender": "female", "dob": date(1996, 4, 11), "goal": "fat_loss", "exp": "intermediate", "diet": "veg", "h": 164, "w": 66, "bf": 26, "plan_idx": 2, "trainer_idx": 1, "status": "frozen", "joined_ago": 180, "streak": 0, "churn": 45},
            {"name": "Amit Tanwar", "phone": "9829100021", "email": None, "gender": "male", "dob": date(1993, 9, 7), "goal": "muscle_gain", "exp": "intermediate", "diet": "non_veg", "h": 179, "w": 84, "bf": 19, "plan_idx": 3, "trainer_idx": 0, "status": "frozen", "joined_ago": 220, "streak": 0, "churn": 50},

            # Expiring this week (for dashboard alert)
            {"name": "Naveen Tak", "phone": "9829100022", "email": "naveen.t@gmail.com", "gender": "male", "dob": date(1994, 6, 14), "goal": "muscle_gain", "exp": "intermediate", "diet": "non_veg", "h": 177, "w": 83, "bf": 16, "plan_idx": 1, "trainer_idx": 2, "status": "active", "joined_ago": 88, "streak": 4, "churn": 55, "expiry_override": today + timedelta(days=3)},
            {"name": "Priyanka Rao", "phone": "9829100023", "email": None, "gender": "female", "dob": date(2000, 2, 28), "goal": "general_fitness", "exp": "beginner", "diet": "veg", "h": 161, "w": 54, "bf": 21, "plan_idx": 0, "trainer_idx": None, "status": "active", "joined_ago": 28, "streak": 2, "churn": 60, "expiry_override": today + timedelta(days=5)},

            # Cancelled
            {"name": "Rahul Bairwa", "phone": "9829100024", "email": None, "gender": "male", "dob": date(1991, 3, 25), "goal": "general_fitness", "exp": "beginner", "diet": "veg", "h": 169, "w": 74, "bf": 24, "plan_idx": 0, "trainer_idx": None, "status": "cancelled", "joined_ago": 500, "streak": 0, "churn": 100},
            {"name": "Sapna Kumari", "phone": "9829100025", "email": "sapna.k@gmail.com", "gender": "female", "dob": date(1999, 10, 1), "goal": "fat_loss", "exp": "beginner", "diet": "veg", "h": 156, "w": 75, "bf": 33, "plan_idx": 0, "trainer_idx": None, "status": "cancelled", "joined_ago": 450, "streak": 0, "churn": 100},
        ]

        created_count = 0
        for md in members_data:
            plan = plans[md["plan_idx"]]
            trainer = trainers[md["trainer_idx"]] if md.get("trainer_idx") is not None else None
            join_date = today - timedelta(days=md["joined_ago"])
            start_date = join_date
            expiry = md.get("expiry_override") or (start_date + timedelta(days=plan.duration_months * 30))

            # For expired/cancelled, set expiry in the past
            if md["status"] in ("expired", "cancelled"):
                expiry = today - timedelta(days=random.randint(10, 60))

            # Calculate BMI
            h_m = md["h"] / 100
            bmi = round(md["w"] / (h_m * h_m), 1)

            # Last check-in
            if md["status"] == "active" and md["streak"] > 0:
                last_checkin = timezone.now() - timedelta(hours=random.randint(1, 48))
            else:
                last_checkin = None

            member, c = Member.objects.update_or_create(
                gym=gym, phone=md["phone"],
                defaults=dict(
                    name=md["name"],
                    email=md.get("email"),
                    gender=md["gender"],
                    date_of_birth=md["dob"],
                    goal=md["goal"],
                    experience_level=md["exp"],
                    dietary_preference=md["diet"],
                    height_cm=md["h"],
                    weight_kg=md["w"],
                    body_fat_pct=md["bf"],
                    bmi=bmi,
                    membership_plan=plan,
                    assigned_trainer=trainer,
                    join_date=join_date,
                    membership_start=start_date,
                    membership_expiry=expiry,
                    amount_paid=plan.price,
                    status=md["status"],
                    attendance_streak=md["streak"],
                    last_check_in=last_checkin,
                    churn_risk_score=md["churn"],
                    emergency_contact=f"98291{random.randint(10000, 99999)}",
                ),
            )
            if c:
                created_count += 1

        self.stdout.write(f"  Members: {created_count} created, {len(members_data) - created_count} updated")

        # ── 5. SaaS Subscription Plans ────────────────────────
        saas_plans = [
            {
                "name": "Starter", "slug": "starter", "display_order": 1,
                "price_monthly": 0, "price_yearly": 0, "discount_pct": 0,
                "max_members": 50, "max_ai_queries_per_month": 50,
                "max_staff_accounts": 2, "max_leads": 25,
                "has_lead_management": False, "has_ai_workout": True,
                "has_ai_diet": False, "has_ai_lead_scoring": False,
                "has_whatsapp_integration": False, "has_instagram_content": False,
                "has_analytics_dashboard": False, "has_white_label": False,
                "has_api_access": False,
            },
            {
                "name": "Pro", "slug": "pro", "display_order": 2,
                "price_monthly": 999, "price_yearly": 9990, "discount_pct": 17,
                "max_members": 500, "max_ai_queries_per_month": 500,
                "max_staff_accounts": 10, "max_leads": 200,
                "has_lead_management": True, "has_ai_workout": True,
                "has_ai_diet": True, "has_ai_lead_scoring": True,
                "has_whatsapp_integration": True, "has_instagram_content": False,
                "has_analytics_dashboard": True, "has_white_label": False,
                "has_api_access": False,
            },
            {
                "name": "Enterprise", "slug": "enterprise", "display_order": 3,
                "price_monthly": 4999, "price_yearly": 49990, "discount_pct": 17,
                "max_members": 9999, "max_ai_queries_per_month": 9999,
                "max_staff_accounts": 50, "max_leads": 9999,
                "has_lead_management": True, "has_ai_workout": True,
                "has_ai_diet": True, "has_ai_lead_scoring": True,
                "has_whatsapp_integration": True, "has_instagram_content": True,
                "has_analytics_dashboard": True, "has_white_label": True,
                "has_api_access": True,
            },
        ]
        created_plans = []
        for sp in saas_plans:
            slug = sp.pop("slug")
            plan_obj, c = SubscriptionPlan.objects.update_or_create(slug=slug, defaults=sp)
            created_plans.append(plan_obj)
        self.stdout.write(f"  SaaS Plans: {len(created_plans)} created/updated (Starter, Pro, Enterprise)")

        # Assign Pro plan to Ryan's Gym
        pro_plan = SubscriptionPlan.objects.filter(slug="pro").first()
        if pro_plan:
            gym.subscription_plan = pro_plan
            gym.subscription_status = "active"
            gym.save(update_fields=["subscription_plan", "subscription_status"])
            self.stdout.write(f"  Assigned '{pro_plan.name}' plan to {gym.name}")

        # ── Summary ──────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(f"""
✅  Seed complete!
    Gym:       {gym.name}
    Gym Code:  {gym.gym_code}
    Brand:     {gym.brand_color} / {gym.font_family}
    Owner:     {owner.name} ({owner.phone})
    Trainers:  {', '.join(t.name for t in trainers)}
    Plans:     {len(plans)} (membership) + {len(created_plans)} (SaaS)
    Members:   {len(members_data)} (Active: {sum(1 for m in members_data if m['status']=='active')}, Expired: {sum(1 for m in members_data if m['status']=='expired')}, Frozen: {sum(1 for m in members_data if m['status']=='frozen')}, Cancelled: {sum(1 for m in members_data if m['status']=='cancelled')})
    Logo:      {'✅ Uploaded' if logo_b64 else '❌ Not found'}

    Login: Gym Code {gym.gym_code} → phone 9928122572 → OTP 123456
    URL:   http://127.0.0.1:8099/login/
"""))
