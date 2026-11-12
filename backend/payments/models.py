from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"
        UPI = "UPI", "UPI"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"

    class Status(models.TextChoices):
        PAID = "PAID", "Paid"
        PENDING = "PENDING", "Pending"
        REFUNDED = "REFUNDED", "Refunded"

    # Generated automatically after the first save, e.g. RCP-000015.
    receipt_no = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False)
    member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="payments")
    membership = models.ForeignKey(
        "plans.Membership",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    method = models.CharField(max_length=15, choices=Method.choices, default=Method.CASH)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PAID)
    paid_on = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=255, blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="received_payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_on", "-id"]
        indexes = [models.Index(fields=["status", "paid_on"])]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.receipt_no:
            self.receipt_no = f"RCP-{self.pk:06d}"
            super().save(update_fields=["receipt_no"])

    def __str__(self):
        return f"{self.receipt_no} - {self.amount}"
