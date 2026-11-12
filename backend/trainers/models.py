from django.conf import settings
from django.db import models
from django.utils import timezone

from core.validators import phone_validator


class Trainer(models.Model):
    """A gym trainer. Optionally linked to a login account (role = TRAINER)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="trainer_profile",
    )
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, validators=[phone_validator])
    specialization = models.CharField(max_length=100)
    experience_years = models.PositiveSmallIntegerField(default=0)
    bio = models.TextField(blank=True)
    joined_date = models.DateField(default=timezone.localdate)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name
