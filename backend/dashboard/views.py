from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Exists, OuterRef, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Role
from core.permissions import RolePermission, STAFF_ROLES
from attendance.models import Attendance
from members.filters import active_membership_qs, any_membership_qs
from members.models import Member
from payments.models import Payment
from plans.models import Membership
from trainers.models import Trainer


def last_months(today, count):
    """First day of each of the last `count` months, oldest first, ending with this month."""
    months = []
    for back in range(count - 1, -1, -1):
        year, month = today.year, today.month - back
        while month <= 0:
            month += 12
            year -= 1
        months.append(date(year, month, 1))
    return months


def as_date(value):
    """TruncMonth may return a date or a datetime depending on the database."""
    return value.date() if hasattr(value, "date") else value


def money(value):
    return float(value or Decimal("0"))


class DashboardView(APIView):
    """
    GET /api/dashboard/

    Everything the dashboard needs in one request. Revenue figures are only
    included for admins and front desk staff; trainers see statistics for
    their own members only.
    """

    permission_classes = [IsAuthenticated, RolePermission]
    read_roles = STAFF_ROLES
    write_roles = STAFF_ROLES

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        Membership.objects.sync_expired()

        is_trainer = user.role == Role.TRAINER
        can_view_finance = user.role in (Role.ADMIN, Role.STAFF)

        members = Member.objects.all()
        memberships = Membership.objects.all()
        attendance = Attendance.objects.all()
        if is_trainer:
            members = members.filter(trainer__user=user)
            memberships = memberships.filter(member__trainer__user=user)
            attendance = attendance.filter(member__trainer__user=user)

        # ---- member statistics --------------------------------------------
        active_sq = active_membership_qs(today)
        any_sq = any_membership_qs()

        total_members = members.count()
        active_members = members.filter(Exists(active_sq)).count()
        expired_members = members.filter(Exists(any_sq)).filter(~Exists(active_sq)).count()
        new_this_month = members.filter(joined_date__gte=today.replace(day=1)).count()

        expiring_limit = today + timedelta(days=7)
        expiring_qs = (
            memberships.filter(
                status=Membership.Status.ACTIVE, end_date__gte=today, end_date__lte=expiring_limit
            )
            .filter(
                ~Exists(
                    Membership.objects.filter(
                        member=OuterRef("member"),
                        status=Membership.Status.ACTIVE,
                        end_date__gt=OuterRef("end_date"),
                    )
                )
            )
            .select_related("member", "plan")
            .order_by("end_date", "id")
        )
        expiring_soon = [
            {
                "id": m.id,
                "member": m.member_id,
                "member_name": m.member.full_name,
                "member_code": m.member.member_code,
                "plan_name": m.plan.name,
                "end_date": m.end_date,
                "days_left": m.days_left,
            }
            for m in expiring_qs[:6]
        ]

        today_visits = attendance.filter(date=today)
        data = {
            "can_view_finance": can_view_finance,
            "stats": {
                "total_members": total_members,
                "active_members": active_members,
                "expired_members": expired_members,
                "no_membership_members": max(total_members - active_members - expired_members, 0),
                "expiring_soon": expiring_qs.count(),
                "new_this_month": new_this_month,
                "total_trainers": Trainer.objects.filter(is_active=True).count(),
                "today_checkins": today_visits.count(),
                "currently_inside": today_visits.filter(check_out__isnull=True).count(),
            },
            "expiring_soon": expiring_soon,
        }

        # ---- plan distribution (active memberships per plan) ---------------
        distribution = (
            memberships.filter(status=Membership.Status.ACTIVE, end_date__gte=today)
            .values("plan__name")
            .annotate(count=Count("id"))
            .order_by("-count", "plan__name")
        )
        data["plan_distribution"] = [{"name": row["plan__name"], "value": row["count"]} for row in distribution]

        # ---- member growth: last 6 months ----------------------------------
        months = last_months(today, 6)
        first_month = months[0]
        joined_before = members.filter(joined_date__lt=first_month).count()
        joined_rows = (
            members.filter(joined_date__gte=first_month)
            .annotate(month=TruncMonth("joined_date"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        joined_by_month = {as_date(row["month"]): row["count"] for row in joined_rows}
        growth, running_total = [], joined_before
        for month in months:
            new_members = joined_by_month.get(month, 0)
            running_total += new_members
            growth.append({"month": month.strftime("%b %Y"), "new": new_members, "total": running_total})
        data["member_growth"] = growth

        # ---- attendance: last 14 days ----------------------------------------
        trend_start = today - timedelta(days=13)
        visit_rows = (
            attendance.filter(date__gte=trend_start, date__lte=today)
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        visits_by_day = {row["date"]: row["count"] for row in visit_rows}
        data["attendance_trend"] = [
            {
                "date": (trend_start + timedelta(days=i)).isoformat(),
                "label": (trend_start + timedelta(days=i)).strftime("%d %b"),
                "count": visits_by_day.get(trend_start + timedelta(days=i), 0),
            }
            for i in range(14)
        ]

        data["recent_members"] = [
            {
                "id": m.id,
                "full_name": m.full_name,
                "member_code": m.member_code,
                "joined_date": m.joined_date,
            }
            for m in members.order_by("-created_at", "-id")[:5]
        ]

        # ---- finance (admin / staff only) --------------------------------------
        if can_view_finance:
            paid = Payment.objects.filter(status=Payment.Status.PAID)
            month_start = today.replace(day=1)
            last_month_start = last_months(today, 2)[0]

            revenue_this_month = paid.filter(paid_on__gte=month_start).aggregate(t=Sum("amount"))["t"]
            revenue_last_month = paid.filter(
                paid_on__gte=last_month_start, paid_on__lt=month_start
            ).aggregate(t=Sum("amount"))["t"]

            revenue_rows = (
                paid.filter(paid_on__gte=first_month)
                .annotate(month=TruncMonth("paid_on"))
                .values("month")
                .annotate(total=Sum("amount"))
                .order_by("month")
            )
            revenue_by_month = {as_date(row["month"]): row["total"] for row in revenue_rows}

            method_rows = (
                paid.filter(paid_on__gte=month_start)
                .values("method")
                .annotate(total=Sum("amount"))
                .order_by("-total")
            )
            method_labels = dict(Payment.Method.choices)

            data["finance"] = {
                "revenue_today": money(paid.filter(paid_on=today).aggregate(t=Sum("amount"))["t"]),
                "revenue_this_month": money(revenue_this_month),
                "revenue_last_month": money(revenue_last_month),
                "total_revenue": money(paid.aggregate(t=Sum("amount"))["t"]),
                "pending_amount": money(
                    Payment.objects.filter(status=Payment.Status.PENDING).aggregate(t=Sum("amount"))["t"]
                ),
            }
            data["monthly_revenue"] = [
                {"month": month.strftime("%b %Y"), "revenue": money(revenue_by_month.get(month))}
                for month in months
            ]
            data["revenue_by_method"] = [
                {"name": method_labels.get(row["method"], row["method"]), "value": money(row["total"])}
                for row in method_rows
            ]
            data["recent_payments"] = [
                {
                    "id": p.id,
                    "receipt_no": p.receipt_no,
                    "member_name": p.member.full_name,
                    "amount": money(p.amount),
                    "status": p.status,
                    "method": p.get_method_display(),
                    "paid_on": p.paid_on,
                }
                for p in Payment.objects.select_related("member").order_by("-paid_on", "-id")[:5]
            ]

        return Response(data)
