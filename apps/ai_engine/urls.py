from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import WorkoutPlanViewSet
from . import views

app_name = 'ai_engine'

router = DefaultRouter()
router.register(r'api/v1/ai/workout', WorkoutPlanViewSet, basename='api-workout')

urlpatterns = [
    # UI Routes
    path('dashboard/ai/workout/', views.WorkoutPlanListView.as_view(), name='workout-list'),
    path('dashboard/ai/workout/create/', views.WorkoutPlanCreateView.as_view(), name='workout-create'),
    path('dashboard/ai/workout/<uuid:pk>/', views.WorkoutPlanDetailView.as_view(), name='workout-detail'),

    # API Routes (Included here or in main urls? Let's keep API routes here but maybe use a specific prefix if included)
    # The router generates /api/v1/ai/workout/ and /api/v1/ai/workout/{pk}/
] + router.urls

# Register Diet ViewSet
from .api_views import DietPlanViewSet
router.register(r'api/v1/ai/diet', DietPlanViewSet, basename='api-diet')

urlpatterns += [
    path('dashboard/ai/diet/', views.DietPlanListView.as_view(), name='diet-list'),
    path('dashboard/ai/diet/create/', views.DietPlanCreateView.as_view(), name='diet-create'),
    path('dashboard/ai/diet/<uuid:pk>/', views.DietPlanDetailView.as_view(), name='diet-detail'),
]
