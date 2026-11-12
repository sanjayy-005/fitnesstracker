from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from core.permissions import ADMIN_ONLY, RolePermission

from .serializers import FitTrackTokenSerializer, UserAdminSerializer, UserSerializer

User = get_user_model()


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/  {username, password} -> {access, refresh, user}"""

    serializer_class = FitTrackTokenSerializer


class LogoutView(APIView):
    """POST /api/auth/logout/  {refresh} -> blacklists the refresh token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                # Token already expired or blacklisted - the user is logged out anyway.
                pass
        return Response({"detail": "Logged out successfully."})


class MeView(APIView):
    """GET /api/auth/me/ -> the currently logged in user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserViewSet(viewsets.ModelViewSet):
    """Admin-only management of login accounts."""

    queryset = User.objects.all().order_by("username")
    serializer_class = UserAdminSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    read_roles = ADMIN_ONLY
    write_roles = ADMIN_ONLY
    filterset_fields = ["role", "is_active"]
    search_fields = ["username", "first_name", "last_name", "email"]
    ordering_fields = ["username", "date_joined", "last_login"]

    def perform_destroy(self, instance):
        if instance.pk == self.request.user.pk:
            raise ValidationError({"detail": "You cannot delete your own account."})
        instance.delete()
