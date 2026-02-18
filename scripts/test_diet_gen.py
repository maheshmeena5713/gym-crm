import os
import django
import sys
from unittest.mock import patch, MagicMock

# Setup Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.members.models import Member
from apps.gyms.models import Gym
from apps.fitness.models import DietPlan
from apps.ai_engine.services_diet import DietPlanService

def test_diet_generation():
    print("--- Starting Diet Gen Test ---")
    
    # 1. Setup Data
    gym, _ = Gym.objects.get_or_create(name="Test Gym", gym_code="TESTGYM001")
    member, _ = Member.objects.get_or_create(
        gym=gym, 
        phone="9998887776",
        defaults={'name': 'Test User', 'join_date': '2023-01-01', 'membership_start': '2023-01-01', 'membership_expiry': '2024-01-01'}
    )
    
    print(f"Member: {member.name}")

    # 2. Mock AI Response
    mock_response = {
        "calories": 2000,
        "preference": "veg",
        "budget": "medium",
        "macro_split": {"protein": "100g", "carbs": "250g", "fats": "60g"},
        "days": [
            {
                "day": "Monday",
                "meals": [
                    {"meal": "Breakfast", "name": "Poha", "items": "1 plate Poha, 1 tea", "calories": 300},
                    {"meal": "Lunch", "name": "Roti Sabzi", "items": "2 Roti, 1 bowl Dal", "calories": 500}
                ]
            }
        ],
        "grocery_list": ["Poha", "Onion", "Potatoes"]
    }

    # 3. Call Service with Mock
    # Default provider is Gemini, so we mock that.
    with patch('apps.ai_engine.services_diet.DietPlanService._generate_with_gemini') as mock_ai:
        mock_ai.return_value = (True, mock_response)
        
        plan, error = DietPlanService.generate_diet_plan(member, 2000, 'veg', 'medium')
        
        if error:
            print(f"FAILED: {error}")
        else:
            print(f"SUCCESS: Generated Plan '{plan.title}' (ID: {plan.id})")
            print(f"Calories: {plan.daily_calories}")
            # Verify structure
            first_day = plan.plan_data.get('days', [])[0] if 'days' in plan.plan_data else plan.plan_data['weekly_plan'][0]
            print(f"First Day: {first_day['day']}")
            
            # Verify DB
            saved_plan = DietPlan.objects.get(id=plan.id)
            assert saved_plan.daily_calories == 2000
            assert saved_plan.dietary_preference == 'veg'
            print("DB Verification Passed")

if __name__ == "__main__":
    test_diet_generation()
