import os
import django
import sys

# Setup Django
# scrips/assign_plan.py -> scripts -> gym_crm
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.gyms.models import Gym
from apps.billing.models import SubscriptionPlan

def assign_plan(gym_code):
    try:
        gym = Gym.objects.get(gym_code=gym_code)
        
        # Get or create a plan that has AI features
        plan, created = SubscriptionPlan.objects.get_or_create(
            slug='pro',
            defaults={
                'name': 'Pro Plan',
                'price_monthly': 2999,
                'price_yearly': 29990,
                'has_ai_workout': True,
                'has_ai_diet': True,
                'has_lead_management': True,
                'max_members': 500,
                'max_ai_queries_per_month': 500,
                # Add explicit defaults for fields that might not have them in older migrations
                'is_active': True,
                'display_order': 1
            }
        )
        
        if created:
            print(f"Created new plan: {plan.name}")
        else:
            # Ensure AI features are enabled on existing plan
            updated = False
            if not plan.has_ai_workout:
                plan.has_ai_workout = True
                updated = True
            
            # Ensure other fields are set correctly if needed
            if updated:
                plan.save()
                print(f"Updated plan {plan.name} to include AI Workout.")
            else:
                 print(f"Plan {plan.name} already has AI Workout enabled.")

        gym.subscription_plan = plan
        gym.subscription_status = 'active'
        gym.save()
        
        print(f"SUCCESS: Assigned '{plan.name}' to {gym.name} ({gym.gym_code})")
            
    except Gym.DoesNotExist:
        print(f"Gym {gym_code} not found.")

if __name__ == "__main__":
    assign_plan("GYM0441925")
