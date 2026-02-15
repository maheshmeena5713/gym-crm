from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.members.models import Member
from apps.communications.services import WhatsAppService

class Command(BaseCommand):
    help = 'Sends WhatsApp reminders to members expiring in 3 days'

    def handle(self, *args, **options):
        # Calculate target date: Today + 3 days
        today = timezone.now().date()
        target_date = today + timezone.timedelta(days=3)

        expiring_members = Member.objects.filter(
            membership_expiry=target_date,
            status='active',
            is_deleted=False
        )

        if not expiring_members.exists():
            self.stdout.write(self.style.WARNING(f'No memberships expiring on {target_date}'))
            return

        service = WhatsAppService()
        count = 0
        
        self.stdout.write(f"Found {expiring_members.count()} members expiring on {target_date}")

        for member in expiring_members:
            if not member.phone:
                continue
                
            response = service.send_renewal_reminder(member)
            if response and response.get('status') == 'success':
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Sent reminder to {member.name} ({member.phone})'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send to {member.name}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully sent {count} renewal reminders'))
