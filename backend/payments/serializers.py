from django.utils import timezone
from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)
    member_code = serializers.CharField(source="member.member_code", read_only=True)
    plan_name = serializers.SerializerMethodField()
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    received_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "receipt_no",
            "member",
            "member_name",
            "member_code",
            "membership",
            "plan_name",
            "amount",
            "method",
            "method_display",
            "status",
            "paid_on",
            "note",
            "received_by_name",
            "created_at",
        ]
        read_only_fields = ["receipt_no", "created_at"]

    def get_plan_name(self, obj):
        return obj.membership.plan.name if obj.membership_id else None

    def get_received_by_name(self, obj):
        return obj.received_by.full_name if obj.received_by_id else None

    def validate_paid_on(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Payment date cannot be in the future.")
        return value

    def validate(self, attrs):
        member = attrs.get("member") or (self.instance.member if self.instance else None)
        membership = attrs.get("membership") if "membership" in attrs else (
            self.instance.membership if self.instance else None
        )
        if membership is not None and member is not None and membership.member_id != member.pk:
            raise serializers.ValidationError({"membership": "This membership belongs to a different member."})
        return attrs
