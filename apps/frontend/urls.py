"""Frontend URL routes - auth, dashboard, members, settings."""

from django.urls import path

from apps.frontend import views

app_name = 'frontend'

urlpatterns = [
    # ── Landing Page ──────────────────────────────────────
    path('', views.LandingPageView.as_view(), name='landing'),

    # ── Auth (3-step: Gym Code → Phone → OTP) ────────────
    path('login/', views.LoginView.as_view(), name='login'),
    path('auth/validate-gym-code/', views.ValidateGymCodeView.as_view(), name='validate-gym-code'),
    path('auth/send-otp/', views.SendOTPView.as_view(), name='send-otp'),
    path('auth/verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # ── Signup (New Gym Owners) ───────────────────────────
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('signup/send-otp/', views.SignupSendOTPView.as_view(), name='signup-send-otp'),
    path('signup/verify-otp/', views.SignupVerifyOTPView.as_view(), name='signup-verify-otp'),
    path('signup/check-username/', views.CheckUsernameView.as_view(), name='check-username'),

    # ── Password Login ────────────────────────────────────
    path('auth/password-login/', views.PasswordLoginView.as_view(), name='password-login'),

    # ── Dashboard ─────────────────────────────────────────
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('business-health/', views.BusinessHealthView.as_view(), name='business-health'),

    # ── Members ───────────────────────────────────────────
    path('members/', views.MemberListView.as_view(), name='member-list'),
    path('members/add/', views.MemberCreateView.as_view(), name='member-add'),
    path('members/import/', views.BulkImportView.as_view(), name='member-import'),
    path('members/import/sample/', views.SampleFileView.as_view(), name='member-import-sample'),
    path('members/scan-card/', views.CardScanView.as_view(), name='member-scan-card'),
    path('members/<uuid:pk>/', views.MemberDetailView.as_view(), name='member-detail'),
    path('members/<uuid:pk>/edit/', views.MemberEditView.as_view(), name='member-edit'),

    # ── Settings (Owner Only) ─────────────────────────────
    path('settings/branding/', views.GymSettingsView.as_view(), name='gym-settings'),
]
