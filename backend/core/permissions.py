"""
Role based access control (RBAC).

Roles
-----
ADMIN    - can do everything.
STAFF    - front desk: members, memberships, payments, attendance.
TRAINER  - read-only access to their own assigned members, can check them in.
MEMBER   - self-service portal only (not staff screens).

A viewset only has to declare which roles may read and which may write:

    class MyViewSet(ModelViewSet):
        permission_classes = [IsAuthenticated, RolePermission]
        read_roles = ALL_ROLES            # GET / HEAD / OPTIONS
        write_roles = ADMIN_STAFF         # POST / PUT / PATCH / DELETE
        action_roles = {"destroy": ADMIN_ONLY}   # optional per-action override
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import Role

ALL_ROLES = (Role.ADMIN, Role.STAFF, Role.TRAINER)
ADMIN_STAFF = (Role.ADMIN, Role.STAFF)
ADMIN_ONLY = (Role.ADMIN,)
MEMBER_ONLY = (Role.MEMBER,)
STAFF_ROLES = (Role.ADMIN, Role.STAFF, Role.TRAINER)
STAFF_AND_MEMBER = (Role.ADMIN, Role.STAFF, Role.TRAINER, Role.MEMBER)


class RolePermission(BasePermission):
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False

        action = getattr(view, "action", None)
        action_roles = getattr(view, "action_roles", {})

        if action in action_roles:
            allowed = action_roles[action]
        elif request.method in SAFE_METHODS:
            allowed = getattr(view, "read_roles", ALL_ROLES)
        else:
            allowed = getattr(view, "write_roles", ADMIN_ONLY)

        return user.role in allowed


class MemberPortalPermission(BasePermission):
    """Only logged-in members with an active linked member profile."""

    message = "Member portal access only."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False
        if user.role != Role.MEMBER:
            return False
        return hasattr(user, "member_profile") and user.member_profile.is_active
