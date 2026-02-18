from rest_framework import serializers
from apps.fitness.models import DietPlan

class DietPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for DietPlan model.
    """
    member_name = serializers.CharField(source='member.name', read_only=True)
    gym_name = serializers.CharField(source='gym.name', read_only=True)
    plan_json = serializers.JSONField(source='plan_data', read_only=True)
    provider = serializers.CharField(source='ai_model_used', read_only=True)

    class Meta:
        model = DietPlan
        fields = [
            'id', 
            'gym_name', 
            'member', 
            'member_name', 
            'title',
            'goal', 
            'dietary_preference',
            'daily_calories',
            'plan_json', 
            'provider',
            'created_at'
        ]
        read_only_fields = ['id', 'plan_json', 'created_at', 'provider', 'gym_name', 'member_name']
