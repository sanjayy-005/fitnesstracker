from django.contrib import admin

from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("member_code", "full_name", "phone", "trainer", "is_active", "joined_date")
    search_fields = ("full_name", "email", "phone", "member_code")
    list_filter = ("is_active", "gender", "trainer")
    readonly_fields = ("member_code",)
