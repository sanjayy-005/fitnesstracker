from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from accounts.models import Role

from .models import Trainer

User = get_user_model()


class MemberIdsSerializer(serializers.Serializer):
    """Body for assign / unassign: {"member_ids": [1, 2, 3]}"""

    member_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)


class TrainerSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    login_username = serializers.SerializerMethodField()
    # Optional: give the trainer a login (role = TRAINER) when creating / editing.
    username = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=150)
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, style={"input_type": "password"}
    )

    class Meta:
        model = Trainer
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "specialization",
            "experience_years",
            "bio",
            "joined_date",
            "is_active",
            "member_count",
            "login_username",
            "username",
            "password",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    # -- read helpers -------------------------------------------------------
    def get_member_count(self, obj):
        annotated = getattr(obj, "member_count", None)
        return annotated if annotated is not None else obj.members.filter(is_active=True).count()

    def get_login_username(self, obj):
        return obj.user.username if obj.user_id else None

    # -- validation ---------------------------------------------------------
    def validate_experience_years(self, value):
        if value > 60:
            raise serializers.ValidationError("Experience cannot be more than 60 years.")
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

    # -- create / update ----------------------------------------------------
    def _create_login(self, trainer, username, password):
        first_name, _, last_name = trainer.full_name.partition(" ")
        user = User.objects.create_user(
            username=username,
            password=password,
            email=trainer.email,
            first_name=first_name,
            last_name=last_name,
            phone=trainer.phone,
            role=Role.TRAINER,
            is_active=trainer.is_active,
        )
        trainer.user = user
        trainer.save(update_fields=["user"])

    @transaction.atomic
    def create(self, validated_data):
        username = validated_data.pop("username", "")
        password = validated_data.pop("password", "")
        trainer = super().create(validated_data)
        if username and password:
            self._create_login(trainer, username, password)
        return trainer

    @transaction.atomic
    def update(self, instance, validated_data):
        username = validated_data.pop("username", "")
        password = validated_data.pop("password", "")
        trainer = super().update(instance, validated_data)

        if trainer.user_id:
            user = trainer.user
            first_name, _, last_name = trainer.full_name.partition(" ")
            user.first_name = first_name
            user.last_name = last_name
            user.email = trainer.email
            user.phone = trainer.phone
            user.is_active = trainer.is_active
            if password:
                user.set_password(password)
            user.save()
        elif username and password:
            self._create_login(trainer, username, password)
        return trainer
