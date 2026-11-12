import django_filters

from .models import Payment


class PaymentFilter(django_filters.FilterSet):
    """/api/payments/?status=PAID&method=UPI&member=3&date_from=2026-01-01&date_to=2026-01-31"""

    date_from = django_filters.DateFilter(field_name="paid_on", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="paid_on", lookup_expr="lte")

    class Meta:
        model = Payment
        fields = ["status", "method", "member", "membership"]
