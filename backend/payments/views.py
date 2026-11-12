from decimal import Decimal

from django.conf import settings
from django.db.models import Count, Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import ADMIN_ONLY, ADMIN_STAFF, RolePermission

from .filters import PaymentFilter
from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    """
    Payment records, history and receipts (admin + front desk staff).

    GET /api/payments/summary/      totals for the current filters
    GET /api/payments/{id}/receipt/ everything needed to print a receipt
    """

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    read_roles = ADMIN_STAFF
    write_roles = ADMIN_STAFF
    action_roles = {"destroy": ADMIN_ONLY}
    filterset_class = PaymentFilter
    search_fields = ["receipt_no", "member__full_name", "member__member_code", "member__phone"]
    ordering_fields = ["paid_on", "amount", "id", "created_at"]
    ordering = ["-paid_on", "-id"]

    def get_queryset(self):
        return Payment.objects.select_related("member", "membership__plan", "received_by")

    def perform_create(self, serializer):
        serializer.save(received_by=self.request.user)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        zero = Decimal("0")

        def total_for(status):
            return queryset.filter(status=status).aggregate(total=Sum("amount"))["total"] or zero

        return Response(
            {
                "total_collected": float(total_for(Payment.Status.PAID)),
                "total_pending": float(total_for(Payment.Status.PENDING)),
                "total_refunded": float(total_for(Payment.Status.REFUNDED)),
                "count": queryset.aggregate(c=Count("id"))["c"],
            }
        )

    @action(detail=True, methods=["get"])
    def receipt(self, request, pk=None):
        payment = self.get_object()
        membership = payment.membership
        return Response(
            {
                "receipt_no": payment.receipt_no,
                "date": payment.paid_on,
                "status": payment.status,
                "method": payment.get_method_display(),
                "amount": payment.amount,
                "note": payment.note,
                "received_by": payment.received_by.full_name if payment.received_by_id else None,
                "gym": {
                    "name": settings.GYM_NAME,
                    "address": settings.GYM_ADDRESS,
                    "phone": settings.GYM_PHONE,
                    "email": settings.GYM_EMAIL,
                },
                "member": {
                    "name": payment.member.full_name,
                    "code": payment.member.member_code,
                    "phone": payment.member.phone,
                    "email": payment.member.email,
                },
                "membership": (
                    {
                        "plan": membership.plan.name,
                        "plan_type": membership.plan.get_plan_type_display(),
                        "start_date": membership.start_date,
                        "end_date": membership.end_date,
                    }
                    if membership
                    else None
                ),
            }
        )
