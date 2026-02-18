from rest_framework import serializers
from apps.fitness.models import WorkoutPlan

class WorkoutPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for WorkoutPlan model (from apps.fitness).
    """
    member_name = serializers.CharField(source='member.name', read_only=True)
    gym_name = serializers.CharField(source='gym.name', read_only=True)
    level = serializers.CharField(source='difficulty', read_only=True)
    plan_json = serializers.JSONField(source='plan_data', read_only=True)
    provider = serializers.CharField(source='ai_model_used', read_only=True)

    class Meta:
        model = WorkoutPlan
        fields = [
            'id', 
            'gym_name', 
            'member', 
            'member_name', 
            'title',
            'goal', 
            'level', 
            'duration_weeks', 
            'plan_json', 
            'provider',
            'created_at'
        ]
        read_only_fields = ['id', 'plan_json', 'created_at', 'provider', 'duration_weeks', 'gym_name', 'member_name']
