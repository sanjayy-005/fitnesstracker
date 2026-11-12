from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import FoodScanViewSet, MealEntryViewSet, NutritionConsentView, NutritionStatusView, NutritionSummaryView

router = SimpleRouter()
router.register("nutrition/scans", FoodScanViewSet, basename="food-scan")
router.register("nutrition/entries", MealEntryViewSet, basename="meal-entry")

urlpatterns = [
    path("nutrition/summary/", NutritionSummaryView.as_view(), name="nutrition-summary"),
    path("nutrition/status/", NutritionStatusView.as_view(), name="nutrition-status"),
    path("nutrition/consent/", NutritionConsentView.as_view(), name="nutrition-consent"),
    *router.urls,
]
