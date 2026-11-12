from django.urls import include, path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, LogoutView, MeView, UserViewSet

router = SimpleRouter()
router.register("users", UserViewSet, basename="user")

# Mounted at /api/auth/
urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
