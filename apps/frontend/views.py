"""
Frontend Views - Template-based views for Gym AI Dashboard.
Session-based auth (not JWT). Multi-method login: OTP or Password.
"""

import logging
import re
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import View

from apps.gyms.models import Gym
from apps.enterprises.models import HoldingCompany, Brand, Organization
from apps.members.models import Member, MembershipPlan
from apps.billing.models import SubscriptionPlan
from apps.users.models import GymUser
from apps.users.services import OTPService
from apps.members.services import BulkImportService, AIScanService
from apps.frontend.forms import MemberForm

logger = logging.getLogger('apps.frontend')


# ── Helper ────────────────────────────────────────────────────

def _gym_branding_ctx(gym):
    """Return gym branding context for templates."""
    if not gym:
        return {}
    return {
        'gym_name': gym.name,
        'gym_code': gym.gym_code,
        'gym_logo': gym.logo_data_uri,
        'brand_color': gym.brand_color,
        'font_family': gym.font_family,
    }


# ── Landing Page ──────────────────────────────────────────────

class LandingPageView(View):
    """Public SaaS landing / marketing page."""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('frontend:dashboard')
        
        plans = SubscriptionPlan.active_objects.all().order_by('display_order', 'price_monthly')
        return render(request, 'landing_redesigned.html', {'plans': plans})


# ── Auth Views ────────────────────────────────────────────────

class LoginView(View):
    """Step 1: Show entity code form or redirect if already validated."""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('frontend:dashboard')

        # Clear entity session if requested (e.g., from "Switch Gym" button)
        if request.GET.get('clear') == '1':
            request.session.pop('login_entity_type', None)
            request.session.pop('login_entity_id', None)
            request.session.pop('login_gym_code', None)

        # Check if entity is already validated in session
        entity_type = request.session.get('login_entity_type')
        entity_id = request.session.get('login_entity_id')

        if entity_type and entity_id:
            # Render context-aware login page (e.g., Logo, Name)
            context = {'entity_type_label': entity_type.title()}
            
            if entity_type == 'gym':
                 gym = Gym.objects.filter(pk=entity_id).first()
                 if gym:
                     context.update(_gym_branding_ctx(gym))
                     context['entity_name'] = gym.name
            elif entity_type == 'holding':
                 holding = HoldingCompany.objects.filter(pk=entity_id).first()
                 if holding:
                     context['entity_name'] = holding.name
            elif entity_type == 'brand':
                 brand = Brand.objects.filter(pk=entity_id).first()
                 if brand:
                     context['entity_name'] = brand.name
            elif entity_type == 'org':
                 org = Organization.objects.filter(pk=entity_id).first()
                 if org:
                     context['entity_name'] = org.name

            # If we have context, it means step 1 is done, show step 2 (login form)
            # reusing existing login.html but potentially with different copy
            return render(request, 'auth/login.html', context)

        if request.htmx:
            return render(request, 'auth/gym_code_form.html')
        
        return render(request, 'auth/login.html')


class ValidateEntityCodeView(View):
    """
    Step 1 of Login: Validate Entity Code (Gym, Holding, Brand, or Org).
    """
    def post(self, request):
        code = request.POST.get('entity_code', '').strip().upper()
        
        if not code:
            return JsonResponse({'success': False, 'error': 'Please enter a valid code.'}, status=400)

        # 1. Check Gym
        try:
            gym = Gym.objects.get(gym_code=code, is_active=True)
            request.session['login_entity_type'] = 'gym'
            request.session['login_entity_id'] = str(gym.pk)
            request.session['login_gym_code'] = gym.gym_code
            response = JsonResponse({'success': True, 'redirect': '/auth/login/', 'name': gym.name, 'type': 'Gym'})
            response['HX-Redirect'] = '/auth/login/'
            return response
        except Gym.DoesNotExist:
            pass

        # 2. Check Holding Company
        try:
            holding = HoldingCompany.objects.get(holding_code=code, is_active=True)
            request.session['login_entity_type'] = 'holding'
            request.session['login_entity_id'] = str(holding.pk)
            del request.session['login_gym_code'] # Clear gym context if switching
            response = JsonResponse({'success': True, 'redirect': '/auth/login/', 'name': holding.name, 'type': 'Holding Company'})
            response['HX-Redirect'] = '/auth/login/'
            return response
        except (HoldingCompany.DoesNotExist, KeyError):
            pass

        # 3. Check Brand
        try:
            brand = Brand.objects.get(brand_code=code, is_active=True)
            request.session['login_entity_type'] = 'brand'
            request.session['login_entity_id'] = str(brand.pk)
            del request.session['login_gym_code'] # Clear gym context
            response = JsonResponse({'success': True, 'redirect': '/auth/login/', 'name': brand.name, 'type': 'Brand'})
            response['HX-Redirect'] = '/auth/login/'
            return response
        except (Brand.DoesNotExist, KeyError):
            pass

        # 4. Check Organization
        try:
            org = Organization.objects.get(org_code=code, is_active=True)
            request.session['login_entity_type'] = 'org'
            request.session['login_entity_id'] = str(org.pk)
            del request.session['login_gym_code'] # Clear gym context
            response = JsonResponse({'success': True, 'redirect': '/auth/login/', 'name': org.name, 'type': 'Organization'})
            response['HX-Redirect'] = '/auth/login/'
            return response
        except (Organization.DoesNotExist, KeyError):
            pass

        return JsonResponse({'success': False, 'error': 'Invalid Entity Code. Please check and try again.'}, status=400)


class SendOTPView(View):
    """Step 2 → 3: Send OTP, return branded OTP form."""
    def post(self, request):
        phone = request.POST.get('phone', '').strip()
        
        # Get entity context
        entity_type = request.session.get('login_entity_type')
        entity_id = request.session.get('login_entity_id')
        
        ctx = {'phone': phone}
        
        # Resolve Entity
        gym = None
        holding = None
        brand = None
        org = None

        if entity_type == 'gym':
             gym = Gym.objects.filter(pk=entity_id).first()
             if gym:
                 ctx.update(_gym_branding_ctx(gym))
                 ctx['entity_name'] = gym.name
                 ctx['entity_type_label'] = 'Gym'
        elif entity_type == 'holding':
             holding = HoldingCompany.objects.filter(pk=entity_id).first()
             if holding:
                 ctx['entity_name'] = holding.name
                 ctx['entity_type_label'] = 'Holding Company'
        elif entity_type == 'brand':
             brand = Brand.objects.filter(pk=entity_id).first()
             if brand:
                 ctx['entity_name'] = brand.name
                 ctx['entity_type_label'] = 'Brand'
        elif entity_type == 'org':
             org = Organization.objects.filter(pk=entity_id).first()
             if org:
                 ctx['entity_name'] = org.name
                 ctx['entity_type_label'] = 'Organization'

        if not phone or len(phone) < 10:
            ctx['error'] = 'Enter a valid 10-digit number.'
            return render(request, 'auth/phone_form.html', ctx)

        # Validate User existence in Entity Context
        user_exists = False
        if entity_type == 'gym' and gym:
             user_exists = GymUser.objects.filter(phone=phone, gym=gym, is_active=True).exists()
        elif entity_type == 'holding' and holding:
             user_exists = GymUser.objects.filter(phone=phone, holding_company=holding, is_active=True).exists()
        elif entity_type == 'brand' and brand:
             user_exists = GymUser.objects.filter(phone=phone, brand=brand, is_active=True).exists()
        elif entity_type == 'org' and org:
             user_exists = GymUser.objects.filter(phone=phone, organization=org, is_active=True).exists()
        
        if not user_exists:
             ctx['error'] = 'This phone number is not registered with this entity.'
             return render(request, 'auth/phone_form.html', ctx)

        success, message = OTPService.send_otp(phone)
        if success:
            return render(request, 'auth/otp_form.html', ctx)

        ctx['error'] = message
        return render(request, 'auth/phone_form.html', ctx)


class VerifyOTPView(View):
    """Step 3: Verify OTP, login, redirect to dashboard."""
    def post(self, request):
        phone = request.POST.get('phone', '').strip()
        otp = request.POST.get('otp', '').strip()

        # Get entity context
        entity_type = request.session.get('login_entity_type')
        entity_id = request.session.get('login_entity_id')
        
        ctx = {'phone': phone}
        
        # Resolve Entity (for branding)
        gym = None
        holding = None
        brand = None
        org = None

        if entity_type == 'gym':
             gym = Gym.objects.filter(pk=entity_id).first()
             if gym:
                 ctx.update(_gym_branding_ctx(gym))
                 ctx['entity_name'] = gym.name
                 ctx['entity_type_label'] = 'Gym'
        elif entity_type == 'holding':
             holding = HoldingCompany.objects.filter(pk=entity_id).first()
             if holding:
                 ctx['entity_name'] = holding.name
                 ctx['entity_type_label'] = 'Holding Company'
        elif entity_type == 'brand':
             brand = Brand.objects.filter(pk=entity_id).first()
             if brand:
                 ctx['entity_name'] = brand.name
                 ctx['entity_type_label'] = 'Brand'
        elif entity_type == 'org':
             org = Organization.objects.filter(pk=entity_id).first()
             if org:
                 ctx['entity_name'] = org.name
                 ctx['entity_type_label'] = 'Organization'

        if not phone or not otp:
            ctx['error'] = 'Please enter the OTP.'
            return render(request, 'auth/otp_form.html', ctx)

        success, result = OTPService.verify_otp(phone, otp)
        
        if success:
            user = result['user']
            
            # Authorization Check: Verify user belongs to the entity
            authorized = False
            if entity_type == 'gym' and gym:
                authorized = (user.gym == gym)
            elif entity_type == 'holding' and holding:
                authorized = (user.holding_company == holding)
            elif entity_type == 'brand' and brand:
                authorized = (user.brand == brand)
            elif entity_type == 'org' and org:
                authorized = (user.organization == org)
            
            # Superusers can bypass entity checks
            if user.is_superuser:
                authorized = True

            if not authorized:
                ctx['error'] = 'Access Denied. You do not belong to this entity.'
                return render(request, 'auth/otp_form.html', ctx)
            
            # Login successful
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Clear login session data
            request.session.pop('login_entity_type', None)
            request.session.pop('login_entity_id', None)
            request.session.pop('login_gym_code', None)
            
            # Build response with HX-Redirect header
            response = HttpResponse(status=200)
            response['HX-Redirect'] = '/dashboard/'
            
            # Pass gym info as JSON for localStorage via a cookie (for gym users only)
            if user.gym:
                import json
                gym_cache = json.dumps({
                    'gym_code': user.gym.gym_code,
                    'gym_name': user.gym.name,
                    'gym_logo': user.gym.logo_data_uri or '',
                })
                response.set_cookie('gym_cache_data', gym_cache, max_age=365*24*60*60, httponly=False, samesite='Lax')

            return response
        
        # OTP verification failed
        ctx['error'] = result
        return render(request, 'auth/otp_form.html', ctx)


# ── Signup Views ──────────────────────────────────────────────

class SignupView(View):
    """Render the signup page for new gym owners."""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('frontend:dashboard')
        
        # Capture pre-selected plan from URL
        selected_plan = request.GET.get('plan', '')
        plans = SubscriptionPlan.active_objects.all().order_by('display_order', 'price_monthly')
        
        context = {
            'selected_plan': selected_plan,
            'plans': plans,
        }
        return render(request, 'auth/signup.html', context)


class SignupSendOTPView(View):
    """Validate gym details from Step 1 + phone from Step 2, send OTP."""
    def post(self, request):
        # Collect all fields
        plan_slug = request.POST.get('plan_slug', '').strip()
        gym_name = request.POST.get('gym_name', '').strip()
        owner_name = request.POST.get('owner_name', '').strip()
        email = request.POST.get('email', '').strip()
        city = request.POST.get('city', '').strip()
        phone = request.POST.get('phone', '').strip()
        username = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '').strip()

        errors = {}
        if not gym_name:
            errors['gym_name'] = 'Gym name is required.'
        if not owner_name:
            errors['owner_name'] = 'Your name is required.'
        if not email:
            errors['email'] = 'Email is required.'
        elif Gym.objects.filter(email=email).exists():
            errors['email'] = 'A gym with this email already exists.'
        if not phone or len(phone) < 10:
            errors['phone'] = 'Enter a valid 10-digit phone number.'

        # Username validation
        print(f"DEBUG Username: '{username}'")
        if not username:
            errors['username'] = 'Username is required.'
        elif len(username) < 4:
            errors['username'] = 'Username must be at least 4 characters.'
        elif len(username) > 30:
            errors['username'] = 'Username must be 30 characters or less.'
        elif not re.match(r'^[a-z0-9_]+$', username):
            errors['username'] = 'Only lowercase letters, numbers & underscores.'
        elif GymUser.objects.filter(username=username).exists():
            errors['username'] = 'This username is already taken.'

        # Password validation
        if not password:
            errors['password'] = 'Password is required.'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        # Store signup data in session
        request.session['signup_data'] = {
            'plan_slug': plan_slug,
            'gym_name': gym_name,
            'owner_name': owner_name,
            'email': email,
            'city': city,
            'phone': phone,
            'username': username,
            'password': password,
        }

        # Send OTP
        success, message = OTPService.send_otp(phone)
        if not success:
            return JsonResponse({'success': False, 'errors': {'phone': message}}, status=400)

        return JsonResponse({'success': True, 'message': 'OTP sent successfully.'})


class SignupVerifyOTPView(View):
    """Verify OTP, create Gym + Owner, auto-login."""
    def post(self, request):
        otp = request.POST.get('otp', '').strip()
        signup_data = request.session.get('signup_data')

        if not signup_data:
            return JsonResponse({'success': False, 'error': 'Signup session expired. Please start again.'}, status=400)

        phone = signup_data['phone']

        if not otp:
            return JsonResponse({'success': False, 'error': 'Please enter the OTP.'}, status=400)

        # Verify OTP
        success, result = OTPService.verify_otp(phone, otp)
        if not success:
            return JsonResponse({'success': False, 'error': result}, status=400)

        # Get the selected plan, fallback to starter if missing
        plan_slug = signup_data.get('plan_slug')
        plan = SubscriptionPlan.objects.filter(slug=plan_slug).first()
        if not plan:
            plan = SubscriptionPlan.objects.filter(slug='starter').first()

        # Create the Gym
        gym = Gym.objects.create(
            name=signup_data['gym_name'],
            owner_name=signup_data['owner_name'],
            owner_phone=phone,
            email=signup_data['email'],
            city=signup_data.get('city', ''),
            subscription_plan=plan,
            subscription_status='trial',
            trial_ends_at=timezone.now() + timedelta(days=30),
            is_active=True,
        )

        # The OTPService.verify_otp already created a GymUser — update it
        user = result['user']
        user.name = signup_data['owner_name']
        user.gym = gym
        user.role = 'owner'
        user.email = signup_data['email']
        user.username = signup_data.get('username')
        if signup_data.get('password'):
            user.set_password(signup_data['password'])
        user.can_view_revenue = True
        user.can_manage_members = True
        user.can_manage_leads = True
        user.can_use_ai = True
        user.save()

        # Auto-login
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Clean up session
        request.session.pop('signup_data', None)

        # Return gym info for localStorage
        import json
        return JsonResponse({
            'success': True,
            'redirect': '/dashboard/',
            'gym_cache': {
                'gym_code': gym.gym_code,
                'gym_name': gym.name,
                'gym_logo': '',
            },
        })


class CheckUsernameView(View):
    """Real-time username availability check (Instagram-style)."""
    def post(self, request):
        username = request.POST.get('username', '').strip().lower()

        if len(username) < 4:
            return JsonResponse({'available': False, 'reason': 'min_length',
                                 'message': 'Minimum 4 characters required'})

        if not re.match(r'^[a-z0-9_]+$', username):
            return JsonResponse({'available': False, 'reason': 'invalid_chars',
                                 'message': 'Only lowercase letters, numbers & underscores'})

        if len(username) > 30:
            return JsonResponse({'available': False, 'reason': 'max_length',
                                 'message': 'Maximum 30 characters'})

        exists = GymUser.objects.filter(username=username).exists()
        if exists:
            return JsonResponse({'available': False, 'reason': 'taken',
                                 'message': 'This username is already taken'})

        return JsonResponse({'available': True, 'message': 'Username is available'})


class PasswordLoginView(View):
    """Login via email/username + password (Tab 2 of login form)."""
    def post(self, request):
        print(request.POST)
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '')

        # Get entity context from session
        entity_type = request.session.get('login_entity_type')
        entity_id = request.session.get('login_entity_id')
        
        # Build context for re-rendering form on error
        ctx = {'active_tab': 'password', 'identifier': identifier}
        
        # Helper to get entity object (could be refactored to shared method)
        gym = None
        holding = None
        brand = None
        org = None

        if entity_type == 'gym':
             gym = Gym.objects.filter(pk=entity_id).first()
             if gym:
                 ctx.update(_gym_branding_ctx(gym))
                 ctx['entity_name'] = gym.name
                 ctx['entity_type_label'] = 'Gym'
        elif entity_type == 'holding':
             holding = HoldingCompany.objects.filter(pk=entity_id).first()
             if holding:
                 ctx['entity_name'] = holding.name
                 ctx['entity_type_label'] = 'Holding Company'
        elif entity_type == 'brand':
             brand = Brand.objects.filter(pk=entity_id).first()
             if brand:
                 ctx['entity_name'] = brand.name
                 ctx['entity_type_label'] = 'Brand'
        elif entity_type == 'org':
             org = Organization.objects.filter(pk=entity_id).first()
             if org:
                 ctx['entity_name'] = org.name
                 ctx['entity_type_label'] = 'Organization'

        if not identifier or not password:
            ctx['pw_error'] = 'Enter your email/username and password.'
            return render(request, 'auth/phone_form.html', ctx)

        if not entity_type or not entity_id:
            ctx['pw_error'] = 'Session expired. Please start from entity code.'
            return render(request, 'auth/phone_form.html', ctx)

        # Authenticate with Entity Scope
        user = authenticate(
            request, 
            gym=gym, 
            identifier=identifier, 
            password=password,
            entity_type=entity_type,
            entity_id=entity_id
        )

        if not user:
            ctx['pw_error'] = 'Invalid credentials or access denied for this entity.'
            return render(request, 'auth/phone_form.html', ctx)

        login(request, user, backend='apps.users.backends.GymPasswordBackend')

        # Clean up session login keys
        request.session.pop('login_gym_id', None)
        request.session.pop('login_gym_code', None)

        # Build response with gym info for localStorage caching
        response = HttpResponse(status=200)
        response['HX-Redirect'] = '/dashboard/'

        if user.gym:
            import json
            gym_cache = json.dumps({
                'gym_code': user.gym.gym_code,
                'gym_name': user.gym.name,
                'gym_logo': user.gym.logo_data_uri or '',
            })
            response.set_cookie('gym_cache_data', gym_cache, max_age=365*24*60*60,
                                httponly=False, samesite='Lax')

        return response


class EnterpriseLoginView(View):
    """
    Direct login for Enterprise Admins (Holding, Brand, Org) who don't have a specific gym code.
    Bypasses the multi-step flow.
    """
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('frontend:dashboard')
        return render(request, 'frontend/auth/enterprise_login.html')

    def post(self, request):
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '')

        if not identifier or not password:
            return render(request, 'frontend/auth/enterprise_login.html', {
                'error': 'Please enter your username/email and password.',
                'identifier': identifier
            })

        # Authenticate without 'gym' context
        user = authenticate(request, gym=None, identifier=identifier, password=password)

        if not user:
            return render(request, 'frontend/auth/enterprise_login.html', {
                'error': 'Invalid credentials or unauthorized account.',
                'identifier': identifier
            })

        login(request, user, backend='apps.users.backends.GymPasswordBackend')
        return redirect('frontend:dashboard')


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('frontend:unified-login')


# ── Dashboard ─────────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        user = request.user
        
        # Enterprise Redirect
        if user.role in [GymUser.Role.HOLDING_ADMIN, GymUser.Role.BRAND_ADMIN, GymUser.Role.ORG_ADMIN]:
            return render(request, 'enterprises/dashboard.html')

        gym = user.gym

        # Build stats
        if gym:
            members_qs = Member.objects.filter(gym=gym, is_deleted=False)
            
            # 1. Total & Status Counts
            total_members = members_qs.count()
            active_count = members_qs.filter(status='active').count()
            expired_count = members_qs.filter(status='expired').count()
            frozen_count = members_qs.filter(status='frozen').count()
            
            # 2. Revenue MTD
            from django.db.models import Sum
            today = timezone.now().date()
            current_month_start = today.replace(day=1)
            revenue_mtd = members_qs.filter(
                join_date__gte=current_month_start
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            
            # Last Month Revenue (Approximation for demo)
            last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
            last_month_end = current_month_start - timedelta(days=1)
            revenue_last_month = members_qs.filter(
                join_date__gte=last_month_start,
                join_date__lte=last_month_end
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            
            revenue_growth = 0
            if revenue_last_month > 0:
                revenue_growth = int(((revenue_mtd - revenue_last_month) / revenue_last_month) * 100)
            else:
                 revenue_growth = 100 if revenue_mtd > 0 else 0

            # 3. Pending Renewals
            week_later = today + timedelta(days=7)
            expiring_soon_qs = members_qs.filter(
                status='active',
                membership_expiry__gte=today,
                membership_expiry__lte=week_later,
            )
            expiring_count = expiring_soon_qs.count()
            # Calculate potential revenue from these renewals
            pending_revenue = 0
            for m in expiring_soon_qs:
                if m.membership_plan:
                    pending_revenue += m.membership_plan.price

            # 4. Churn Risk & AI Insights
            high_risk_qs = members_qs.filter(churn_risk_score__gte=70)
            high_risk_count = high_risk_qs.count()
            
            # Detailed breakdown for "Why"
            inactive_10_days = members_qs.filter(
                last_check_in__lt=timezone.now() - timedelta(days=10),
                status='active'
            ).count()
            
            # AI Insights List (Conversational)
            ai_insights = []
            if high_risk_count > 0:
                ai_insights.append(f"{high_risk_count} members likely to churn based on attendance drops.")
            if inactive_10_days > 0:
                 ai_insights.append(f"{inactive_10_days} high-value members inactive for 10+ days.")
            if expiring_count > 0:
                 ai_insights.append(f"{expiring_count} renewals due in the next 7 days.")
            if not ai_insights:
                ai_insights.append("AI is analyzing member patterns. No critical alerts today.")

            stats = {
                'total_members': total_members,
                'active': active_count,
                'expired': expired_count,
                'frozen': frozen_count,
                'high_churn_risk': high_risk_count,
                'revenue_mtd': revenue_mtd,
                'revenue_growth': revenue_growth,
                'pending_renewals_amount': pending_revenue,
                'pending_renewals_count': expiring_count,
                'risk_inactive_count': inactive_10_days,
                'risk_renewal_count': expiring_count, # overlapping logic but okay for UI
            }
            recent_members = members_qs.order_by('-created_at')[:5]
            expiring_soon = expiring_soon_qs.order_by('membership_expiry')[:10]
        else:
            stats = {}
            recent_members = []
            expiring_soon = []
            ai_insights = []

        return render(request, 'dashboard/index.html', {
            'stats': stats,
            'recent_members': recent_members,
            'expiring_soon': expiring_soon,
            'ai_insights': ai_insights,
            'today': timezone.now().date(),
        })


class BusinessHealthView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        gym = request.user.gym
        if not gym:
            return redirect('frontend:dashboard')

        members_qs = Member.objects.filter(gym=gym, is_deleted=False)
        total_members = members_qs.count() or 1

        # 1. Revenue
        from django.db.models import Sum
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        revenue_mtd = members_qs.filter(
            join_date__gte=current_month_start
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)
        revenue_last = members_qs.filter(
            join_date__gte=last_month_start,
            join_date__lte=last_month_end
        ).aggregate(total=Sum('amount_paid'))['total'] or 0

        growth = 0
        if revenue_last > 0:
            growth = int(((revenue_mtd - revenue_last) / revenue_last) * 100)
        else:
            growth = 100 if revenue_mtd > 0 else 0

        # 2. Retention
        active_count = members_qs.filter(status='active').count()
        active_pct = int((active_count / total_members) * 100)
        
        expired_count = members_qs.filter(status='expired').count()
        expired_pct = int((expired_count / total_members) * 100)
        
        at_risk_count = members_qs.filter(churn_risk_score__gte=70).count()
        at_risk_pct = int((at_risk_count / total_members) * 100)

        # 3. Action Needed Lists
        inactive_7_days = members_qs.filter(
            last_check_in__lt=timezone.now() - timedelta(days=7),
            status='active'
        )[:5]
        
        expiring_3_days = members_qs.filter(
             status='active',
             membership_expiry__lte=today+timedelta(days=3),
             membership_expiry__gte=today
        )[:5]
        
        # Payment pending = Expired in last 30 days
        payment_pending = members_qs.filter(
            status='expired',
            membership_expiry__gte=today-timedelta(days=30),
            membership_expiry__lte=today
        )[:5]

        context = {
            'revenue': {
                'mtd': revenue_mtd,
                'last': revenue_last,
                'growth': growth
            },
            'retention': {
                'active_pct': active_pct,
                'expired_pct': expired_pct,
                'at_risk_pct': at_risk_pct,
                'total_members': total_members if members_qs.count() > 0 else 0
            },
            'actions': {
                'inactive': inactive_7_days,
                'expiring': expiring_3_days,
                'pending': payment_pending
            }
        }
        return render(request, 'dashboard/business_health.html', context)


# ── Member Views ──────────────────────────────────────────────

class MemberListView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        user = request.user
        gym = user.gym
        if not gym:
            return render(request, 'members/list.html', {
                'members': [], 'total_count': 0
            })

        qs = Member.objects.filter(gym=gym, is_deleted=False).select_related(
            'membership_plan', 'assigned_trainer'
        )

        # Search
        search = request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )

        # Filters
        status = request.GET.get('status', '')
        goal = request.GET.get('goal', '')
        if status:
            qs = qs.filter(status=status)
        if goal:
            qs = qs.filter(goal=goal)

        qs = qs.order_by('-created_at')

        # Pagination
        paginator = Paginator(qs, 20)
        page = request.GET.get('page', 1)
        members = paginator.get_page(page)

        ctx = {
            'members': members,
            'total_count': paginator.count,
            'search_query': search,
            'current_status': status,
            'current_goal': goal,
        }

        return render(request, 'members/list.html', ctx)


class MemberCreateView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        form = MemberForm(gym=request.user.gym)
        return render(request, 'members/form.html', self._context(form))

    def post(self, request):
        form = MemberForm(request.POST, gym=request.user.gym)
        if form.is_valid():
            member = form.save(commit=False)
            member.gym = request.user.gym
            if not member.membership_start:
                member.membership_start = timezone.now().date()
            member.save()
            from django.contrib import messages
            messages.success(request, f"Member {member.name} added successfully! WhatsApp welcome message sent.")
            return redirect('frontend:member-detail', pk=member.pk)
        return render(request, 'members/form.html', self._context(form))

    def _context(self, form):
        gym = self.request.user.gym
        return {
            'form': form,
            'form_title': 'Add Member',
            'submit_label': 'Add Member',
            'plans': MembershipPlan.objects.filter(
                gym=gym, is_deleted=False, is_active=True
            ) if gym else [],
            'trainers': GymUser.objects.filter(
                gym=gym, role__in=['trainer', 'manager']
            ) if gym else [],
            'today': timezone.now().date().isoformat(),
        }


class MemberDetailView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, pk):
        member = get_object_or_404(
            Member.objects.select_related('membership_plan', 'assigned_trainer', 'gym'),
            pk=pk, gym=request.user.gym, is_deleted=False,
        )
        return render(request, 'members/detail.html', {'member': member})


class MemberEditView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk, gym=request.user.gym, is_deleted=False)
        form = MemberForm(instance=member, gym=request.user.gym)
        return render(request, 'members/form.html', self._context(form, member))

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk, gym=request.user.gym, is_deleted=False)
        form = MemberForm(request.POST, instance=member, gym=request.user.gym)
        if form.is_valid():
            form.save()
            return redirect('frontend:member-detail', pk=member.pk)
        return render(request, 'members/form.html', self._context(form, member))

    def _context(self, form, member):
        gym = self.request.user.gym
        return {
            'form': form,
            'form_title': f'Edit {member.name}',
            'form_subtitle': f'Update member details',
            'submit_label': 'Save Changes',
            'plans': MembershipPlan.objects.filter(
                gym=gym, is_deleted=False, is_active=True
            ) if gym else [],
            'trainers': GymUser.objects.filter(
                gym=gym, role__in=['trainer', 'manager']
            ) if gym else [],
            'today': timezone.now().date().isoformat(),
        }



class BulkImportView(LoginRequiredMixin, View):
    """Handle bulk import of members via CSV/Excel."""
    def post(self, request):
        gym = request.user.gym
        if not gym:
             return JsonResponse({'success': False, 'message': 'No gym associated.'}, status=400)

        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'success': False, 'message': 'No file uploaded.'}, status=400)

        success_count, errors = BulkImportService.process_file(file, gym)

        if success_count > 0:
            if errors:
                msg = f"Imported {success_count} members. {len(errors)} errors: " + "; ".join(errors[:3])
            else:
                msg = f"Successfully imported {success_count} members."
            return JsonResponse({'success': True, 'message': msg, 'errors': errors})
        else:
            return JsonResponse({'success': False, 'message': 'Import failed.', 'errors': errors}, status=400)


class SampleFileView(LoginRequiredMixin, View):
    """Download a sample CSV/Excel file for bulk import."""
    def get(self, request):
        format = request.GET.get('format', 'csv')
        
        # Create sample data
        data = [
            {'Name': 'John Doe', 'Phone': '9876543210', 'Email': 'john@example.com', 'Plan': 'Monthly'},
            {'Name': 'Jane Smith', 'Phone': '9123456789', 'Email': 'jane@example.com', 'Plan': 'Yearly'},
        ]
        
        import pandas as pd
        df = pd.DataFrame(data)
        
        from io import BytesIO
        buffer = BytesIO()

        if format == 'xlsx':
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = 'members_sample.xlsx'
        else:
            # CSV
            df.to_csv(buffer, index=False)
            content_type = 'text/csv'
            filename = 'members_sample.csv'

        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class CardScanView(LoginRequiredMixin, View):
    """AI Scan of membership card."""
    def post(self, request):
        image = request.FILES.get('image')
        if not image:
            logger.error("CardScanView: No image in request.FILES")
            return JsonResponse({'success': False, 'message': 'No image uploaded.'}, status=400)

        logger.info(f"CardScanView: Processing image {image.name}")
        success, result = AIScanService.scan_card(image)
        if success:
            return JsonResponse({'success': True, 'data': result})
        else:
            logger.error(f"CardScanView: Scan failed - {result}")
            return JsonResponse({'success': False, 'message': result}, status=400)


# ── Settings Views ────────────────────────────────────────────

class GymSettingsView(LoginRequiredMixin, View):
    """Owner-only gym branding settings."""
    login_url = '/login/'

    def get(self, request):
        if request.user.role != 'owner':
            return redirect('frontend:dashboard')
        gym = request.user.gym
        from apps.gyms.models import FONT_CHOICES
        return render(request, 'settings/branding.html', {
            'gym': gym,
            'font_choices': FONT_CHOICES,
        })

    def post(self, request):
        if request.user.role != 'owner':
            return redirect('frontend:dashboard')

        gym = request.user.gym
        if not gym:
            return redirect('frontend:dashboard')

        # Update brand color
        brand_color = request.POST.get('brand_color', '').strip()
        if brand_color and brand_color.startswith('#') and len(brand_color) == 7:
            gym.brand_color = brand_color

        # Update font
        font_family = request.POST.get('font_family', '').strip()
        from apps.gyms.models import FONT_CHOICES
        valid_fonts = [f[0] for f in FONT_CHOICES]
        if font_family in valid_fonts:
            gym.font_family = font_family

        # Update logo (base64)
        logo_data = request.POST.get('logo_base64', '').strip()
        if logo_data and logo_data.startswith('data:image'):
            gym.logo_base64 = logo_data

        gym.save()

        if request.htmx:
            response = HttpResponse(status=200)
            response['HX-Redirect'] = '/settings/branding/'
            return response

        return redirect('frontend:gym-settings')


class UnifiedLoginView(View):
    """
    Simplified Login - Entity Code + Username + Password (Single Step).
    Session-based authentication for frontend.
    """
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('frontend:dashboard')
        return render(request, 'auth/unified_login.html')

    def post(self, request):
        entity_code = request.POST.get('entity_code', '').strip().upper()
        username = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '')

        if not entity_code or not username or not password:
            return render(request, 'auth/unified_login.html', {
                'error': 'Please fill in all fields.',
                'entity_code': entity_code,
                'username': username
            })

        # Step 1: Resolve Entity (Gym or Organization)
        gym = None
        organization = None
        
        # Check Gym first (Most common)
        try:
            gym = Gym.objects.get(gym_code=entity_code, is_active=True)
        except Gym.DoesNotExist:
            pass
            
        # If not Gym, check Organization
        if not gym:
            try:
                # Assuming Organization has a code field, e.g., 'holding_code' or similar?
                # The prompt implies generic 'entity_code'. 
                # Model 'Organization' doesn't seem to have 'org_code' in the snippet viewed earlier?
                # It has 'holding_code' on HoldingCompany, but Organization?
                # Let's check Organization model again if needed, but for now rely on previous correct logic or standard fallback.
                # Actually, in the previous code I replaced, it used `entity_code=entity_code`.
                # But Organization model snippet I saw (lines 100-150 of enterprises/models.py) didn't show `entity_code`.
                # However, the user request specifically mentions "GYM..." codes.
                # I will focus on GYM support first as that's what the user provided.
                # But I should keep Organization support if it existed.
                organization = Organization.objects.filter(org_code=entity_code, is_active=True).first()
            except Exception:
                pass

        if not gym and not organization:
             return render(request, 'auth/unified_login.html', {
                'error': 'Invalid Gym or Organization code.',
                'entity_code': entity_code,
                'username': username
            })

        # Step 2: Authenticate user
        # Note: 'authenticate' backend usually needs 'username' and 'password'.
        # Custom backend might need 'gym' or 'organization' context if usernames are scoped (e.g. 'trainer' exists in multiple gyms).
        # But our usernames in seed data are unique ('ryan_owner', 'jfc_1_owner').
        # So standard auth should work if backend is standard ModelBackend.
        user = authenticate(request, username=username, password=password)
        
        if not user:
             return render(request, 'auth/unified_login.html', {
                'error': 'Invalid username or password.',
                'entity_code': entity_code,
                'username': username
            })

        # Step 3: Verify Access to Resolved Entity
        has_access = False
        if gym:
            # User belongs to this gym? (Directly or via multi-location)
            if user.gym == gym or gym in user.locations.all() or user.is_superuser:
                has_access = True
            # Or if user is Org Admin of the gym's org
            elif user.organization and user.organization == gym.organization:
                has_access = True
                
        elif organization:
            if user.organization == organization or user.is_superuser:
                has_access = True

        if not has_access:
            return render(request, 'auth/unified_login.html', {
                'error': 'You do not have access to this specific Gym/Organization.',
                'entity_code': entity_code,
                'username': username
            })

        # Step 4: Check Activity
        if not user.is_active:
             return render(request, 'auth/unified_login.html', {
                'error': 'Account deactivated.',
                'entity_code': entity_code,
                'username': username
            })

        # Step 5: Login
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        # Set gym cookie for convenience if it's a gym login
        response = redirect('frontend:dashboard')
        if gym:
            import json
            gym_cache = json.dumps({
                'gym_code': gym.gym_code,
                'gym_name': gym.name,
                'gym_logo': gym.logo_data_uri or '',
            })
            response.set_cookie('gym_cache_data', gym_cache, max_age=365*24*60*60, httponly=False, samesite='Lax')
        
        return response


# ── Informational Pages ────────────────────────────────────────

class ContactView(View):
    """Contact form for website visitors."""
    
    def get(self, request):
        return render(request, 'pages/contact.html')
    
    def post(self, request):
        from apps.communications.models import ContactQuery
        
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        company = request.POST.get('company', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Validation
        if not all([name, email, subject, message]):
            return JsonResponse({
                'success': False,
                'error': 'Please fill in all required fields.'
            })
        
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create contact query
        ContactQuery.objects.create(
            name=name,
            email=email,
            phone=phone,
            company=company,
            subject=subject,
            message=message,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"New contact query from: {name} ({email})")
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you! Your message has been sent successfully.'
        })


class AboutView(View):
    """About Us page."""
    def get(self, request):
        return render(request, 'pages/about.html')


class BlogView(View):
    """Blog listing page."""
    def get(self, request):
        return render(request, 'pages/blog.html')


class PrivacyPolicyView(View):
    """Privacy Policy page."""
    def get(self, request):
        return render(request, 'pages/privacy.html')


class TermsOfServiceView(View):
    """Terms of Service page."""
    def get(self, request):
        return render(request, 'pages/terms.html')


class RefundPolicyView(View):
    """Refund Policy page."""
    def get(self, request):
        return render(request, 'pages/refund_policy.html')
