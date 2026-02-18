import json
import logging
from django.conf import settings
from django.utils import timezone
from apps.fitness.models import WorkoutPlan
from apps.ai_engine.models import AIUsageLog
import requests 

logger = logging.getLogger('apps.ai_engine.services')

class WorkoutPlanService:
    @staticmethod
    def generate_workout_plan(member, goal, level, user=None):
        """
        Generates a workout plan using AI (Gemini or OpenAI).
        """
        provider = getattr(settings, 'AI_PROVIDER', 'gemini').lower()
        
        # Auto-switch if key missing
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
        
        # Logic to map 'level' to 'difficulty' if needed
        # Assuming level matches values in WorkoutPlan.Difficulty or is passed as string
        
        usage_log = AIUsageLog(
            gym=member.gym,
            user=member.assigned_trainer if member.assigned_trainer else None, 
            feature=AIUsageLog.Feature.WORKOUT_PLAN,
        )

        try:
            if provider == 'gemini':
                model_used = 'gemini-2.0-flash'
                success, plan_data = WorkoutPlanService._generate_with_gemini(member, goal, level)
            else:
                model_used = 'gpt-4o-mini'
                success, plan_data = WorkoutPlanService._generate_with_openai(member, goal, level)

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

            # Create WorkoutPlan (using apps.fitness.models.WorkoutPlan)
            plan = WorkoutPlan.objects.create(
                gym=member.gym,
                member=member,
                created_by=user,
                goal=goal,
                difficulty=level, # Mapping 'level' to 'difficulty'
                plan_data=plan_data, # Mapping 'plan_json' to 'plan_data'
                ai_model_used=model_used,
                title=f"{goal.replace('_', ' ').title()} Plan",
                duration_weeks=4 
            )
            return plan, None

        except Exception as e:
            logger.error(f"Workout Generation Error: {e}")
            usage_log.error_message = str(e)
            usage_log.was_successful = False
            usage_log.save()
            return None, str(e)

    @staticmethod
    def _construct_prompt(member, goal, level):
        return f"""
        Create a 4-week structured workout plan for a {member.get_gender_display()} gym member.
        Profile:
        - Age: {timezone.now().year - member.date_of_birth.year if member.date_of_birth else 'Unknown'}
        - Weight: {member.weight_kg}kg, Height: {member.height_cm}cm
        - Goal: {goal}
        - Experience Level: {level}
        - Medical Conditions: {member.medical_conditions or 'None'}
        - Days per week: 4-5

        Return purely JSON in this structure:
        {{
          "goal": "{goal}",
          "level": "{level}",
          "duration_weeks": 4,
          "weekly_plan": [
            {{
              "day": "Monday",
              "focus": "Chest + Triceps",
              "exercises": [
                {{
                  "name": "Bench Press",
                  "sets": 4,
                  "reps": "10-12",
                  "notes": "Focus on form"
                }}
              ]
            }}
          ]
        }}
        """

    @staticmethod
    def _generate_with_openai(member, goal, level):
        try:
            prompt = WorkoutPlanService._construct_prompt(member, goal, level)
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are an expert fitness trainer AI."},
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
    def _generate_with_gemini(member, goal, level):
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = WorkoutPlanService._construct_prompt(member, goal, level)
            
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
