import logging
import requests
from django.conf import settings
from django.utils import timezone
from .models import WhatsAppMessage

logger = logging.getLogger(__name__)

class WhatsAppService:
    """
    Service to handle WhatsApp Business API interactions.
    Supports 'Simulation Mode' for testing without credentials.
    """

    def __init__(self):
        self.api_url = getattr(settings, 'META_WHATSAPP_API_URL', '')
        self.access_token = getattr(settings, 'META_WHATSAPP_ACCESS_TOKEN', '')
        self.phone_number_id = getattr(settings, 'META_WHATSAPP_PHONE_NUMBER_ID', '')
        self.simulation_mode = getattr(settings, 'WHATSAPP_SIMULATION_MODE', True)

    def send_template_message(self, recipient_phone, template_name, language_code='en', components=None, gym=None, member=None, message_type='custom'):
        """
        Generic method to send a template message.
        """
        # Format phone number: ensure it has 91 prefix if 10 digits
        formatted_phone = self._format_phone(recipient_phone)

        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components or []
            }
        }

        if self.simulation_mode:
            return self._simulate_send(payload, gym, member, message_type)
        else:
            return self._execute_send(payload, gym, member, message_type)

    def _format_phone(self, phone):
        """
        Ensure phone number is in E.164 format (roughly).
        For India, add 91 if length is 10.
        """
        if not phone:
            return ""
        # Remove spaces, dashes, pluses
        clean_phone = ''.join(filter(str.isdigit, str(phone)))
        
        if len(clean_phone) == 10:
            return f"91{clean_phone}"
        return clean_phone

    def _simulate_send(self, payload, gym, member, message_type):
        """
        Logs the message as sent without actually hitting the API.
        """
        logger.info(f"SIMULATION: Sending WhatsApp to {payload['to']} | Template: {payload['template']['name']}")
        
        # Create log entry
        msg = WhatsAppMessage.objects.create(
            gym=gym,
            member=member,
            direction=WhatsAppMessage.Direction.OUTBOUND,
            message_type=message_type,
            recipient_phone=payload['to'],
            content=f"Template: {payload['template']['name']} | Data: {payload}",
            template_name=payload['template']['name'],
            status=WhatsAppMessage.DeliveryStatus.SENT,
            wa_message_id=f"sim_{timezone.now().timestamp()}",
            cost_inr=0.00 # No cost in simulation
        )
        return {"status": "success", "message_id": msg.wa_message_id, "simulation": True}

    def _execute_send(self, payload, gym, member, message_type):
        """
        Actually calls the Meta API.
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        url = f"{self.api_url}/{self.phone_number_id}/messages"

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract Message ID
            wa_id = data.get('messages', [{}])[0].get('id')

            # Log success
            WhatsAppMessage.objects.create(
                gym=gym,
                member=member,
                direction=WhatsAppMessage.Direction.OUTBOUND,
                message_type=message_type,
                recipient_phone=payload['to'],
                content=f"Template: {payload['template']['name']}",
                template_name=payload['template']['name'],
                status=WhatsAppMessage.DeliveryStatus.SENT,
                wa_message_id=wa_id,
                # Simple cost estimation logic (approx 0.80 INR per conversation)
                cost_inr=0.80 
            )
            return {"status": "success", "data": data}

        except requests.exceptions.RequestException as e:
            logger.error(f"WhatsApp API Error: {str(e)}")
            if e.response is not None:
                logger.error(f"Response: {e.response.text}")
            
            # Log failure
            WhatsAppMessage.objects.create(
                gym=gym,
                member=member,
                direction=WhatsAppMessage.Direction.OUTBOUND,
                message_type=message_type,
                recipient_phone=payload['to'],
                content=f"Template: {payload['template']['name']}",
                template_name=payload['template']['name'],
                status=WhatsAppMessage.DeliveryStatus.FAILED,
                error_message=f"{str(e)} | Response: {e.response.text if e.response else 'No Response'}"
            )
            return {"status": "failed", "error": str(e)}

    # ── High Level Methods ────────────────────────────────────────

    def send_welcome_message(self, member):
        """
        Sends welcome message to a new member.
        """
        if not member.phone or not member.gym:
            return None
            
        components = [
            {
                "type": "header",
                "parameters": [
                    {"type": "text", "parameter_name": "gym_name", "text": member.gym.name}
                ]
            },
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "parameter_name": "member_name", "text": member.name},
                    {"type": "text", "parameter_name": "gym_name", "text": member.gym.name},
                    {"type": "text", "parameter_name": "gym_team", "text": f"{member.gym.name} Team"},
                ]
            }
        ]
        
        return self.send_template_message(
            recipient_phone=member.phone,
            template_name="gym_welcome_message", 
            language_code="en_IN",
            components=components,
            gym=member.gym,
            member=member,
            message_type=WhatsAppMessage.MessageType.WELCOME
        )

    def send_renewal_reminder(self, member):
        """
        Sends renewal reminder (3 days before).
        """
        if not member.phone or not member.gym:
            return None
        
        days_left = (member.membership_expiry - timezone.now().date()).days if member.membership_expiry else 0
        
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "parameter_name": "member_name", "text": member.name},
                    {"type": "text", "parameter_name": "gym_name", "text": member.gym.name},
                    {"type": "text", "parameter_name": "no_of_days", "text": str(days_left)},
                    {"type": "text", "parameter_name": "payment_link", "text": "https://pay.gym.in/renew"}, # Placeholder link
                    {"type": "text", "parameter_name": "gym_team", "text": f"{member.gym.name} Team"},
                ]
            }
        ]

        return self.send_template_message(
            recipient_phone=member.phone,
            template_name="gym_renewal_reminder",
            language_code="en",
            components=components,
            gym=member.gym,
            member=member,
            message_type=WhatsAppMessage.MessageType.EXPIRY_REMINDER
        )

    def send_daily_quote(self, member, quote):
        """
        Sends daily motivational quote.
        """
        if not member.phone or not member.gym:
            return None

        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "parameter_name": "member_name", "text": member.name},
                    {"type": "text", "parameter_name": "gym_name", "text": member.gym.name},
                    {"type": "text", "parameter_name": "quote", "text": quote.content},
                    {"type": "text", "parameter_name": "gym_team", "text": f"{member.gym.name} Team"},
                ]
            }
        ]

        return self.send_template_message(
            recipient_phone=member.phone,
            template_name="gym_daily_motivation",
            language_code="en",
            components=components,
            gym=member.gym,
            member=member,
            message_type=WhatsAppMessage.MessageType.PROMOTION
        )

    def send_whatsapp_message(self, phone, message, gym=None, member=None):
        """
        Sends a raw WhatsApp message (no template constraints) or handles
        custom Meta API text messaging. Logs the result in WhatsAppMessageLog.
        This provides a swappable interface (e.g. Meta API, Twilio). 
        """
        formatted_phone = self._format_phone(phone)
        
        # We need the WhatsAppMessageLog model
        from apps.communications.models import WhatsAppMessageLog

        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": "text",
            "text": {
                "body": message
            }
        }

        if self.simulation_mode:
            logger.info(f"SIMULATION: Sending Raw WA to {formatted_phone}: {message[:30]}...")
            msg_log = WhatsAppMessageLog.objects.create(
                gym=gym,
                member=member,
                phone=formatted_phone,
                message=message,
                status=WhatsAppMessageLog.DeliveryStatus.SENT,
                response='{"simulation": true, "status": "success"}'
            )
            return {"status": "success", "message_id": f"sim_{msg_log.id}"}
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        url = f"{self.api_url}/{self.phone_number_id}/messages"

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            WhatsAppMessageLog.objects.create(
                gym=gym,
                member=member,
                phone=formatted_phone,
                message=message,
                status=WhatsAppMessageLog.DeliveryStatus.SENT,
                response=response.text
            )
            return {"status": "success", "data": data}

        except requests.exceptions.RequestException as e:
            error_response = e.response.text if e.response else str(e)
            logger.error(f"WhatsApp Raw Error: {error_response}")
            WhatsAppMessageLog.objects.create(
                gym=gym,
                member=member,
                phone=formatted_phone,
                message=message,
                status=WhatsAppMessageLog.DeliveryStatus.FAILED,
                response=error_response
            )
            return {"status": "failed", "error": str(e)}
