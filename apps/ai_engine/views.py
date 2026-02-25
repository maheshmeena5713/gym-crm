from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.fitness.models import WorkoutPlan
from apps.members.models import Member
from .services import WorkoutPlanService

from django.core.signing import Signer, BadSignature
from django.http import JsonResponse, Http404
from django.urls import reverse

class WorkoutPlanListView(LoginRequiredMixin, ListView):
    model = WorkoutPlan
    template_name = 'ai_engine/workout_list.html'
    context_object_name = 'plans'
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.gym:
             return WorkoutPlan.objects.filter(gym=self.request.user.gym).order_by('-created_at')
        return WorkoutPlan.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.gym:
            context['active_members'] = Member.objects.filter(gym=self.request.user.gym, status='active').order_by('name')
        return context

class WorkoutPlanDetailView(LoginRequiredMixin, DetailView):
    model = WorkoutPlan
    template_name = 'ai_engine/workout_detail.html'
    context_object_name = 'workout_plan'

    def get_queryset(self):
        if self.request.user.gym:
            return WorkoutPlan.objects.filter(gym=self.request.user.gym)
        return WorkoutPlan.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.gym:
            context['active_members'] = Member.objects.filter(gym=self.request.user.gym, status='active').order_by('name')
        return context

class WorkoutPlanCreateView(LoginRequiredMixin, View):
    def get(self, request):
        if not request.user.gym:
             return redirect('dashboard')
             
        return render(request, 'ai_engine/workout_form.html')

    def post(self, request):
        goal = request.POST.get('goal')
        level = request.POST.get('level')
        custom_requirements = request.POST.get('custom_requirements', '')

        if not all([goal, level]):
             messages.error(request, "Please fill all required fields.")
             return redirect('ai_engine:workout-create')

        try:
            plan, error = WorkoutPlanService.generate_workout_plan(
                gym=request.user.gym, 
                goal=goal, 
                level=level, 
                member=None, 
                custom_requirements=custom_requirements,
                user=request.user
            )
            
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
             return DietPlan.objects.filter(gym=self.request.user.gym).order_by('-created_at')
        return DietPlan.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.gym:
            context['active_members'] = Member.objects.filter(gym=self.request.user.gym, status='active').order_by('name')
        return context

class DietPlanDetailView(LoginRequiredMixin, DetailView):
    model = DietPlan
    template_name = 'ai_engine/diet_detail.html'
    context_object_name = 'diet_plan'

    def get_queryset(self):
        if self.request.user.gym:
            return DietPlan.objects.filter(gym=self.request.user.gym)
        return DietPlan.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.gym:
            context['active_members'] = Member.objects.filter(gym=self.request.user.gym, status='active').order_by('name')
        return context

class DietPlanCreateView(LoginRequiredMixin, View):
    def get(self, request):
        if not request.user.gym:
             return redirect('dashboard')
        
        return render(request, 'ai_engine/diet_form.html')

    def post(self, request):
        calories = request.POST.get('calories')
        preference = request.POST.get('preference')
        budget = request.POST.get('budget')
        custom_requirements = request.POST.get('custom_requirements', '')

        if not all([calories, preference, budget]):
             messages.error(request, "Please fill all required fields.")
             return redirect('ai_engine:diet-create')

        try:
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
                 messages.error(request, f"Generation failed: {error}")
                 return redirect('ai_engine:diet-create')
            
            messages.success(request, "Diet plan generated successfully!")
            return redirect('ai_engine:diet-detail', pk=plan.pk)

        except Member.DoesNotExist:
             messages.error(request, "Member not found.")
             return redirect('ai_engine:diet-create')

class SharedPlanGenerateView(LoginRequiredMixin, View):
    def post(self, request, pk, plan_type):
        member_id = request.POST.get('member_id')
        if not member_id:
            return JsonResponse({'error': 'Member is required'}, status=400)
            
        try:
            member = Member.objects.get(id=member_id, gym=request.user.gym)
        except Member.DoesNotExist:
            return JsonResponse({'error': 'Member not found'}, status=404)
            
        if plan_type == 'workout':
            plan = get_object_or_404(WorkoutPlan, pk=pk, gym=request.user.gym)
        elif plan_type == 'diet':
            plan = get_object_or_404(DietPlan, pk=pk, gym=request.user.gym)
        else:
            return JsonResponse({'error': 'Invalid plan type'}, status=400)
            
        signer = Signer()
        data = f"{member.id}:{plan_type}:{plan.id}"
        token = signer.sign(data)
        
        url = request.build_absolute_uri(reverse('ai_engine:shared-plan', kwargs={'token': token}))
        return JsonResponse({'url': url})

class SharedPlanPublicView(View):
    def get(self, request, token):
        signer = Signer()
        try:
            data = signer.unsign(token)
            member_id, plan_type, plan_id = data.split(':')
        except (BadSignature, ValueError):
            raise Http404("Invalid or expired link")
            
        member = get_object_or_404(Member, id=member_id)
        
        if plan_type == 'workout':
            plan = get_object_or_404(WorkoutPlan, id=plan_id)
        elif plan_type == 'diet':
            plan = get_object_or_404(DietPlan, id=plan_id)
        else:
            raise Http404("Invalid plan type")
            
        if member.gym != plan.gym:
            raise Http404("Access denied")
            
        context = {
            'plan': plan,
            'plan_type': plan_type,
            'member': member,
            'gym': plan.gym
        }
        return render(request, 'ai_engine/shared_public.html', context)
