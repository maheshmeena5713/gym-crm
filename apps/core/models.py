"""
Core app - Base model and utilities for Gym AI SaaS.
All models in the project inherit from BaseModel.
"""
import uuid

from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """
    Abstract base model providing UUID primary key, timestamps, and soft delete.
    Every model in the project inherits from this.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
        help_text="Unique identifier (UUID v4)",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
        help_text="Timestamp when the record was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
        help_text="Timestamp when the record was last updated",
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Is Deleted",
        help_text="Soft delete flag. If True, the record is considered deleted.",
        db_index=True,
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Deleted At",
        help_text="Timestamp when the record was soft-deleted",
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self):
        """Mark this record as deleted without removing from the database."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])


class ActiveManager(models.Manager):
    """Manager that filters out soft-deleted records by default."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
