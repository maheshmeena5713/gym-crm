from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from io import StringIO
from django.core.management import call_command

from apps.gyms.models import Gym
from apps.billing.models import SubscriptionPlan
from apps.members.models import Member, MembershipPlan
from apps.communications.models import WhatsAppAutomation, WhatsAppMessageLog
from apps.communications.services import WhatsAppService
from unittest.mock import patch, MagicMock

class WhatsAppAutomationTests(TestCase):
    def setUp(self):
        # Create Plans
        self.pro_plan = SubscriptionPlan.objects.create(
            name="Pro", slug="pro", price_monthly=1000, price_yearly=10000,
            has_whatsapp_integration=True
        )
        self.basic_plan = SubscriptionPlan.objects.create(
            name="Basic", slug="basic", price_monthly=500, price_yearly=5000,
            has_whatsapp_integration=False
        )
        
        # Create Gyms
        self.gym_pro = Gym.objects.create(
            name="Pro Gym", gym_code="PRO123", email="pro@gym.com", owner_name="Owner",
            subscription_plan=self.pro_plan, is_active=True
        )
        self.gym_basic = Gym.objects.create(
            name="Basic Gym", gym_code="BAS123", email="bas@gym.com", owner_name="Owner2",
            subscription_plan=self.basic_plan, is_active=True
        )

        # Create Memberships
        self.mplan = MembershipPlan.objects.create(
            gym=self.gym_pro, name="Monthly", duration_months=1, price=1000
        )
        
        # We need an expiry 3 days from now
        self.today = timezone.now().date()
        self.target_expiry = self.today + timedelta(days=3)
        self.past_target = self.today - timedelta(days=3)

        self.member1 = Member.objects.create(
            gym=self.gym_pro, name="John Doe", phone="9876543210", 
            membership_plan=self.mplan, join_date=self.today, 
            membership_start=self.today, membership_expiry=self.target_expiry,
            status='active'
        )
        
        self.member_inactive = Member.objects.create(
            gym=self.gym_pro, name="Jane Doe", phone="9876543211", 
            membership_plan=self.mplan, join_date=self.past_target, 
            membership_start=self.past_target, membership_expiry=self.today,
            last_check_in=timezone.now() - timedelta(days=3),
            status='active'
        )

    @patch('apps.communications.services.WhatsAppService.send_whatsapp_message')
    def test_automation_filtering_logic(self, mock_send):
        """Test that members matching rules are found correctly"""
        # Create automations
        auto_expiry = WhatsAppAutomation.objects.create(
            gym=self.gym_pro,
            type=WhatsAppAutomation.AutomationType.EXPIRY_REMINDER,
            enabled=True,
            days_before=3,
            template="Hi {{name}}, your plan {{plan_name}} expires on {{expiry_date}}."
        )

        mock_send.return_value = {"status": "success", "message_id": "test_123"}

        out = StringIO()
        call_command('run_whatsapp_automations', stdout=out)
        
        # Verify
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        self.assertEqual(kwargs['phone'], self.member1.phone)
        self.assertIn("John Doe", kwargs['message'])
        self.assertIn("Monthly", kwargs['message'])
        
        # Verify log was created (the mock doesn't create the log directly unless the management command does it? No, the command creates the log indirectly if simulation_mode is off, wait. 
        # The command expects `send_whatsapp_message` to create the log. If mocked, the log won't be created.
        # But we do check if `already_sent` query filters correctly.)

    @patch('apps.communications.services.WhatsAppService.send_whatsapp_message')
    def test_duplicate_prevention(self, mock_send):
        """Test that messages are not sent twice in the same day."""
        auto_expiry = WhatsAppAutomation.objects.create(
            gym=self.gym_pro,
            type=WhatsAppAutomation.AutomationType.EXPIRY_REMINDER,
            enabled=True,
            days_before=3,
            template="Ping!"
        )

        # Pre-create a log to simulate an already sent message
        WhatsAppMessageLog.objects.create(
            gym=self.gym_pro,
            member=self.member1,
            phone=self.member1.phone,
            message="Ping!",
            status='sent'
        )
        
        out = StringIO()
        call_command('run_whatsapp_automations', stdout=out)
        
        # Assert send wasn't called because it was skipped
        mock_send.assert_not_called()

    @patch('apps.communications.services.WhatsAppService.send_whatsapp_message')
    def test_pro_plan_restriction(self, mock_send):
        """Test that gyms without the integration flag are ignored."""
        auto_basic = WhatsAppAutomation.objects.create(
            gym=self.gym_basic,
            type=WhatsAppAutomation.AutomationType.EXPIRY_REMINDER,
            enabled=True,
            days_before=3,
            template="Hi"
        )
        Member.objects.create(
            gym=self.gym_basic, name="Basic User", phone="1111111111", 
            membership_plan=self.mplan, join_date=self.today, 
            membership_start=self.today, membership_expiry=self.target_expiry,
            status='active'
        )
        
        out = StringIO()
        call_command('run_whatsapp_automations', stdout=out)
        
        # Basic gym should be skipped
        mock_send.assert_not_called()
