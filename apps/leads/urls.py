from django.urls import path
from .views import LeadListView, LeadCreateView, LeadUpdateView

app_name = 'leads'

urlpatterns = [
    path('', LeadListView.as_view(), name='lead-list'),
    path('add/', LeadCreateView.as_view(), name='lead-create'),
    path('<uuid:pk>/edit/', LeadUpdateView.as_view(), name='lead-update'),
]
