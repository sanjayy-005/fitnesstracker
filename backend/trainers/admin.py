from django.contrib import admin

from .models import Trainer


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "specialization", "phone", "is_active")
    search_fields = ("full_name", "email", "phone")
    list_filter = ("is_active",)
