from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class MembershipPlan(models.Model):
    """A plan the gym sells: monthly, quarterly or yearly."""

    class PlanType(models.TextChoices):
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        YEARLY = "YEARLY", "Yearly"

    DURATION_DAYS = {"MONTHLY": 30, "QUARTERLY": 90, "YEARLY": 365}

    name = models.CharField(max_length=100, unique=True)
    plan_type = models.CharField(max_length=10, choices=PlanType.choices, default=PlanType.MONTHLY)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1)])
    description = models.TextField(blank=True)
    features = models.TextField(blank=True, help_text="One feature per line.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["price", "name"]

    @property
    def duration_days(self):
        return self.DURATION_DAYS[self.plan_type]

    def __str__(self):
        return f"{self.name} ({self.get_plan_type_display()})"


class MembershipQuerySet(models.QuerySet):
    def sync_expired(self):
        """Flip ACTIVE memberships whose end date has passed to EXPIRED."""
        return self.filter(
            status=Membership.Status.ACTIVE,
            end_date__lt=timezone.localdate(),
        ).update(status=Membership.Status.EXPIRED)


class Membership(models.Model):
    """One purchase of a plan by a member (a renewal creates a new row)."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"
        CANCELLED = "CANCELLED", "Cancelled"

    member = models.ForeignKey("members.Member", on_delete=models.CASCADE, related_name="memberships")
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT, related_name="memberships")
    start_date = models.DateField()
    end_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # price at the time of purchase
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_memberships",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = MembershipQuerySet.as_manager()

    class Meta:
        ordering = ["-end_date", "-id"]
        indexes = [models.Index(fields=["status", "end_date"])]

    @property
    def effective_status(self):
        """Status based on today's date, so it is never stale."""
        if self.status == self.Status.CANCELLED:
            return self.Status.CANCELLED.value
        if self.end_date < timezone.localdate():
            return self.Status.EXPIRED.value
        return self.Status.ACTIVE.value

    @property
    def days_left(self):
        """Days until the end date (negative when already expired)."""
        return (self.end_date - timezone.localdate()).days

    def __str__(self):
        return f"{self.member_id} - {self.plan.name} ({self.start_date} to {self.end_date})"
