from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.members.models import Member
from apps.communications.models import Quote, WhatsAppMessage
from apps.communications.services import WhatsAppService
import random

class Command(BaseCommand):
    help = 'Sends daily motivational quote to all active members'

    def handle(self, *args, **options):
        # 1. Get a random active quote that hasn't been sent recently
        # For simplicity in this MVP, we just pick a random active one
        quotes = Quote.objects.filter(is_active=True)
        if not quotes.exists():
            self.stdout.write(self.style.WARNING("No active quotes found."))
            return

        quote = random.choice(quotes)
        
        # 2. Get all active members
        active_members = Member.objects.filter(status='active', is_deleted=False)
        
        if not active_members.exists():
             self.stdout.write(self.style.WARNING("No active members found."))
             return

        service = WhatsAppService()
        count = 0
        
        self.stdout.write(f"Sending quote: '{quote.content}' to {active_members.count()} members.")

        # 3. Send to each member
        for member in active_members:
            if not member.phone:
                continue

            # Avoid spamming: Check if we already sent a quote today to this member
            already_sent = WhatsAppMessage.objects.filter(
                member=member,
                message_type=WhatsAppMessage.MessageType.PROMOTION,
                created_at__date=timezone.now().date()
            ).exists()

            if already_sent:
                 continue

            response = service.send_daily_quote(member, quote)
            if response and response.get('status') == 'success':
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Sent quote to {member.name}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send to {member.name}'))

        # Update last sent date for the quote
        quote.last_sent = timezone.now().date()
        quote.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully sent {count} daily quotes'))
