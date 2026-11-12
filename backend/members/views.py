from django.db import transaction
from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import Role
from core.permissions import ADMIN_STAFF, ALL_ROLES, RolePermission
from plans.models import Membership

from .filters import MemberFilter
from .models import Member
from .serializers import MemberSerializer


class MemberViewSet(viewsets.ModelViewSet):
    """
    Member CRUD with search, filters, ordering and pagination.

    GET /api/members/?search=ana&membership_status=EXPIRING&trainer=2&page=1
    Trainers only see (read-only) the members assigned to them.
    """

    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    read_roles = ALL_ROLES
    write_roles = ADMIN_STAFF
    filterset_class = MemberFilter
    search_fields = ["full_name", "email", "phone", "member_code"]
    ordering_fields = ["full_name", "joined_date", "created_at", "member_code"]
    ordering = ["-created_at", "-id"]

    def get_queryset(self):
        # Make sure memberships that ran out yesterday show as EXPIRED today.
        Membership.objects.sync_expired()

        queryset = Member.objects.select_related("trainer").prefetch_related(
            Prefetch(
                "memberships",
                queryset=Membership.objects.select_related("plan").order_by("-end_date", "-id"),
                to_attr="prefetched_memberships",
            )
        )
        if self.request.user.role == Role.TRAINER:
            queryset = queryset.filter(trainer__user=self.request.user)
        return queryset

    def perform_destroy(self, instance):
        user = instance.user
        with transaction.atomic():
            instance.delete()
            if user is not None:
                user.delete()
