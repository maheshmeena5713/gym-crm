"""
Template context processor for subscription plan features and trial status.
Injects `plan` and `trial` into every template context.
"""

from django.utils import timezone


def subscription_context(request):
    """
    Inject subscription plan and trial info into every template.

    Usage in templates:
        {{ plan.name }}                 → "Starter" / "Pro" / "Enterprise"
        {{ plan.has_lead_management }}  → True/False
        {{ plan.has_ai_workout }}       → True/False
        {{ trial.is_trial }}           → True/False
        {{ trial.days_left }}          → 12
        {{ trial.expired }}            → True/False
    """
    ctx = {'plan': None, 'trial': {'is_trial': False, 'days_left': 0, 'expired': False}}

    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', False):
        return ctx

    gym = getattr(user, 'gym', None)
    if not gym:
        return ctx

    # ── Plan ──
    ctx['plan'] = gym.subscription_plan

    # ── Trial info ──
    if gym.subscription_status == 'trial':
        trial_info = {'is_trial': True, 'days_left': 0, 'expired': False, 'ends_at': None}

        if gym.trial_ends_at:
            trial_info['ends_at'] = gym.trial_ends_at
            delta = gym.trial_ends_at - timezone.now()
            days_left = max(0, delta.days)
            trial_info['days_left'] = days_left
            trial_info['expired'] = days_left <= 0

        ctx['trial'] = trial_info

    return ctx
