from django.urls import path
from .views import HoldingDashboardView, OrganizationDashboardView, RoyaltyReportView

app_name = 'enterprises'

urlpatterns = [
    path('dashboard/holding/', HoldingDashboardView.as_view(), name='holding-dashboard'),
    path('dashboard/organization/', OrganizationDashboardView.as_view(), name='org-dashboard'),
    path('royalties/', RoyaltyReportView.as_view(), name='royalty-report'),
]
