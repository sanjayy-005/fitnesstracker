from collections import Counter
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Role
from core.permissions import ADMIN_STAFF, ALL_ROLES, RolePermission
from plans.models import Membership

from .filters import AttendanceFilter
from .models import Attendance, current_time
from .serializers import AttendanceSerializer, CheckInSerializer


class AttendanceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Attendance tracking.

    POST /api/attendance/check-in/        {"member": id}
    POST /api/attendance/{id}/check-out/
    GET  /api/attendance/report/?days=30  daily counts, top members, peak hours
    """

    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    read_roles = ALL_ROLES
    write_roles = ADMIN_STAFF
    action_roles = {
        "check_in": ALL_ROLES,
        "check_out": ALL_ROLES,
        "report": ALL_ROLES,
        "destroy": ADMIN_STAFF,
    }
    filterset_class = AttendanceFilter
    search_fields = ["member__full_name", "member__member_code", "member__phone"]
    ordering_fields = ["date", "check_in", "check_out"]
    ordering = ["-date", "-check_in", "-id"]

    def get_queryset(self):
        queryset = Attendance.objects.select_related("member")
        if self.request.user.role == Role.TRAINER:
            queryset = queryset.filter(member__trainer__user=self.request.user)
        return queryset

    @action(detail=False, methods=["post"], url_path="check-in")
    def check_in(self, request):
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = serializer.validated_data["member"]
        today = timezone.localdate()

        if request.user.role == Role.TRAINER and (
            member.trainer is None or member.trainer.user_id != request.user.id
        ):
            raise PermissionDenied("You can only check in members assigned to you.")
        if not member.is_active:
            raise ValidationError({"member": "This member is inactive."})

        Membership.objects.sync_expired()
        has_active_membership = Membership.objects.filter(
            member=member, status=Membership.Status.ACTIVE, end_date__gte=today
        ).exists()
        if not has_active_membership:
            raise ValidationError({"member": "No active membership. Renew the membership before check-in."})
        if Attendance.objects.filter(member=member, date=today).exists():
            raise ValidationError({"member": "This member has already checked in today."})

        record = Attendance.objects.create(
            member=member, date=today, check_in=current_time(), marked_by=request.user
        )
        return Response(AttendanceSerializer(record).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="check-out")
    def check_out(self, request, pk=None):
        record = self.get_object()
        if record.check_out:
            raise ValidationError({"detail": "This member has already checked out."})
        if record.date != timezone.localdate():
            raise ValidationError({"detail": "Check-out is only available for today's visits."})
        record.check_out = max(current_time(), record.check_in)
        record.save(update_fields=["check_out"])
        return Response(AttendanceSerializer(record).data)

    @action(detail=False, methods=["get"])
    def report(self, request):
        try:
            days = int(request.query_params.get("days", 30))
        except ValueError:
            days = 30
        days = min(max(days, 1), 365)

        today = timezone.localdate()
        start = today - timedelta(days=days - 1)
        records = self.get_queryset().filter(date__gte=start, date__lte=today)

        counts = {
            row["date"]: row["count"]
            for row in records.values("date").annotate(count=Count("id")).order_by("date")
        }
        daily = []
        for offset in range(days):
            day = start + timedelta(days=offset)
            daily.append({"date": day, "count": counts.get(day, 0)})

        total_visits = sum(counts.values())
        # order_by() clears the default ordering, otherwise DISTINCT would include those columns.
        unique_members = records.order_by().values("member").distinct().count()

        top_members = [
            {
                "member": row["member"],
                "name": row["member__full_name"],
                "code": row["member__member_code"],
                "visits": row["visits"],
            }
            for row in records.values("member", "member__full_name", "member__member_code")
            .annotate(visits=Count("id"))
            .order_by("-visits", "member__full_name")[:5]
        ]

        hour_counter = Counter(check_in.hour for check_in in records.values_list("check_in", flat=True))
        peak_hours = [{"hour": hour, "count": hour_counter.get(hour, 0)} for hour in range(5, 23)]

        return Response(
            {
                "days": days,
                "start_date": start,
                "end_date": today,
                "total_visits": total_visits,
                "unique_members": unique_members,
                "average_per_day": round(total_visits / days, 1),
                "daily": daily,
                "top_members": top_members,
                "peak_hours": peak_hours,
            }
        )
