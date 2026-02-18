import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.gyms.models import Gym
from apps.billing.models import SubscriptionPlan

def debug_gym_plan(gym_code):
    try:
        gym = Gym.objects.get(gym_code=gym_code)
        print(f"Gym: {gym.name} ({gym.gym_code})")
        print(f"Status: {gym.subscription_status}")
        
        plan = gym.subscription_plan
        if plan:
            print(f"Plan: {plan.name}")
            print(f"Has AI Workout: {getattr(plan, 'has_ai_workout', 'N/A')}")
            print(f"Has AI Diet: {getattr(plan, 'has_ai_diet', 'N/A')}")
        else:
            print("Plan: None")
            
    except Gym.DoesNotExist:
        print(f"Gym {gym_code} not found.")

if __name__ == "__main__":
    debug_gym_plan("GYM0441925")
