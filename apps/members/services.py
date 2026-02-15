import base64
import json
import logging
from io import BytesIO

import pandas as pd
import requests
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone

from apps.members.models import Member, MembershipPlan
from apps.users.models import GymUser

logger = logging.getLogger('apps.members.services')


class BulkImportService:
    """Service to handle bulk import of members from CSV/Excel."""

    @staticmethod
    def process_file(file_obj, gym):
        """
        Process the uploaded file and create members.
        Returns: (success_count, errors_list)
        """
        try:
            # Read file
            if file_obj.name.endswith('.csv'):
                df = pd.read_csv(file_obj)
            elif file_obj.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_obj)
            else:
                return 0, ['Invalid file format. Please upload CSV or Excel.']

            # Normalize headers
            df.columns = [c.lower().strip().replace(' ', '_') for c in df.columns]

            required_cols = ['name', 'phone']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                return 0, [f'Missing required columns: {", ".join(missing)}']

            success_count = 0
            errors = []

            # Default plan (if not specified or not found) - try finding a 'Monthly' plan or first active plan
            default_plan = MembershipPlan.objects.filter(gym=gym, is_active=True).first()

            for index, row in df.iterrows():
                try:
                    name = str(row.get('name', '')).strip()
                    phone = str(row.get('phone', '')).strip()
                    email = str(row.get('email', '')).strip() if pd.notna(row.get('email')) else ''
                    
                    # Basic validation
                    if not name or not phone:
                        errors.append(f"Row {index+2}: Name and Phone are required.")
                        continue

                    # Check for duplicates (phone) within gym
                    if Member.objects.filter(gym=gym, phone=phone).exists():
                        errors.append(f"Row {index+2}: Member with phone {phone} already exists.")
                        continue
                    
                    # Create member
                    member = Member(
                        gym=gym,
                        name=name,
                        phone=phone,
                        email=email,
                        status='active',
                        membership_start=timezone.now().date(),
                    )

                    # Assign plan if specified
                    plan_name = str(row.get('plan', '')).strip() if pd.notna(row.get('plan')) else ''
                    if plan_name:
                        plan = MembershipPlan.objects.filter(gym=gym, name__iexact=plan_name).first()
                        if plan:
                            member.membership_plan = plan
                            # Calculate expiry based on plan duration
                            member.membership_expiry = member.membership_start + timezone.timedelta(days=plan.duration_days)
                        else:
                             # Fallback to default if plan name doesn't match
                            if default_plan:
                                member.membership_plan = default_plan
                                member.membership_expiry = member.membership_start + timezone.timedelta(days=default_plan.duration_days)
                    elif default_plan:
                        member.membership_plan = default_plan
                        member.membership_expiry = member.membership_start + timezone.timedelta(days=default_plan.duration_days)

                    member.save()
                    success_count += 1

                except Exception as e:
                    errors.append(f"Row {index+2}: {str(e)}")

            return success_count, errors

        except Exception as e:
            logger.error(f"Bulk import failed: {e}")
            return 0, [f"File processing failed: {str(e)}"]


class AIScanService:
    """Service to extract member details from an image using OpenAI Vision API."""

    @staticmethod
    def scan_card(image_file):
        """
        Sends image to OpenAI and extracts JSON data.
        Returns: (success, data_dict_or_error_message)
        """
        provider = getattr(settings, 'AI_PROVIDER', 'gemini').lower()
        
        # Auto-detect if provider not explicitly set or key missing
        if provider == 'gemini' and not settings.GEMINI_API_KEY:
            if settings.OPENAI_API_KEY:
                provider = 'openai'
        elif provider == 'openai' and not settings.OPENAI_API_KEY:
             if settings.GEMINI_API_KEY:
                provider = 'gemini'

        if provider == 'gemini':
            if not settings.GEMINI_API_KEY:
                 return False, "Gemini API key not configured."
            return AIScanService._scan_with_gemini(image_file)
        else:
            if not settings.OPENAI_API_KEY:
                 return False, "OpenAI API key not configured."
            return AIScanService._scan_with_openai(image_file)

    @staticmethod
    def _scan_with_openai(image_file):
        try:
            # Encode image to base64
            image_content = image_file.read()
            base64_image = base64.b64encode(image_content).decode('utf-8')
            
            # Reset file pointer for subsequent uses if any
            image_file.seek(0)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
            }

            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract 'Name', 'Phone', 'Email', and 'Plan' from this image. It could be a membership card or a full application form. for 'Plan', look for keywords like 'Monthly', 'Quarterly', 'Yearly', 'Annual'. If not found, leave empty. Return JSON with keys: 'name', 'phone', 'email', 'plan'. Ensure phone contains only digits."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500,
                "response_format": {"type": "json_object"} 
            }

            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Parse JSON response
            data = json.loads(content)
            
            return True, data

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API error: {e}")
            return False, "Failed to connect to AI service."
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response: {content}")
            return False, "AI returned invalid data format."
        except Exception as e:
            logger.error(f"AI Scan error: {e}")
            return False, f"Scan failed: {str(e)}"

    @staticmethod
    def _scan_with_gemini(image_file):
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=settings.GEMINI_API_KEY)

            # Read image data
            image_data = image_file.read()
            image_file.seek(0) # Reset pointer
            
            # Determine mime type (basic check or default to jpeg)
            mime_type = "image/jpeg"
            if image_file.name.lower().endswith('.png'):
                mime_type = "image/png"
            elif image_file.name.lower().endswith('.webp'):
                mime_type = "image/webp"

            prompt = "Extract 'Name', 'Phone', 'Email', and 'Plan' from this image. Return just the JSON object with keys: 'name', 'phone', 'email', 'plan'. No markdown."

            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_data, mime_type=mime_type)
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            text = response.text
            data = json.loads(text)
            return True, data

        except Exception as e:
            logger.error(f"Gemini Scan error: {e}")
            return False, f"Gemini Scan failed: {str(e)}"
