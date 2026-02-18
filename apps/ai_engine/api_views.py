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
        member_id = request.data.get('member')
        goal = request.data.get('goal')
        level = request.data.get('level')

        if not all([member_id, goal, level]):
            return Response(
                {"error": "Missing required fields: member, goal, level"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate Member belongs to user's gym
        from apps.members.models import Member
        try:
            member = Member.objects.get(id=member_id, gym=request.user.gym)
        except Member.DoesNotExist:
            return Response(
                {"error": "Member not found or access denied."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Call Service
        plan, error = WorkoutPlanService.generate_workout_plan(member, goal, level, user=request.user)
        
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
        member_id = request.data.get('member')
        calories = request.data.get('calories')
        preference = request.data.get('preference')
        budget = request.data.get('budget', 'medium')

        if not all([member_id, calories, preference]):
            return Response(
                {"error": "Missing required fields: member, calories, preference"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.members.models import Member
        try:
            member = Member.objects.get(id=member_id, gym=request.user.gym)
        except Member.DoesNotExist:
            return Response(
                {"error": "Member not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        plan, error = DietPlanService.generate_diet_plan(member, calories, preference, budget, user=request.user)
        
        if error:
            return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
