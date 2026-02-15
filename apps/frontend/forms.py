"""
Frontend Forms - Django forms for template-based views.
"""

from django import forms
from apps.members.models import Member


class MemberForm(forms.ModelForm):
    """Form for adding/editing members."""

    class Meta:
        model = Member
        fields = [
            'name', 'phone', 'email', 'gender', 'date_of_birth',
            'goal', 'experience_level', 'height_cm', 'weight_kg',
            'dietary_preference', 'medical_conditions',
            'membership_plan', 'assigned_trainer',
            'join_date', 'membership_start', 'membership_expiry',
            'amount_paid', 'status', 'emergency_contact',
        ]

    def __init__(self, *args, gym=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.gym = gym
        # Make optional fields not required
        optional = [
            'email', 'gender', 'date_of_birth', 'height_cm', 'weight_kg',
            'medical_conditions', 'membership_plan', 'assigned_trainer',
            'membership_start', 'membership_expiry', 'emergency_contact',
        ]
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if self.gym:
            qs = Member.objects.filter(gym=self.gym, phone=phone)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("A member with this phone already exists in your gym.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        membership_expiry = cleaned_data.get('membership_expiry')
        membership_plan = cleaned_data.get('membership_plan')
        membership_start = cleaned_data.get('membership_start')
        
        # Auto-calculate expiry if missing but plan is selected
        if not membership_expiry and membership_plan:
            from django.utils import timezone
            if not membership_start:
                membership_start = timezone.now().date()
                cleaned_data['membership_start'] = membership_start
            
            # Calculate based on months
            days = membership_plan.duration_months * 30 
            cleaned_data['membership_expiry'] = membership_start + timezone.timedelta(days=days)
            membership_expiry = cleaned_data['membership_expiry']

        # If still missing, it's an error because model requires it
        if not membership_expiry:
             self.add_error('membership_expiry', "Membership expiry date is required.")
        
        return cleaned_data
