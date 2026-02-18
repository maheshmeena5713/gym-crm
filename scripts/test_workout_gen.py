import os
import django
import sys
import json
from unittest.mock import MagicMock

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.members.models import Member
from apps.gyms.models import Gym
from apps.ai_engine.services import WorkoutPlanService

def test_generation():
    print("Setting up test data...")
    # Get or create gym
    gym = Gym.objects.first()
    if not gym:
        print("No gym found. Creating one.")
        gym = Gym.objects.create(name="Test Gym", city="Test City")

    # Get or create member
    member = Member.objects.filter(gym=gym).first()
    if not member:
        print("No member found. Creating one.")
        member = Member.objects.create(
            gym=gym, 
            name="Test Member", 
            phone="9999999999", 
            join_date="2023-01-01", 
            membership_start="2023-01-01",
            membership_expiry="2024-01-01"
        )
    
    # Mock the internal generation method to avoid API costs/keys
    dummy_plan = {
        "goal": "fat_loss",
        "level": "beginner",
        "duration_weeks": 4,
        "weekly_plan": [
            {
                "day": "Monday", 
                "focus": "Full Body", 
                "exercises": [{"name": "Pushups", "sets": 3, "reps": "10"}]
            }
        ]
    }
    
    # Patch the service method
    print("Mocking AI Service...")
    original_gemini = WorkoutPlanService._generate_with_gemini
    
    # We mock _generate_with_gemini because default provider is likely gemini (from settings logic)
    # If settings.AI_PROVIDER is openai, we might need to mock that too.
    # But for safety we can mock both or check config.
    
    WorkoutPlanService._generate_with_gemini = MagicMock(return_value=(True, dummy_plan))
    
    print(f"Generating workout plan for {member.name}...")
    plan, error = WorkoutPlanService.generate_workout_plan(member, "fat_loss", "beginner", user=None)
    
    if error:
        print(f"FAILED: {error}")
    else:
        print(f"SUCCESS: Plan created (ID: {plan.id})")
        print(f"Title: {plan.title}")
        print(f"Provider: {plan.ai_model_used}")
        print("JSON Data snippet:", str(plan.plan_data)[:100])

    # Restore
    WorkoutPlanService._generate_with_gemini = original_gemini

if __name__ == "__main__":
    test_generation()
