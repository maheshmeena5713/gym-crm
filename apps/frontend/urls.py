"""Frontend URL routes - auth, dashboard, members, settings."""

from django.urls import path

from apps.frontend import views

app_name = 'frontend'

urlpatterns = [
    # ── Landing Page ──────────────────────────────────────
    path('', views.LandingPageView.as_view(), name='landing'),

    # ── Auth (3-step: Gym Code → Phone →    # ── Simplified Unified Login (Primary) ──────────────
    path('login/', views.UnifiedLoginView.as_view(), name='unified-login'),

    # ── Auth (Legacy Multi-Step: OTP Flow) ──────────────
    path('auth/login/', views.LoginView.as_view(), name='login'),
    # Renamed view, kept URL for compatibility (or we can change it to validate-entity-code)
    path('auth/validate-gym-code/', views.ValidateEntityCodeView.as_view(), name='validate-gym-code'),
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

    # ── Enterprise Login (No Gym Code) ────────────────────
    path('enterprise/login/', views.EnterpriseLoginView.as_view(), name='enterprise-login'),

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
    
    # ── Informational Pages ───────────────────────────────
    path('about/', views.AboutView.as_view(), name='about'),
    path('blog/', views.BlogView.as_view(), name='blog'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('privacy/', views.PrivacyPolicyView.as_view(), name='privacy'),
    path('terms/', views.TermsOfServiceView.as_view(), name='terms'),
    path('refund-policy/', views.RefundPolicyView.as_view(), name='refund-policy'),
    
    # ── WhatsApp Integration ──────────────────────────────
    path('whatsapp/', views.WhatsAppDashboardView.as_view(), name='whatsapp-dashboard'),
    path('whatsapp/broadcast/', views.WhatsAppBroadcastView.as_view(), name='whatsapp-broadcast'),
    path('whatsapp/templates/', views.WhatsAppTemplatesView.as_view(), name='whatsapp-templates'),
    path('whatsapp/logs/', views.WhatsAppLogsView.as_view(), name='whatsapp-logs'),
]
