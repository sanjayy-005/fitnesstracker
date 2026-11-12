"""Root URL configuration. Every API endpoint lives under /api/."""
from django.contrib import admin
from django.urls import include, path

from core.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("members.urls")),
    path("api/", include("trainers.urls")),
    path("api/", include("plans.urls")),
    path("api/", include("payments.urls")),
    path("api/", include("attendance.urls")),
    path("api/", include("dashboard.urls")),
    path("api/portal/", include("portal.urls")),
    path("api/", include("nutrition.urls")),
]
