
import os
import sys
import django
import random
from faker import Faker
from django.utils import timezone
from datetime import timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.gyms.models import Gym
from apps.leads.models import Lead

fake = Faker()

def generate_leads():
    print("🚀 Generating 50 Random Leads...")

    gyms = Gym.objects.all()
    if not gyms.exists():
        print("❌ No Gym found. Please create a gym first.")
        return

    for gym in gyms:
        print(f"🏢 Generating leads for gym: {gym.name}")
        generate_leads_for_gym(gym)

def generate_leads_for_gym(gym):

    statuses = [choice[0] for choice in Lead.Status.choices]
    sources = [choice[0] for choice in Lead.Source.choices]
    goals = ["Weight Loss", "Muscle Gain", "General Fitness", "Endurance", "Flexibility"]
    budgets = ["1000-2000", "2000-5000", "5000-10000", "10000+"]

    leads_created = 0

    for _ in range(50):
        try:
            status = random.choice(statuses)
            created_at = fake.date_time_between(start_date='-30d', end_date='now', tzinfo=timezone.get_current_timezone())
            
            lead = Lead(
                gym=gym,
                name=fake.name(),
                phone=fake.numerify(text="9#########"), # Random 10 digit phone
                email=fake.email(),
                source=random.choice(sources),
                status=status,
                goal=random.choice(goals),
                budget_range=random.choice(budgets),
                notes=fake.sentence(),
                ai_score=random.randint(10, 100),
                created_at=created_at
            )

            # Set specific dates based on status
            if status == Lead.Status.CONTACTED:
                lead.last_contacted_date = created_at + timedelta(days=random.randint(1, 5))
            
            if status == Lead.Status.TRIAL_BOOKED:
                lead.trial_date = created_at + timedelta(days=random.randint(1, 7))
                lead.last_contacted_date = created_at

            if status == Lead.Status.CONVERTED:
                lead.converted_at = created_at + timedelta(days=random.randint(5, 15))
                lead.last_contacted_date = created_at
            
            # Manual follow up for some
            if random.choice([True, False]):
                lead.next_followup_date = (timezone.now() + timedelta(days=random.randint(1, 10))).date()

            lead.save()
            
            # Update created_at (save() overrides it usually, so we update it back)
            Lead.objects.filter(id=lead.id).update(created_at=created_at)

            leads_created += 1
            
        except Exception as e:
            print(f"⚠️ Error creating lead: {e}")

    print(f"✅ Successfully created {leads_created} leads for {gym.name}.")

if __name__ == '__main__':
    generate_leads()
