from datetime import timedelta

import django_filters
from django.db.models import Exists, OuterRef
from django.utils import timezone

from plans.models import Membership

from .models import Member


def active_membership_qs(today):
    """Memberships (of the outer Member row) that are currently valid."""
    return Membership.objects.filter(
        member=OuterRef("pk"),
        status=Membership.Status.ACTIVE,
        end_date__gte=today,
    )


def any_membership_qs():
    """Memberships (of the outer Member row) that were not cancelled."""
    return Membership.objects.filter(member=OuterRef("pk")).exclude(status=Membership.Status.CANCELLED)


class MemberFilter(django_filters.FilterSet):
    """
    /api/members/?membership_status=ACTIVE|EXPIRING|EXPIRED|NONE
                 &trainer=3  &trainer_isnull=true  &gender=F  &is_active=true
    """

    membership_status = django_filters.CharFilter(method="filter_membership_status")
    trainer_isnull = django_filters.BooleanFilter(field_name="trainer", lookup_expr="isnull")

    class Meta:
        model = Member
        fields = ["is_active", "gender", "trainer"]

    def filter_membership_status(self, queryset, name, value):
        value = (value or "").upper()
        today = timezone.localdate()
        active = active_membership_qs(today)

        if value == "ACTIVE":
            return queryset.filter(Exists(active))
        if value == "EXPIRING":
            # Active, but no membership that runs for longer than the next 7 days.
            limit = today + timedelta(days=7)
            return queryset.filter(Exists(active)).filter(~Exists(active.filter(end_date__gt=limit)))
        if value == "EXPIRED":
            return queryset.filter(Exists(any_membership_qs())).filter(~Exists(active))
        if value == "NONE":
            return queryset.filter(~Exists(any_membership_qs()))
        return queryset
