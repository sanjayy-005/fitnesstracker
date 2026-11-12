"""Member self-service: own profile, membership and visit history."""
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Role
from attendance.models import Attendance
from attendance.serializers import AttendanceSerializer
from core.pagination import StandardPagination
from core.permissions import MemberPortalPermission
from members.models import Member
from members.serializers import get_current_membership
from plans.models import Membership
from plans.serializers import MembershipSerializer


def member_for_request(request):
    if request.user.role != Role.MEMBER:
        raise PermissionDenied("This area is for member accounts only.")
    try:
        return Member.objects.select_related("trainer").get(user=request.user, is_active=True)
    except Member.DoesNotExist:
        raise NotFound("No member profile is linked to this login. Ask the front desk to set one up.")


class MemberProfileView(APIView):
    permission_classes = [IsAuthenticated, MemberPortalPermission]

    def get(self, request):
        member = member_for_request(request)
        membership = get_current_membership(member)
        return Response(
            {
                "id": member.id,
                "member_code": member.member_code,
                "full_name": member.full_name,
                "email": member.email,
                "phone": member.phone,
                "height_cm": member.height_cm,
                "weight_kg": member.weight_kg,
                "joined_date": member.joined_date,
                "trainer_name": member.trainer.full_name if member.trainer_id else None,
                "nutrition_consent_at": member.nutrition_consent_at,
                "membership": MembershipSerializer(membership).data if membership else None,
            }
        )


class MemberMembershipsView(APIView):
    permission_classes = [IsAuthenticated, MemberPortalPermission]

    def get(self, request):
        member = member_for_request(request)
        Membership.objects.sync_expired()
        qs = Membership.objects.filter(member=member).select_related("plan").order_by("-end_date", "-id")
        return Response(MembershipSerializer(qs, many=True).data)


class MemberAttendanceView(ListAPIView):
    permission_classes = [IsAuthenticated, MemberPortalPermission]
    serializer_class = AttendanceSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        member = member_for_request(self.request)
        return Attendance.objects.filter(member=member).select_related("member").order_by("-date", "-check_in", "-id")
