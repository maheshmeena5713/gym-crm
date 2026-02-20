from django.core.management.base import BaseCommand
from apps.billing.models import SubscriptionPlan

class Command(BaseCommand):
    help = 'Seeds the database with default subscription plans based on the GymEdge landing page pricing.'

    def handle(self, *args, **kwargs):
        plans = [
            {
                'name': 'Starter',
                'slug': 'starter',
                'price_monthly': 799.00,
                'price_yearly': 7990.00,  # Example: 10 months price for yearly
                'discount_pct': 16,
                'max_members': 150,
                'max_ai_queries_per_month': 0,
                'max_staff_accounts': 1,
                'max_leads': 50,
                'has_lead_management': False,
                'has_ai_workout': False,
                'has_ai_diet': False,
                'has_ai_lead_scoring': False,
                'has_whatsapp_integration': False,
                'has_instagram_content': False,
                'has_analytics_dashboard': False,
                'has_white_label': False,
                'has_api_access': False,
                'display_order': 1,
                'is_active': True,
            },
            {
                'name': 'Growth',
                'slug': 'growth',
                'price_monthly': 1299.00,
                'price_yearly': 12990.00,
                'discount_pct': 16,
                'max_members': 500,
                'max_ai_queries_per_month': 500,
                'max_staff_accounts': 3,
                'max_leads': 500,
                'has_lead_management': True,
                'has_ai_workout': False,
                'has_ai_diet': False,
                'has_ai_lead_scoring': False,
                'has_whatsapp_integration': True,
                'has_instagram_content': False,
                'has_analytics_dashboard': True,
                'has_white_label': False,
                'has_api_access': False,
                'display_order': 2,
                'is_active': True,
            },
            {
                'name': 'Pro',
                'slug': 'pro',
                'price_monthly': 1999.00,
                'price_yearly': 19990.00,
                'discount_pct': 16,
                'max_members': 5000,
                'max_ai_queries_per_month': 5000,
                'max_staff_accounts': 10,
                'max_leads': 5000,
                'has_lead_management': True,
                'has_ai_workout': True,
                'has_ai_diet': True,
                'has_ai_lead_scoring': True,
                'has_whatsapp_integration': True,
                'has_instagram_content': True,
                'has_analytics_dashboard': True,
                'has_white_label': False,
                'has_api_access': False,
                'display_order': 3,
                'is_active': True,
            },
        ]

        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.update_or_create(
                slug=plan_data['slug'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created plan: {plan.name}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated plan: {plan.name}"))

        self.stdout.write(self.style.SUCCESS('Successfully seeded subscription plans.'))
