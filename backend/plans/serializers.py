from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from members.models import Member
from payments.models import Payment

from .models import Membership, MembershipPlan
from .services import create_membership


class MembershipPlanSerializer(serializers.ModelSerializer):
    duration_days = serializers.IntegerField(read_only=True)
    plan_type_display = serializers.CharField(source="get_plan_type_display", read_only=True)
    features_list = serializers.SerializerMethodField()
    active_members = serializers.SerializerMethodField()

    class Meta:
        model = MembershipPlan
        fields = [
            "id",
            "name",
            "plan_type",
            "plan_type_display",
            "duration_days",
            "price",
            "description",
            "features",
            "features_list",
            "is_active",
            "active_members",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_features_list(self, obj):
        return [line.strip() for line in obj.features.splitlines() if line.strip()]

    def get_active_members(self, obj):
        annotated = getattr(obj, "active_members", None)
        if annotated is not None:
            return annotated
        return obj.memberships.filter(
            status=Membership.Status.ACTIVE, end_date__gte=timezone.localdate()
        ).count()


class MembershipSerializer(serializers.ModelSerializer):
    """Read serializer for membership lists and details."""

    member_name = serializers.CharField(source="member.full_name", read_only=True)
    member_code = serializers.CharField(source="member.member_code", read_only=True)
    member_phone = serializers.CharField(source="member.phone", read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    plan_type = serializers.CharField(source="plan.plan_type", read_only=True)
    status = serializers.CharField(source="effective_status", read_only=True)
    days_left = serializers.IntegerField(read_only=True)

    class Meta:
        model = Membership
        fields = [
            "id",
            "member",
            "member_name",
            "member_code",
            "member_phone",
            "plan",
            "plan_name",
            "plan_type",
            "start_date",
            "end_date",
            "price",
            "status",
            "days_left",
            "created_at",
        ]
        read_only_fields = fields


class PurchaseOptionsSerializer(serializers.Serializer):
    """Payment options shared by 'new membership' and 'renew'."""

    record_payment = serializers.BooleanField(default=True)
    payment_method = serializers.ChoiceField(choices=Payment.Method.choices, required=False)
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, min_value=Decimal("0.01")
    )

    def validate(self, attrs):
        if attrs.get("record_payment", True) and not attrs.get("payment_method"):
            raise serializers.ValidationError({"payment_method": "Select how the member paid."})
        return attrs


class MembershipCreateSerializer(PurchaseOptionsSerializer):
    """POST /api/memberships/"""

    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    plan = serializers.PrimaryKeyRelatedField(queryset=MembershipPlan.objects.filter(is_active=True))
    start_date = serializers.DateField(required=False)

    def validate_member(self, value):
        if not value.is_active:
            raise serializers.ValidationError("This member is inactive.")
        return value

    def validate_start_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError(
                "Start date cannot be in the future. Leave it empty to start automatically."
            )
        return value

    def create(self, validated_data):
        return create_membership(
            member=validated_data["member"],
            plan=validated_data["plan"],
            start_date=validated_data.get("start_date"),
            record_payment=validated_data["record_payment"],
            payment_method=validated_data.get("payment_method"),
            amount=validated_data.get("amount"),
            user=self.context["request"].user,
        )


class MembershipRenewSerializer(PurchaseOptionsSerializer):
    """POST /api/memberships/{id}/renew/  (plan is optional - defaults to the same plan)"""

    plan = serializers.PrimaryKeyRelatedField(
        queryset=MembershipPlan.objects.filter(is_active=True), required=False
    )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        membership = self.context["membership"]
        if not membership.member.is_active:
            raise serializers.ValidationError({"detail": "This member is inactive."})
        plan = attrs.get("plan") or membership.plan
        if not plan.is_active:
            raise serializers.ValidationError({"plan": "This plan is no longer offered. Choose another plan."})
        attrs["plan"] = plan
        return attrs

    def create(self, validated_data):
        membership = self.context["membership"]
        return create_membership(
            member=membership.member,
            plan=validated_data["plan"],
            record_payment=validated_data["record_payment"],
            payment_method=validated_data.get("payment_method"),
            amount=validated_data.get("amount"),
            user=self.context["request"].user,
        )
