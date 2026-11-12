from django.core.management.base import BaseCommand

from plans.models import Membership


class Command(BaseCommand):
    help = "Mark memberships whose end date has passed as EXPIRED (safe to run daily)."

    def handle(self, *args, **options):
        updated = Membership.objects.sync_expired()
        self.stdout.write(self.style.SUCCESS(f"{updated} membership(s) marked as expired."))
