from django.conf import settings
from django.db import models
from django.utils import timezone


def current_time():
    """Current local time without microseconds (used as the default check-in time)."""
    return timezone.localtime().time().replace(microsecond=0)


class Attendance(models.Model):
    """One gym visit. A member can have at most one record per day."""

    member = models.ForeignKey("members.Member", on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField(default=timezone.localdate)
    check_in = models.TimeField(default=current_time)
    check_out = models.TimeField(null=True, blank=True)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="marked_attendance",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-check_in", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["member", "date"], name="unique_attendance_per_member_per_day"),
        ]

    def __str__(self):
        return f"{self.member_id} on {self.date}"
