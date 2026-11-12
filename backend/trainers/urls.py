from rest_framework.routers import SimpleRouter

from .views import TrainerViewSet

router = SimpleRouter()
router.register("trainers", TrainerViewSet, basename="trainer")

urlpatterns = router.urls
