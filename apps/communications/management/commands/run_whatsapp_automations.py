import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from apps.gyms.models import Gym
from apps.members.models import Member
from apps.communications.models import WhatsAppAutomation, WhatsAppMessageLog
from apps.communications.services import WhatsAppService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Runs daily WhatsApp automations for Pro plan gyms'

    def handle(self, *args, **options):
        self.stdout.write("Starting WhatsApp Automations...")
        
        # 1. Fetch gyms that have the integration flag enabled (Pro+)
        gyms = Gym.objects.filter(
            is_active=True,
            subscription_plan__has_whatsapp_integration=True
        )
        
        service = WhatsAppService()
        today = timezone.now().date()
        
        for gym in gyms:
            automations = WhatsAppAutomation.objects.filter(gym=gym, enabled=True)
            if not automations.exists():
                continue
                
            self.stdout.write(f"Processing Gym: {gym.name}")
            
            for auto in automations:
                # Target date for time-based triggers
                days = auto.days_before or 0
                
                # Fetch members based on automation type
                members = self._get_target_members(gym, auto.type, days, today)
                
                if not members:
                    continue
                    
                self.stdout.write(f"  [{auto.get_type_display()}] Found {members.count()} members")
                
                for member in members:
                    if not member.phone:
                        continue
                        
                    # Prevent duplicate messages for the exact same automation type today
                    # We log raw messages to WhatsAppMessageLog
                    already_sent = WhatsAppMessageLog.objects.filter(
                        gym=gym,
                        member=member,
                        created_at__date=today,
                        # A simple way to track is by exact message body matches or checking the daily log
                        # Ideally, we add automation_type to the log, but since we didn't, 
                        # we can just prevent ANY automated message of the SAME type today by looking for recently sent logs.
                        # Wait, we can't easily distinguish manual vs auto without a flag. Let's just prevent multiple messages per member per day 
                        # to be extremely safe, OR just check if they got a message today containing part of the template.
                    ).exists()
                    
                    if already_sent:
                        self.stdout.write(f"    Skipping {member.name} (already messaged today)")
                        continue
                        
                    # Build Message
                    message = self._render_template(auto.template, gym, member)
                    
                    # Send
                    response = service.send_whatsapp_message(
                        phone=member.phone, 
                        message=message, 
                        gym=gym, 
                        member=member
                    )
                    
                    if response.get('status') == 'success':
                        self.stdout.write(self.style.SUCCESS(f"    Sent to {member.name} - {member.phone}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"    Failed for {member.name} - {response.get('error')}"))
                
                # Update automation last run
                auto.last_run_at = timezone.now()
                auto.save()

        self.stdout.write("Finished WhatsApp Automations.")

    def _get_target_members(self, gym, auto_type, days_before, today):
        """Fetch members matching the rules"""
        target_date = today + timedelta(days=days_before)
        target_date_past = today - timedelta(days=days_before)
        
        qs = Member.objects.filter(gym=gym, is_deleted=False)
        
        if auto_type == WhatsAppAutomation.AutomationType.EXPIRY_REMINDER:
            # e.g., membership expires in exactly X days
            return qs.filter(status='active', membership_expiry=target_date)
            
        elif auto_type == WhatsAppAutomation.AutomationType.PAYMENT_PENDING:
            # Members who are active but haven't paid full amount, or whose end date passed but haven't renewed
            # Simple assumption: membership expired exactly X days ago
            return qs.filter(membership_expiry=target_date_past)
            
        elif auto_type == WhatsAppAutomation.AutomationType.INACTIVE_REMINDER:
            # Members with last check-in exactly X days ago
            return qs.filter(status='active', last_check_in__date=target_date_past)
            
        elif auto_type == WhatsAppAutomation.AutomationType.BIRTHDAY:
            # Members whose birthday is today (ignoring year)
            return qs.filter(
                status='active',
                date_of_birth__day=today.day,
                date_of_birth__month=today.month
            )
            
        return Member.objects.none()

    def _render_template(self, template, gym, member):
        """Simple text replacement for the template"""
        text = template
        text = text.replace('{{name}}', member.name or 'Member')
        text = text.replace('{{gym_name}}', gym.name or 'Gym')
        
        if '{{expiry_date}}' in text and member.membership_expiry:
            text = text.replace('{{expiry_date}}', member.membership_expiry.strftime('%d %b %Y'))
        else:
            text = text.replace('{{expiry_date}}', 'Soon')
            
        if '{{plan_name}}' in text and member.membership_plan:
            text = text.replace('{{plan_name}}', member.membership_plan.name)
        else:
            text = text.replace('{{plan_name}}', 'Your Plan')
            
        return text
