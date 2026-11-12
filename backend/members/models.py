from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from core.validators import phone_validator


class Member(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="member_profile",
    )
    nutrition_consent_at = models.DateTimeField(null=True, blank=True)
    # Generated automatically after the first save, e.g. FT00042.
    member_code = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, validators=[phone_validator])
    gender = models.CharField(max_length=1, choices=Gender.choices, default=Gender.MALE)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, validators=[phone_validator])
    height_cm = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(50), MaxValueValidator(260)]
    )
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(400)],
    )
    trainer = models.ForeignKey(
        "trainers.Trainer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="members",
    )
    joined_date = models.DateField(default=timezone.localdate)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.member_code:
            self.member_code = f"FT{self.pk:05d}"
            super().save(update_fields=["member_code"])

    def __str__(self):
        return f"{self.full_name} ({self.member_code})"
