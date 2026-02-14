"""
Fitness Admin - WorkoutPlan, DietPlan, Attendance, ProgressLog with import/export.
"""

from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.fitness.models import WorkoutPlan, DietPlan, Attendance, ProgressLog


# ── WorkoutPlan ───────────────────────────────────────────────

class WorkoutPlanResource(resources.ModelResource):
    class Meta:
        model = WorkoutPlan
        import_id_fields = ['id']
        fields = (
            'id', 'gym', 'member', 'created_by', 'title', 'goal',
            'duration_weeks', 'difficulty', 'ai_model_used',
            'ai_prompt_tokens', 'ai_completion_tokens',
            'is_active', 'created_at',
        )
        export_order = fields


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(ImportExportModelAdmin):
    resource_classes = [WorkoutPlanResource]

    list_display = (
        'title', 'member', 'gym', 'goal', 'difficulty',
        'duration_weeks', 'ai_model_used', 'is_active', 'created_at',
    )
    list_filter = ('difficulty', 'goal', 'ai_model_used', 'is_active', 'gym')
    search_fields = ('title', 'member__name', 'gym__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 25


# ── DietPlan ──────────────────────────────────────────────────

class DietPlanResource(resources.ModelResource):
    class Meta:
        model = DietPlan
        import_id_fields = ['id']
        fields = (
            'id', 'gym', 'member', 'created_by', 'title', 'goal',
            'dietary_preference', 'daily_calories',
            'daily_protein_g', 'daily_carbs_g', 'daily_fat_g',
            'ai_model_used', 'is_active', 'created_at',
        )
        export_order = fields


@admin.register(DietPlan)
class DietPlanAdmin(ImportExportModelAdmin):
    resource_classes = [DietPlanResource]

    list_display = (
        'title', 'member', 'gym', 'goal', 'dietary_preference',
        'daily_calories', 'ai_model_used', 'is_active', 'created_at',
    )
    list_filter = ('dietary_preference', 'goal', 'ai_model_used', 'is_active', 'gym')
    search_fields = ('title', 'member__name', 'gym__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 25


# ── Attendance ────────────────────────────────────────────────

class AttendanceResource(resources.ModelResource):
    class Meta:
        model = Attendance
        import_id_fields = ['id']
        fields = (
            'id', 'gym', 'member', 'check_in', 'check_out',
            'duration_minutes', 'created_at',
        )
        export_order = fields


@admin.register(Attendance)
class AttendanceAdmin(ImportExportModelAdmin):
    resource_classes = [AttendanceResource]

    list_display = (
        'member', 'gym', 'check_in', 'check_out',
        'duration_minutes', 'created_at',
    )
    list_filter = ('gym',)
    search_fields = ('member__name', 'member__phone', 'gym__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 50
    date_hierarchy = 'check_in'


# ── ProgressLog ───────────────────────────────────────────────

class ProgressLogResource(resources.ModelResource):
    class Meta:
        model = ProgressLog
        import_id_fields = ['id']
        fields = (
            'id', 'gym', 'member', 'recorded_by', 'date',
            'weight_kg', 'body_fat_pct', 'muscle_mass_kg', 'bmi',
            'chest_cm', 'waist_cm', 'hips_cm', 'biceps_cm', 'thighs_cm',
            'created_at',
        )
        export_order = fields


@admin.register(ProgressLog)
class ProgressLogAdmin(ImportExportModelAdmin):
    resource_classes = [ProgressLogResource]

    list_display = (
        'member', 'gym', 'date', 'weight_kg', 'body_fat_pct',
        'muscle_mass_kg', 'bmi',
    )
    list_filter = ('gym',)
    search_fields = ('member__name', 'gym__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 25
    date_hierarchy = 'date'
