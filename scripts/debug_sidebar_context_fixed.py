import os
import sys

# Setup Django first
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from apps.users.models import GymUser
from apps.gyms.models import Gym
from apps.billing.models import SubscriptionPlan
from apps.ai_engine.views import DietPlanListView
from apps.frontend.context_processors import subscription_context

def debug_context():
    # 1. Setup Data - Use a random suffix to avoid collision
    import random
    suffix = random.randint(1000, 9999)
    email = f"debug_ai_{suffix}@example.com"
    
    plan, _ = SubscriptionPlan.objects.get_or_create(
        slug='pro', 
        defaults={'name': 'Pro Plan', 'has_ai_diet': True, 'has_ai_workout': True}
    )
    
    # Check if gym exists first
    gym = Gym.objects.filter(gym_code="DEBUG_AI_001").first()
    if not gym:
        gym = Gym.objects.create(name="Debug AI Gym", gym_code="DEBUG_AI_001", subscription_plan=plan, email=email)
    
    # Check if user exists
    user = GymUser.objects.filter(username="debug_owner_ai").first()
    if not user:
        user = GymUser.objects.create(
            username="debug_owner_ai",
            email=email, 
            role='owner', 
            gym=gym
        )
    
    print(f"User: {user.username}, Role: {user.role}")
    print(f"Gym: {gym.name}, Plan: {gym.subscription_plan.name}")
    print(f"Plan has AI Diet: {gym.subscription_plan.has_ai_diet}")

    # 2. Create Request
    factory = RequestFactory()
    request = factory.get('/dashboard/ai/diet/')
    request.user = user
    
    # Add session
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()

    # 3. Simulate Context Processor manually
    ctx = subscription_context(request)
    print("\n--- Context Processor Output ---")
    plan_ctx = ctx.get('plan')
    print(f"Plan in Context: {plan_ctx}")
    if plan_ctx:
        print(f"  - has_ai_diet: {plan_ctx.has_ai_diet}")
        print(f"  - has_ai_workout: {plan_ctx.has_ai_workout}")

    # 4. Cleanup
    user.delete()
    gym.delete()

if __name__ == "__main__":
    debug_context()
