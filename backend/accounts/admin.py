from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (("FitTrack", {"fields": ("role", "phone")}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (("FitTrack", {"fields": ("role", "phone")}),)
    list_display = ("username", "email", "role", "is_active", "is_staff")
    list_filter = DjangoUserAdmin.list_filter + ("role",)
