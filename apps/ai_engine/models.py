"""
AI Engine App - AIUsageLog Model
Track every AI call per gym. Critical for cost control and billing.
"""

from django.db import models

from apps.core.models import BaseModel, ActiveManager


