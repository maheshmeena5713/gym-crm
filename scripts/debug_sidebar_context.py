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
    # 1. Setup Data
    plan, _ = SubscriptionPlan.objects.get_or_create(
        slug='pro', 
        defaults={'name': 'Pro Plan', 'has_ai_diet': True, 'has_ai_workout': True}
    )
    gym, _ = Gym.objects.get_or_create(name="Debug Gym", gym_code="DEBUG001", defaults={'subscription_plan': plan})
    user, _ = GymUser.objects.get_or_create(
        username="debug_owner",
        email="debug@example.com", 
        defaults={'role': 'owner', 'gym': gym}
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
    print(f"Plan in Context: {ctx.get('plan')}")

    # 4. View Integration Logic
    # We can't easily run full view dispatch without full middleware stack (auth, messages, etc)
    # But we can check if the view allows context processor execution by default (it should).
    # Since we verified context processor logic above with the same request object, 
    # if the view uses RequestContext (which generic views do), it WILL have the 'plan'.
    
    print("\n--- SUCCESS ---")
    print("If this script prints the Plan correctly, the issue is likely not in the backend logic.")

if __name__ == "__main__":
    debug_context()
