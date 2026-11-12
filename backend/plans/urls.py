from rest_framework.routers import SimpleRouter

from .views import MembershipPlanViewSet, MembershipViewSet

router = SimpleRouter()
router.register("plans", MembershipPlanViewSet, basename="plan")
router.register("memberships", MembershipViewSet, basename="membership")

urlpatterns = router.urls
