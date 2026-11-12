from rest_framework.routers import SimpleRouter

from .views import MemberViewSet

router = SimpleRouter()
router.register("members", MemberViewSet, basename="member")

urlpatterns = router.urls
