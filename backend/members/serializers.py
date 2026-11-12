from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.models import Role
from plans.models import Membership

from .models import Member

User = get_user_model()


def get_current_membership(member):
    """
    The membership that best describes the member right now:
    the valid one that ends last, otherwise the most recent non-cancelled one.
    Uses the prefetched list when the view provided it (avoids extra queries).
    """
    memberships = getattr(member, "prefetched_memberships", None)
    if memberships is None:
        memberships = list(member.memberships.select_related("plan").order_by("-end_date", "-id"))

    live = [m for m in memberships if m.status != Membership.Status.CANCELLED]
    if not live:
        return None
    for membership in live:
        if membership.effective_status == Membership.Status.ACTIVE:
            return membership
    return live[0]


class MemberSerializer(serializers.ModelSerializer):
    trainer_name = serializers.SerializerMethodField()
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)
    membership_status = serializers.SerializerMethodField()
    membership_plan = serializers.SerializerMethodField()
    membership_end_date = serializers.SerializerMethodField()
    days_left = serializers.SerializerMethodField()
    login_username = serializers.SerializerMethodField()
    username = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=150)
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, style={"input_type": "password"}
    )

    class Meta:
        model = Member
        fields = [
            "id",
            "member_code",
            "full_name",
            "email",
            "phone",
            "gender",
            "gender_display",
            "date_of_birth",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "height_cm",
            "weight_kg",
            "trainer",
            "trainer_name",
            "joined_date",
            "is_active",
            "notes",
            "membership_status",
            "membership_plan",
            "membership_end_date",
            "days_left",
            "login_username",
            "username",
            "password",
            "created_at",
        ]
        read_only_fields = ["member_code", "created_at"]

    def get_trainer_name(self, obj):
        return obj.trainer.full_name if obj.trainer_id else None

    def get_login_username(self, obj):
        return obj.user.username if obj.user_id else None

    def get_membership_status(self, obj):
        membership = get_current_membership(obj)
        return membership.effective_status if membership else "NONE"

    def get_membership_plan(self, obj):
        membership = get_current_membership(obj)
        return membership.plan.name if membership else None

    def get_membership_end_date(self, obj):
        membership = get_current_membership(obj)
        return membership.end_date if membership else None

    def get_days_left(self, obj):
        membership = get_current_membership(obj)
        return membership.days_left if membership else None

    def validate_date_of_birth(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def validate_trainer(self, value):
        current = self.instance.trainer_id if self.instance is not None else None
        if value is not None and not value.is_active and value.pk != current:
            raise serializers.ValidationError("This trainer is inactive.")
        return value

    def validate(self, attrs):
        username = (attrs.get("username") or "").strip()
        password = attrs.get("password") or ""
        existing_user = self.instance.user if self.instance is not None and self.instance.user_id else None

        errors = {}
        if existing_user is None and (username or password):
            if not username:
                errors["username"] = "Username is required to create a login."
            if not password:
                errors["password"] = "Password is required to create a login."
            if username and User.objects.filter(username__iexact=username).exists():
                errors["username"] = "This username is already taken."

        if password:
            try:
                password_validation.validate_password(password)
            except DjangoValidationError as exc:
                errors["password"] = list(exc.messages)

        if errors:
            raise serializers.ValidationError(errors)

        attrs["username"] = username
        attrs["password"] = password
        return attrs

    def _create_login(self, member, username, password):
        first_name, _, last_name = member.full_name.partition(" ")
        user = User.objects.create_user(
            username=username,
            password=password,
            email=member.email,
            first_name=first_name,
            last_name=last_name,
            phone=member.phone,
            role=Role.MEMBER,
            is_active=member.is_active,
        )
        member.user = user
        member.save(update_fields=["user"])

    @transaction.atomic
    def create(self, validated_data):
        username = validated_data.pop("username", "")
        password = validated_data.pop("password", "")
        member = super().create(validated_data)
        if username and password:
            self._create_login(member, username, password)
        return member

    @transaction.atomic
    def update(self, instance, validated_data):
        username = validated_data.pop("username", "")
        password = validated_data.pop("password", "")
        member = super().update(instance, validated_data)

        if member.user_id:
            user = member.user
            first_name, _, last_name = member.full_name.partition(" ")
            user.first_name = first_name
            user.last_name = last_name
            user.email = member.email
            user.phone = member.phone
            user.is_active = member.is_active
            if password:
                user.set_password(password)
            user.save()
        elif username and password:
            self._create_login(member, username, password)
        return member


class MemberMiniSerializer(serializers.ModelSerializer):
    """Small version used in pickers and trainer assignment lists."""

    class Meta:
        model = Member
        fields = ["id", "member_code", "full_name", "phone", "is_active", "trainer"]
