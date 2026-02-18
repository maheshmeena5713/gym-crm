from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.leads.models import Lead
from apps.leads.services import LeadService

class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = 'leads/lead_list.html'
    context_object_name = 'leads'
    paginate_by = 20

    def get_queryset(self):
        if hasattr(self.request.user, 'gym') and self.request.user.gym:
            return Lead.objects.filter(gym=self.request.user.gym).order_by('-created_at')
        return Lead.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'gym') and self.request.user.gym:
            context['summary'] = LeadService.get_lead_summary(self.request.user.gym)
        return context

class LeadCreateView(LoginRequiredMixin, CreateView):
    model = Lead
    template_name = 'leads/lead_form.html'
    fields = ['name', 'phone', 'email', 'source', 'budget_range', 'goal', 'notes']
    success_url = reverse_lazy('leads:lead-list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'gym') and self.request.user.gym:
            form.instance.gym = self.request.user.gym
            form.instance.status = Lead.Status.NEW
            messages.success(self.request, "Lead created successfully!")
            return super().form_valid(form)
        messages.error(self.request, "You must be associated with a gym to create leads.")
        return self.form_invalid(form)

class LeadUpdateView(LoginRequiredMixin, UpdateView):
    model = Lead
    template_name = 'leads/lead_form.html'
    fields = ['name', 'phone', 'email', 'source', 'status', 'budget_range', 'goal', 'notes', 'next_followup_date']
    success_url = reverse_lazy('leads:lead-list')

    def get_queryset(self):
        if hasattr(self.request.user, 'gym') and self.request.user.gym:
            return Lead.objects.filter(gym=self.request.user.gym)
        return Lead.objects.none()

    def form_valid(self, form):
        messages.success(self.request, "Lead updated successfully!")
        return super().form_valid(form)
