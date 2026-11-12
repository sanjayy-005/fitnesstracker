from datetime import timedelta

import django_filters
from django.utils import timezone

from .models import Membership


class MembershipFilter(django_filters.FilterSet):
    """
    /api/memberships/?status=ACTIVE&plan=2&member=5&expiring_in=7
    expiring_in=N -> active memberships that end within the next N days.
    """

    expiring_in = django_filters.NumberFilter(method="filter_expiring_in")

    class Meta:
        model = Membership
        fields = ["status", "plan", "member", "plan__plan_type"]

    def filter_expiring_in(self, queryset, name, value):
        today = timezone.localdate()
        return queryset.filter(
            status=Membership.Status.ACTIVE,
            end_date__gte=today,
            end_date__lte=today + timedelta(days=int(value)),
        )
