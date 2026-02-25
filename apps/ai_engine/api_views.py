from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from apps.fitness.models import WorkoutPlan
from .serializers import WorkoutPlanSerializer
from .services import WorkoutPlanService

class WorkoutPlanViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing AI Workout Plans.
    Only allows creating new plans or viewing existing ones.
    """
    serializer_class = WorkoutPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see plans for their gym
        if self.request.user.gym:
            return WorkoutPlan.objects.filter(gym=self.request.user.gym).select_related('member')
        return WorkoutPlan.objects.none()

    def create(self, request, *args, **kwargs):
        goal = request.data.get('goal')
        level = request.data.get('level')
        custom_requirements = request.data.get('custom_requirements', '')

        if not all([goal, level]):
            return Response(
                {"error": "Missing required fields: goal, level"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Call Service
        plan, error = WorkoutPlanService.generate_workout_plan(
            gym=request.user.gym, 
            goal=goal, 
            level=level, 
            member=None, 
            custom_requirements=custom_requirements,
            user=request.user
        )
        
        if error:
            return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

from apps.fitness.models import DietPlan
from .serializers_diet import DietPlanSerializer
from .services_diet import DietPlanService

class DietPlanViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing AI Diet Plans.
    """
    serializer_class = DietPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.gym:
            return DietPlan.objects.filter(gym=self.request.user.gym).select_related('member')
        return DietPlan.objects.none()

    def create(self, request, *args, **kwargs):
        calories = request.data.get('calories')
        preference = request.data.get('preference')
        budget = request.data.get('budget', 'medium')
        custom_requirements = request.data.get('custom_requirements', '')

        if not all([calories, preference]):
            return Response(
                {"error": "Missing required fields: calories, preference"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        plan, error = DietPlanService.generate_diet_plan(
            gym=request.user.gym, 
            calories=calories, 
            preference=preference, 
            budget=budget, 
            member=None, 
            custom_requirements=custom_requirements,
            user=request.user
        )
        
        if error:
            return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
