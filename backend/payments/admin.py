from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("receipt_no", "member", "amount", "method", "status", "paid_on")
    list_filter = ("status", "method")
    search_fields = ("receipt_no", "member__full_name", "member__member_code")
    readonly_fields = ("receipt_no",)
