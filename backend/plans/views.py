from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Role
from core.permissions import ADMIN_ONLY, ADMIN_STAFF, ALL_ROLES, RolePermission

from .filters import MembershipFilter
from .models import Membership, MembershipPlan
from .serializers import (
    MembershipCreateSerializer,
    MembershipPlanSerializer,
    MembershipRenewSerializer,
    MembershipSerializer,
)


class MembershipPlanViewSet(viewsets.ModelViewSet):
    """Membership plans. Everyone can read; only admins can change them."""

    serializer_class = MembershipPlanSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    read_roles = ALL_ROLES
    write_roles = ADMIN_ONLY
    filterset_fields = ["is_active", "plan_type"]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "name", "created_at"]
    ordering = ["price", "name"]

    def get_queryset(self):
        today = timezone.localdate()
        return MembershipPlan.objects.annotate(
            active_members=Count(
                "memberships",
                filter=Q(memberships__status=Membership.Status.ACTIVE, memberships__end_date__gte=today),
                distinct=True,
            )
        )


class MembershipViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Memberships (a member buying a plan).

    POST /api/memberships/               sell a plan to a member (+ optional payment)
    POST /api/memberships/{id}/renew/    renew (same plan or a different one)
    POST /api/memberships/{id}/cancel/   cancel an active membership
    DELETE                               admin only (removes a mistaken entry)
    """

    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    read_roles = ALL_ROLES
    write_roles = ADMIN_STAFF
    action_roles = {"destroy": ADMIN_ONLY}
    filterset_class = MembershipFilter
    search_fields = ["member__full_name", "member__member_code", "member__phone", "plan__name"]
    ordering_fields = ["end_date", "start_date", "created_at", "price"]
    ordering = ["-end_date", "-id"]

    def get_queryset(self):
        Membership.objects.sync_expired()
        queryset = Membership.objects.select_related("member", "plan")
        if self.request.user.role == Role.TRAINER:
            queryset = queryset.filter(member__trainer__user=self.request.user)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = MembershipCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def renew(self, request, pk=None):
        membership = self.get_object()
        serializer = MembershipRenewSerializer(
            data=request.data,
            context={"request": request, "membership": membership},
        )
        serializer.is_valid(raise_exception=True)
        new_membership = serializer.save()
        return Response(MembershipSerializer(new_membership).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        membership = self.get_object()
        if membership.effective_status != Membership.Status.ACTIVE:
            raise ValidationError({"detail": "Only an active membership can be cancelled."})
        membership.status = Membership.Status.CANCELLED
        membership.save(update_fields=["status"])
        return Response(MembershipSerializer(membership).data)
