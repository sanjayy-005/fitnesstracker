from django.db import transaction
from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Role
from core.permissions import ADMIN_ONLY, ADMIN_STAFF, ALL_ROLES, RolePermission
from members.models import Member
from members.serializers import MemberMiniSerializer

from .models import Trainer
from .serializers import MemberIdsSerializer, TrainerSerializer


class TrainerViewSet(viewsets.ModelViewSet):
    """
    Trainer CRUD + member assignment.

    GET    /api/trainers/                 list (search, filter, paginate)
    POST   /api/trainers/                 create (admin)
    GET    /api/trainers/{id}/members/    members assigned to a trainer
    POST   /api/trainers/{id}/assign/     {"member_ids": [..]}   (admin, staff)
    POST   /api/trainers/{id}/unassign/   {"member_ids": [..]}   (admin, staff)
    """

    serializer_class = TrainerSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    read_roles = ALL_ROLES
    write_roles = ADMIN_ONLY
    action_roles = {
        "members": ALL_ROLES,
        "assign": ADMIN_STAFF,
        "unassign": ADMIN_STAFF,
    }
    filterset_fields = ["is_active"]
    search_fields = ["full_name", "email", "phone", "specialization"]
    ordering_fields = ["full_name", "joined_date", "experience_years", "member_count"]
    ordering = ["full_name"]

    def get_queryset(self):
        return Trainer.objects.select_related("user").annotate(
            member_count=Count("members", filter=Q(members__is_active=True), distinct=True)
        )

    def perform_destroy(self, instance):
        user = instance.user
        with transaction.atomic():
            instance.delete()
            if user is not None:
                user.delete()

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        trainer = self.get_object()
        queryset = Member.objects.filter(trainer=trainer).order_by("full_name")
        if request.user.role == Role.TRAINER and trainer.user_id != request.user.id:
            queryset = queryset.none()
        return Response(MemberMiniSerializer(queryset, many=True).data)

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        trainer = self.get_object()
        serializer = MemberIdsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not trainer.is_active:
            raise ValidationError({"detail": "You cannot assign members to an inactive trainer."})
        updated = Member.objects.filter(pk__in=serializer.validated_data["member_ids"]).update(trainer=trainer)
        return Response({"assigned": updated, "detail": f"{updated} member(s) assigned to {trainer.full_name}."})

    @action(detail=True, methods=["post"])
    def unassign(self, request, pk=None):
        trainer = self.get_object()
        serializer = MemberIdsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = Member.objects.filter(
            pk__in=serializer.validated_data["member_ids"], trainer=trainer
        ).update(trainer=None)
        return Response({"unassigned": updated, "detail": f"{updated} member(s) unassigned."})
