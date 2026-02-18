import logging
from django.utils import timezone
from django.db.models import Count, Q
from django.db import transaction
from apps.leads.models import Lead
from apps.members.models import Member

logger = logging.getLogger('apps.leads.services')

class LeadService:
    @staticmethod
    def convert_lead(lead, converted_by=None):
        """
        Converts a Lead into a Member.
        - Creates Member record (if phone unique)
        - Updates Lead status to 'converted'
        - Sets timestamps
        """
        if lead.status == Lead.Status.CONVERTED:
            return None, "Lead is already converted."

        gym = lead.gym

        # Check if member already exists with this phone in this gym
        if Member.objects.filter(gym=gym, phone=lead.phone).exists():
            return None, "Member with this phone number already exists."

        try:
            with transaction.atomic():
                # Create Member
                member = Member.objects.create(
                    gym=gym,
                    name=lead.name,
                    phone=lead.phone,
                    email=lead.email,
                    # Auto-fill fields based on Lead info
                    goal=lead.goal if lead.goal else Member.Goal.GENERAL_FITNESS,
                    # Defaults
                    status=Member.Status.ACTIVE,
                    join_date=timezone.now().date(),
                    membership_start=timezone.now().date(),
                    membership_expiry=timezone.now().date() + timezone.timedelta(days=30), # Default 30 days, manual update needed
                )

                # Update Lead
                lead.status = Lead.Status.CONVERTED
                lead.converted_at = timezone.now()
                lead.converted_member = member
                lead.save()
                
                logger.info(f"Lead {lead.id} converted to Member {member.id} by {converted_by}")
                return member, None

        except Exception as e:
            logger.error(f"Error converting lead {lead.id}: {str(e)}")
            return None, f"Conversion failed: {str(e)}"

    @staticmethod
    def bulk_convert(lead_ids, user):
        """
        Convert multiple leads to members.
        Returns a summary of successes and failures.
        """
        results = {
            'converted': [],
            'failed': []
        }
        
        # Filter leads by user's gym to ensure permission
        leads = Lead.objects.filter(id__in=lead_ids, gym=user.gym)
        
        for lead in leads:
            member, error = LeadService.convert_lead(lead, converted_by=user)
            if member:
                results['converted'].append({'id': lead.id, 'name': lead.name, 'member_id': member.id})
            else:
                results['failed'].append({'id': lead.id, 'name': lead.name, 'error': error})
                
        return results

    @staticmethod
    def get_lead_summary(gym):
        """
        Returns lead statistics for the gym.
        - New this month
        - Active Trials
        - Converted (Total & Monthly)
        - Lost
        """
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        stats = Lead.objects.filter(gym=gym).aggregate(
            total=Count('id'),
            new_this_month=Count('id', filter=Q(created_at__gte=month_start)),
            converted_total=Count('id', filter=Q(status=Lead.Status.CONVERTED)),
            converted_this_month=Count('id', filter=Q(status=Lead.Status.CONVERTED, converted_at__gte=month_start)),
            lost=Count('id', filter=Q(status=Lead.Status.LOST)),
            trials=Count('id', filter=Q(status__in=[Lead.Status.TRIAL_BOOKED, Lead.Status.TRIAL_DONE])),
        )

        # Calculate conversion rate
        total_closed = stats['converted_total'] + stats['lost']
        conversion_rate = 0
        if total_closed > 0:
            conversion_rate = (stats['converted_total'] / total_closed) * 100

        stats['conversion_rate'] = round(conversion_rate, 2)
        
        return stats
