from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from accounts.models import Role
from members.models import Member


def member_for_user(user, *, member_id=None) -> Member:
    if user.role == Role.MEMBER:
        try:
            return Member.objects.get(user=user)
        except Member.DoesNotExist:
            raise NotFound("No member profile is linked to this login.")

    if member_id is None:
        raise ValidationError({"member": "Select a member."})

    member = Member.objects.select_related("trainer").filter(pk=member_id).first()
    if member is None:
        raise ValidationError({"member": "Member not found."})

    if user.role == Role.TRAINER:
        if member.trainer is None or member.trainer.user_id != user.id:
            raise PermissionDenied("You can only log meals for members assigned to you.")
    elif user.role not in (Role.ADMIN, Role.STAFF):
        raise PermissionDenied("You do not have permission to log meals for this member.")

    return member
