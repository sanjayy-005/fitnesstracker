import django_filters

from .models import Attendance


class AttendanceFilter(django_filters.FilterSet):
    """
    /api/attendance/?date=2026-01-15
    /api/attendance/?date_from=2026-01-01&date_to=2026-01-31&member=4
    /api/attendance/?still_inside=true   (checked in but not checked out)
    """

    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    still_inside = django_filters.BooleanFilter(field_name="check_out", lookup_expr="isnull")

    class Meta:
        model = Attendance
        fields = ["member", "date"]
