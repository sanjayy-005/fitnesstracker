# Generated manually for nutrition app

import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("members", "0002_member_login_and_consent"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FoodScan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("meal_type", models.CharField(default="OTHER", max_length=20)),
                ("note", models.CharField(blank=True, max_length=300)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("SUCCEEDED", "Succeeded"), ("NEEDS_REVIEW", "Needs review"), ("FAILED", "Failed")], default="PENDING", max_length=20)),
                ("provider", models.CharField(blank=True, max_length=40)),
                ("model_name", models.CharField(blank=True, max_length=120)),
                ("prompt_version", models.CharField(blank=True, max_length=20)),
                ("raw_response", models.JSONField(blank=True, null=True)),
                ("analysis", models.JSONField(blank=True, null=True)),
                ("error", models.TextField(blank=True)),
                ("latency_ms", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="food_scans_created", to=settings.AUTH_USER_MODEL)),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="food_scans", to="members.member")),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="MealEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("eaten_on", models.DateField(default=django.utils.timezone.localdate)),
                ("meal_type", models.CharField(choices=[("BREAKFAST", "Breakfast"), ("LUNCH", "Lunch"), ("DINNER", "Dinner"), ("SNACK", "Snack"), ("OTHER", "Other")], default="OTHER", max_length=20)),
                ("source", models.CharField(choices=[("AI", "AI"), ("AI_EDITED", "AI (edited)"), ("MANUAL", "Manual")], default="MANUAL", max_length=20)),
                ("total_kcal", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=8)),
                ("protein_g", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=8)),
                ("carbs_g", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=8)),
                ("fat_g", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=8)),
                ("fiber_g", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=8)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="meal_entries_created", to=settings.AUTH_USER_MODEL)),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="meal_entries", to="members.member")),
                ("scan", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="meal_entry", to="nutrition.foodscan")),
            ],
            options={"ordering": ["-eaten_on", "-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="MealItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("quantity", models.DecimalField(decimal_places=2, default=Decimal("1"), max_digits=8)),
                ("unit", models.CharField(default="serving", max_length=20)),
                ("grams", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ("kcal", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=8)),
                ("protein_g", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=8)),
                ("carbs_g", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=8)),
                ("fat_g", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=8)),
                ("fiber_g", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=8)),
                ("confidence", models.CharField(blank=True, max_length=10)),
                ("was_edited", models.BooleanField(default=False)),
                ("entry", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="nutrition.mealentry")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.AddIndex(
            model_name="foodscan",
            index=models.Index(fields=["member", "created_at"], name="nutrition_f_member__a1c2d3_idx"),
        ),
        migrations.AddIndex(
            model_name="mealentry",
            index=models.Index(fields=["member", "eaten_on"], name="nutrition_m_member__b4e5f6_idx"),
        ),
    ]
