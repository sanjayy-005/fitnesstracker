from datetime import datetime

from rest_framework import serializers

from members.models import Member

from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)
    member_code = serializers.CharField(source="member.member_code", read_only=True)
    duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            "id",
            "member",
            "member_name",
            "member_code",
            "date",
            "check_in",
            "check_out",
            "duration_minutes",
        ]
        read_only_fields = fields

    def get_duration_minutes(self, obj):
        if not obj.check_out:
            return None
        start = datetime.combine(obj.date, obj.check_in)
        end = datetime.combine(obj.date, obj.check_out)
        return max(int((end - start).total_seconds() // 60), 0)


class CheckInSerializer(serializers.Serializer):
    """POST /api/attendance/check-in/  {"member": 12}"""

    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.select_related("trainer"))
