import json
import logging
from django.conf import settings
from django.utils import timezone
from apps.fitness.models import DietPlan
from apps.activity_logs.models import AIUsageLog
import requests 

logger = logging.getLogger('apps.ai_engine.services')

class DietPlanService:
    @staticmethod
    def generate_diet_plan(gym, calories, preference, budget, member=None, custom_requirements=None, user=None):
        """
        Generates an Indian Diet Plan using AI.
        """
        provider = getattr(settings, 'AI_PROVIDER', 'gemini').lower()
        
        # Auto-switch logic (same as workout)
        if provider == 'gemini' and not settings.GEMINI_API_KEY:
            if settings.OPENAI_API_KEY:
                provider = 'openai'
        elif provider == 'openai' and not settings.OPENAI_API_KEY:
             if settings.GEMINI_API_KEY:
                provider = 'gemini'

        start_time = timezone.now()
        success = False
        error_message = ""
        plan_data = {}
        model_used = ""
        
        usage_log = AIUsageLog(
            gym=gym,
            user=user, 
            feature=AIUsageLog.Feature.DIET_PLAN,
        )

        try:
            if provider == 'gemini':
                model_used = 'gemini-2.0-flash'
                success, plan_data = DietPlanService._generate_with_gemini(calories, preference, budget, member, custom_requirements)
            else:
                model_used = 'gpt-4o-mini'
                success, plan_data = DietPlanService._generate_with_openai(calories, preference, budget, member, custom_requirements)

            if not success:
                error_message = str(plan_data)
                usage_log.error_message = error_message
                usage_log.was_successful = False
                usage_log.save()
                return None, error_message

            # Save Benchmark
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds() * 1000
            
            usage_log.model_used = model_used
            usage_log.response_time_ms = int(duration)
            usage_log.was_successful = True
            usage_log.save()

            # Create DietPlan
            # We store budget in plan_data as model doesn't have it
            if 'meta' not in plan_data:
                plan_data['meta'] = {}
            plan_data['meta']['budget'] = budget

            goal = member.goal if member else "General Health"
            plan = DietPlan.objects.create(
                gym=gym,
                member=member,
                created_by=user,
                title=f"{preference.title()} Indian Diet ({calories} kcal)",
                goal=goal,
                dietary_preference=preference,
                daily_calories=calories,
                custom_requirements=custom_requirements,
                plan_data=plan_data,
                ai_model_used=model_used,
            )
            return plan, None

        except Exception as e:
            logger.error(f"Diet Generation Error: {e}")
            usage_log.error_message = str(e)
            usage_log.was_successful = False
            usage_log.save()
            return None, str(e)

    @staticmethod
    def _construct_prompt(calories, preference, budget, member=None, custom_requirements=None):
        profile_str = ""
        if member:
            profile_str = f"""
        Profile:
        - Weight: {member.weight_kg}kg
        - Goal: {member.get_goal_display()}
        - Medical: {member.medical_conditions or 'None'}"""
            
        reqs_str = f"\n        - Custom Requirements: {custom_requirements}" if custom_requirements else ""

        return f"""
        Create a detailed weekly Indian Diet Plan.{profile_str}
        - Calorie Target: {calories} kcal/day
        - Preference: {preference} (Strictly Indian Cuisine)
        - Budget: {budget} (Low=Home simplified, High=Premium ingredients){reqs_str}

        Requirements:
        1. Foods must be common Indian items (Roti, Dal, Sabzi, Rice, Poha, Idli, Paneer, Chicken Curry etc).
        2. Macros should be balanced for the goal.
        3. Include a grocery list.

        Return strictly JSON:
        {{
          "calories": {calories},
          "preference": "{preference}",
          "budget": "{budget}",
          "macro_split": {{"protein": "XXg", "carbs": "XXg", "fats": "XXg"}},
          "days": [
            {{
              "day": "Monday",
              "meals": [
                {{
                  "meal": "Breakfast",
                  "name": "Paneer Paratha with Curd",
                  "items": "2 Parathas, 100g Curd",
                  "calories": 400
                }},
                {{
                  "meal": "Lunch",
                  "name": "Dal Fry, Rice, Salad",
                  "items": "1 bowl Dal, 150g Rice, Cucumber Salad",
                  "calories": 600
                }}
                ... (Snack, Dinner)
              ]
            }}
             ... (Just give 1 typical day structure or 7 distinct days if possible within token limits, let's ask for a 'Sample Day' repeated or 7 days if concise)
             Actually, please provide a '7-Day Plan' but referencing repeated meals is okay to save tokens.
          ],
          "grocery_list": ["Atta", "Rice", "Toor Dal", ...]
        }}
        """

    @staticmethod
    def _generate_with_openai(calories, preference, budget, member=None, custom_requirements=None):
        try:
            prompt = DietPlanService._construct_prompt(calories, preference, budget, member, custom_requirements)
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are an expert Indian nutritionist AI."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            content = data['choices'][0]['message']['content']
            parsed = json.loads(content)
            return True, parsed
            
        except Exception as e:
            return False, str(e)

    @staticmethod
    def _generate_with_gemini(calories, preference, budget, member=None, custom_requirements=None):
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = DietPlanService._construct_prompt(calories, preference, budget, member, custom_requirements)
            
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            parsed = json.loads(response.text)
            return True, parsed
            
        except Exception as e:
            return False, str(e)
