from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.fitness.models import WorkoutPlan
from apps.members.models import Member
from .services import WorkoutPlanService

class WorkoutPlanListView(LoginRequiredMixin, ListView):
    model = WorkoutPlan
    template_name = 'ai_engine/workout_list.html'
    context_object_name = 'plans'
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.gym:
             return WorkoutPlan.objects.filter(gym=self.request.user.gym).select_related('member').order_by('-created_at')
        return WorkoutPlan.objects.none()

class WorkoutPlanDetailView(LoginRequiredMixin, DetailView):
    model = WorkoutPlan
    template_name = 'ai_engine/workout_detail.html'
    context_object_name = 'workout_plan'

    def get_queryset(self):
        # Ensure user can only view plans from their gym
        if self.request.user.gym:
            return WorkoutPlan.objects.filter(gym=self.request.user.gym)
        return WorkoutPlan.objects.none()

class WorkoutPlanCreateView(LoginRequiredMixin, View):
    def get(self, request):
        if not request.user.gym:
             return redirect('dashboard')
             
        members = Member.objects.filter(gym=request.user.gym, status='active').order_by('name')
        return render(request, 'ai_engine/workout_form.html', {'members': members})

    def post(self, request):
        member_id = request.POST.get('member')
        goal = request.POST.get('goal')
        level = request.POST.get('level')

        if not all([member_id, goal, level]):
             messages.error(request, "Please fill all fields.")
             return redirect('ai_engine:workout-create')

        try:
            member = Member.objects.get(id=member_id, gym=request.user.gym)
            plan, error = WorkoutPlanService.generate_workout_plan(member, goal, level, user=request.user)
            
            if error:
                 messages.error(request, f"Generation failed: {error}")
                 return redirect('ai_engine:workout-create')
            
            messages.success(request, "Workout plan generated successfully!")
            return redirect('ai_engine:workout-detail', pk=plan.pk)

        except Member.DoesNotExist:
             messages.error(request, "Member not found.")
             return redirect('ai_engine:workout-create')

from apps.fitness.models import DietPlan
from .services_diet import DietPlanService

class DietPlanListView(LoginRequiredMixin, ListView):
    model = DietPlan
    template_name = 'ai_engine/diet_list.html'
    context_object_name = 'plans'
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.gym:
             return DietPlan.objects.filter(gym=self.request.user.gym).select_related('member').order_by('-created_at')
        return DietPlan.objects.none()

class DietPlanDetailView(LoginRequiredMixin, DetailView):
    model = DietPlan
    template_name = 'ai_engine/diet_detail.html'
    context_object_name = 'diet_plan'

    def get_queryset(self):
        if self.request.user.gym:
            return DietPlan.objects.filter(gym=self.request.user.gym)
        return DietPlan.objects.none()

class DietPlanCreateView(LoginRequiredMixin, View):
    def get(self, request):
        if not request.user.gym:
             return redirect('dashboard')
        
        # Use status='active' fix here too
        members = Member.objects.filter(gym=request.user.gym, status='active').order_by('name')
        return render(request, 'ai_engine/diet_form.html', {'members': members})

    def post(self, request):
        member_id = request.POST.get('member')
        calories = request.POST.get('calories')
        preference = request.POST.get('preference')
        budget = request.POST.get('budget')

        if not all([member_id, calories, preference, budget]):
             messages.error(request, "Please fill all fields.")
             return redirect('ai_engine:diet-create')

        try:
            member = Member.objects.get(id=member_id, gym=request.user.gym)
            plan, error = DietPlanService.generate_diet_plan(member, calories, preference, budget, user=request.user)
            
            if error:
                 messages.error(request, f"Generation failed: {error}")
                 return redirect('ai_engine:diet-create')
            
            messages.success(request, "Diet plan generated successfully!")
            return redirect('ai_engine:diet-detail', pk=plan.pk)

        except Member.DoesNotExist:
             messages.error(request, "Member not found.")
             return redirect('ai_engine:diet-create')
