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
from django.utils import timezone
from django.views import View

from apps.gyms.models import Gym
from apps.members.models import Member, MembershipPlan
from apps.users.models import GymUser
from apps.users.services import OTPService
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
        return render(request, 'landing.html')


# ── Auth Views ────────────────────────────────────────────────

class LoginView(View):
    """Step 1: Show gym code form."""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('frontend:dashboard')
        if request.htmx:
            return render(request, 'auth/gym_code_form.html')
        return render(request, 'auth/login.html')


class ValidateGymCodeView(View):
    """Validate gym code and return branded phone form (Step 2)."""
    def post(self, request):
        code = request.POST.get('gym_code', '').strip().upper()
        if not code:
            return render(request, 'auth/gym_code_form.html', {
                'error': 'Please enter your gym code.'
            })

        try:
            gym = Gym.objects.get(gym_code=code, is_active=True)
        except Gym.DoesNotExist:
            return render(request, 'auth/gym_code_form.html', {
                'error': 'Invalid gym code. Please check and try again.',
                'gym_code': code,
            })

        # Store gym in session for subsequent steps
        request.session['login_gym_id'] = str(gym.pk)
        request.session['login_gym_code'] = gym.gym_code

        ctx = _gym_branding_ctx(gym)
        return render(request, 'auth/phone_form.html', ctx)


class SendOTPView(View):
    """Step 2 → 3: Send OTP, return branded OTP form."""
    def post(self, request):
        phone = request.POST.get('phone', '').strip()
        gym_code = request.POST.get('gym_code', '') or request.session.get('login_gym_code', '')

        # Retrieve gym from session
        gym_id = request.session.get('login_gym_id')
        gym = None
        if gym_id:
            try:
                gym = Gym.objects.get(pk=gym_id)
            except Gym.DoesNotExist:
                pass

        ctx = _gym_branding_ctx(gym)

        if not phone or len(phone) < 10:
            ctx['error'] = 'Enter a valid 10-digit number.'
            return render(request, 'auth/phone_form.html', ctx)

        # Check that the phone belongs to a staff user of this gym
        if gym:
            if not GymUser.objects.filter(phone=phone, gym=gym, is_active=True).exists():
                ctx['error'] = 'This phone number is not registered with this gym.'
                ctx['phone'] = phone
                return render(request, 'auth/phone_form.html', ctx)

        success, message = OTPService.send_otp(phone)
        if success:
            ctx['phone'] = phone
            return render(request, 'auth/otp_form.html', ctx)

        ctx['error'] = message
        return render(request, 'auth/phone_form.html', ctx)


class VerifyOTPView(View):
    """Step 3: Verify OTP, login, redirect to dashboard."""
    def post(self, request):
        phone = request.POST.get('phone', '').strip()
        otp = request.POST.get('otp', '').strip()

        # Get gym from session
        gym_id = request.session.get('login_gym_id')
        gym = None
        if gym_id:
            try:
                gym = Gym.objects.get(pk=gym_id)
            except Gym.DoesNotExist:
                pass

        ctx = _gym_branding_ctx(gym)
        ctx['phone'] = phone

        if not phone or not otp:
            ctx['error'] = 'Please enter the OTP.'
            return render(request, 'auth/otp_form.html', ctx)

        success, result = OTPService.verify_otp(phone, otp)
        if not success:
            ctx['error'] = result
            return render(request, 'auth/otp_form.html', ctx)

        user = result['user']

        # Verify user belongs to this gym
        if gym and user.gym_id != gym.pk:
            ctx['error'] = 'This account does not belong to this gym.'
            return render(request, 'auth/otp_form.html', ctx)

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Clean up session login keys
        request.session.pop('login_gym_id', None)
        request.session.pop('login_gym_code', None)

        # Build response with gym info for localStorage caching
        response = HttpResponse(status=200)
        response['HX-Redirect'] = '/dashboard/'

        # Pass gym info as JSON for localStorage via a cookie
        if user.gym:
            import json
            gym_cache = json.dumps({
                'gym_code': user.gym.gym_code,
                'gym_name': user.gym.name,
                'gym_logo': user.gym.logo_data_uri or '',
            })
            response.set_cookie('gym_cache_data', gym_cache, max_age=365*24*60*60, httponly=False, samesite='Lax')

        return response


# ── Signup Views ──────────────────────────────────────────────

class SignupView(View):
    """Render the signup page for new gym owners."""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('frontend:dashboard')
        return render(request, 'auth/signup.html')


class SignupSendOTPView(View):
    """Validate gym details from Step 1 + phone from Step 2, send OTP."""
    def post(self, request):
        # Collect all fields
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

        # Get the Starter plan
        from apps.billing.models import SubscriptionPlan
        starter_plan = SubscriptionPlan.objects.filter(slug='starter').first()

        # Create the Gym
        gym = Gym.objects.create(
            name=signup_data['gym_name'],
            owner_name=signup_data['owner_name'],
            owner_phone=phone,
            email=signup_data['email'],
            city=signup_data.get('city', ''),
            subscription_plan=starter_plan,
            subscription_status='trial',
            trial_ends_at=timezone.now() + timedelta(days=14),
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
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '')

        # Get gym from session (set in Step 1 — gym code)
        gym_id = request.session.get('login_gym_id')
        gym = None
        if gym_id:
            try:
                gym = Gym.objects.get(pk=gym_id)
            except Gym.DoesNotExist:
                pass

        ctx = _gym_branding_ctx(gym)

        if not identifier or not password:
            ctx['pw_error'] = 'Enter your email/username and password.'
            ctx['active_tab'] = 'password'
            return render(request, 'auth/phone_form.html', ctx)

        if not gym:
            ctx['pw_error'] = 'Session expired. Please start from gym code.'
            ctx['active_tab'] = 'password'
            return render(request, 'auth/phone_form.html', ctx)

        user = authenticate(request, gym=gym, identifier=identifier, password=password)

        if not user:
            ctx['pw_error'] = 'Invalid credentials. Check your email/username and password.'
            ctx['active_tab'] = 'password'
            ctx['identifier'] = identifier
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


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('frontend:login')


# ── Dashboard ─────────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        user = request.user
        gym = user.gym

        # Build stats
        if gym:
            members_qs = Member.objects.filter(gym=gym, is_deleted=False)
            stats = {
                'total_members': members_qs.count(),
                'active': members_qs.filter(status='active').count(),
                'expired': members_qs.filter(status='expired').count(),
                'frozen': members_qs.filter(status='frozen').count(),
                'high_churn_risk': members_qs.filter(churn_risk_score__gte=70).count(),
            }
            recent_members = members_qs.order_by('-created_at')[:5]
            # Members expiring in the next 7 days
            week_later = timezone.now().date() + timedelta(days=7)
            expiring_soon = members_qs.filter(
                status='active',
                membership_expiry__lte=week_later,
                membership_expiry__gte=timezone.now().date(),
            ).order_by('membership_expiry')[:10]
        else:
            stats = {}
            recent_members = []
            expiring_soon = []

        return render(request, 'dashboard/index.html', {
            'stats': stats,
            'recent_members': recent_members,
            'expiring_soon': expiring_soon,
        })


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
