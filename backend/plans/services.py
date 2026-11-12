"""Business logic for selling and renewing memberships."""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from payments.models import Payment

from .models import Membership


@transaction.atomic
def create_membership(
    *,
    member,
    plan,
    start_date=None,
    record_payment=True,
    payment_method=None,
    amount=None,
    user=None,
):
    """
    Create a membership (and optionally the matching payment) in one step.

    * If `start_date` is omitted and the member still has an active membership,
      the new one starts the day after it ends (a seamless renewal).
      Otherwise it starts today.
    * The end date is inclusive: a 30 day plan starting on the 1st ends on the 30th.
    """
    today = timezone.localdate()

    if start_date is None:
        current = (
            Membership.objects.filter(member=member, status=Membership.Status.ACTIVE, end_date__gte=today)
            .order_by("-end_date")
            .first()
        )
        start_date = current.end_date + timedelta(days=1) if current else today

    end_date = start_date + timedelta(days=plan.duration_days - 1)
    status = Membership.Status.EXPIRED if end_date < today else Membership.Status.ACTIVE

    membership = Membership.objects.create(
        member=member,
        plan=plan,
        start_date=start_date,
        end_date=end_date,
        price=plan.price,
        status=status,
        created_by=user,
    )

    if record_payment:
        Payment.objects.create(
            member=member,
            membership=membership,
            amount=amount or plan.price,
            method=payment_method,
            status=Payment.Status.PAID,
            paid_on=today,
            received_by=user,
            note=f"{plan.name} membership",
        )

    return membership
