from rest_framework import serializers
from apps.leads.models import Lead

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            'id', 'name', 'phone', 'email', 'source', 'goal', 
            'budget_range', 'preferred_time', 'status', 'lost_reason',
            'ai_score', 'ai_recommended_action', 'ai_follow_up_date',
            'last_contacted_date', 'next_followup_date', 'trial_date', 'converted_at',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'ai_score', 'ai_recommended_action', 'converted_at', 'created_at', 'updated_at']

class LeadSummarySerializer(serializers.Serializer):
    total = serializers.IntegerField()
    new_this_month = serializers.IntegerField()
    converted_total = serializers.IntegerField()
    converted_this_month = serializers.IntegerField()
    lost = serializers.IntegerField()
    trials = serializers.IntegerField()
    conversion_rate = serializers.FloatField()
