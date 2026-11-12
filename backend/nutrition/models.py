from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from members.models import Member


class FoodScan(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        NEEDS_REVIEW = "NEEDS_REVIEW", "Needs review"
        FAILED = "FAILED", "Failed"

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="food_scans")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="food_scans_created",
    )
    meal_type = models.CharField(max_length=20, default="OTHER")
    note = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    provider = models.CharField(max_length=40, blank=True)
    model_name = models.CharField(max_length=120, blank=True)
    prompt_version = models.CharField(max_length=20, blank=True)
    raw_response = models.JSONField(null=True, blank=True)
    analysis = models.JSONField(null=True, blank=True)
    error = models.TextField(blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["member", "created_at"])]


class MealEntry(models.Model):
    class MealType(models.TextChoices):
        BREAKFAST = "BREAKFAST", "Breakfast"
        LUNCH = "LUNCH", "Lunch"
        DINNER = "DINNER", "Dinner"
        SNACK = "SNACK", "Snack"
        OTHER = "OTHER", "Other"

    class Source(models.TextChoices):
        AI = "AI", "AI"
        AI_EDITED = "AI_EDITED", "AI (edited)"
        MANUAL = "MANUAL", "Manual"

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="meal_entries")
    scan = models.OneToOneField(
        FoodScan,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="meal_entry",
    )
    eaten_on = models.DateField(default=timezone.localdate)
    meal_type = models.CharField(max_length=20, choices=MealType.choices, default=MealType.OTHER)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    total_kcal = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    protein_g = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    carbs_g = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    fat_g = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    fiber_g = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="meal_entries_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-eaten_on", "-created_at", "-id"]
        indexes = [models.Index(fields=["member", "eaten_on"])]


class MealItem(models.Model):
    entry = models.ForeignKey(MealEntry, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("1"))
    unit = models.CharField(max_length=20, default="serving")
    grams = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    kcal = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    protein_g = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    carbs_g = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    fat_g = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    fiber_g = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    confidence = models.CharField(max_length=10, blank=True)
    was_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]
