from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Role

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Read-only view of a user (returned on login and by /auth/me/)."""

    full_name = serializers.CharField(read_only=True)
    member_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "role",
            "member_id",
            "is_active",
            "last_login",
            "date_joined",
        ]
        read_only_fields = ["last_login", "date_joined"]

    def get_member_id(self, obj):
        if obj.role == Role.MEMBER:
            profile = getattr(obj, "member_profile", None)
            return profile.id if profile is not None else None
        return None


class UserAdminSerializer(UserSerializer):
    """Used by the admin-only Users screen (create / edit / reset password)."""

    password = serializers.CharField(write_only=True, required=False, style={"input_type": "password"})

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["password"]

    def validate_password(self, value):
        try:
            password_validation.validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate(self, attrs):
        creating = self.instance is None
        role = attrs.get("role", self.instance.role if self.instance else Role.STAFF)

        if creating:
            if not attrs.get("password"):
                raise serializers.ValidationError({"password": "Password is required."})
            if role == Role.TRAINER:
                raise serializers.ValidationError(
                    {"role": "Trainer logins are created from the Trainers page."}
                )
            if role == Role.MEMBER:
                raise serializers.ValidationError(
                    {"role": "Member logins are created from the Members page."}
                )
        elif role != self.instance.role and role in (Role.TRAINER, Role.MEMBER):
            page = "Trainers" if role == Role.TRAINER else "Members"
            raise serializers.ValidationError(
                {"role": f"{role.title()} accounts are managed from the {page} page."}
            )

        request = self.context.get("request")
        if self.instance is not None and request is not None and self.instance.pk == request.user.pk:
            if attrs.get("is_active") is False:
                raise serializers.ValidationError({"is_active": "You cannot deactivate your own account."})
            if "role" in attrs and attrs["role"] != self.instance.role:
                raise serializers.ValidationError({"role": "You cannot change your own role."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user


class FitTrackTokenSerializer(TokenObtainPairSerializer):
    """Login serializer: returns access + refresh tokens and the user profile."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
