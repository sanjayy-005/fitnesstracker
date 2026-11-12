from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Role
from core.permissions import ADMIN_STAFF, MEMBER_ONLY, RolePermission, STAFF_AND_MEMBER
from members.models import Member

from .access import member_for_user
from .image_utils import normalize_meal_image
from .models import FoodScan, MealEntry
from .serializers import (
    ConfirmScanSerializer,
    FoodScanSerializer,
    ManualMealSerializer,
    MealEntrySerializer,
)
from .services import confirm_scan, ensure_scanning_configured, run_food_scan, totals_from_items


class NutritionAccessMixin:
    def nutrition_member_queryset(self, qs):
        user = self.request.user
        if user.role == Role.MEMBER:
            return qs.filter(member__user=user)
        if user.role == Role.TRAINER:
            return qs.filter(member__trainer__user=user)
        return qs


class FoodScanViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = FoodScanSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    read_roles = STAFF_AND_MEMBER
    write_roles = STAFF_AND_MEMBER

    def get_queryset(self):
        qs = FoodScan.objects.select_related("member")
        user = self.request.user
        if user.role == Role.MEMBER:
            qs = qs.filter(member__user=user)
        elif user.role == Role.TRAINER:
            qs = qs.filter(member__trainer__user=user)
        member = self.request.query_params.get("member")
        if member and user.role in (Role.ADMIN, Role.STAFF):
            qs = qs.filter(member_id=member)
        return qs

    def create(self, request, *args, **kwargs):
        try:
            ensure_scanning_configured()
        except RuntimeError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        image = request.FILES.get("image")
        if not image:
            raise ValidationError({"image": "Choose a meal photo to upload."})

        meal_type = request.data.get("meal_type") or "OTHER"
        note = (request.data.get("note") or "")[:300]
        member_id = request.data.get("member")

        member = member_for_user(request.user, member_id=member_id)
        if not member.is_active:
            raise ValidationError({"member": "This member is inactive."})

        if member.nutrition_consent_at is None:
            raise ValidationError(
                {"detail": "Food photo analysis requires consent. Accept the disclaimer first."}
            )

        today = timezone.localdate()
        daily_limit = settings.FOOD_AI_DAILY_SCANS_PER_USER
        count_today = FoodScan.objects.filter(created_by=request.user, created_at__date=today).count()
        if count_today >= daily_limit:
            raise ValidationError({"detail": f"Daily scan limit reached ({daily_limit}). Try again tomorrow."})

        try:
            image_bytes, mime = normalize_meal_image(image, max_px=settings.FOOD_AI_MAX_IMAGE_PX)
        except ValueError as exc:
            raise ValidationError({"image": str(exc)}) from exc

        scan = FoodScan.objects.create(
            member=member,
            created_by=request.user,
            meal_type=meal_type,
            note=note,
        )
        run_food_scan(scan, image_bytes, mime)
        return Response(FoodScanSerializer(scan).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        scan = self.get_object()
        serializer = ConfirmScanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            entry = confirm_scan(
                scan,
                eaten_on=data["eaten_on"],
                meal_type=data["meal_type"],
                items_data=data["items"],
                user=request.user,
                edited=data["edited"],
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(MealEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class MealEntryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = MealEntrySerializer
    permission_classes = [IsAuthenticated, RolePermission]
    read_roles = STAFF_AND_MEMBER
    write_roles = STAFF_AND_MEMBER
    action_roles = {"destroy": ADMIN_STAFF, "create_manual": STAFF_AND_MEMBER}

    def get_queryset(self):
        qs = MealEntry.objects.select_related("member").prefetch_related("items")
        user = self.request.user
        if user.role == Role.MEMBER:
            qs = qs.filter(member__user=user)
        elif user.role == Role.TRAINER:
            qs = qs.filter(member__trainer__user=user)

        member = self.request.query_params.get("member")
        if member and user.role in (Role.ADMIN, Role.STAFF, Role.TRAINER):
            qs = qs.filter(member_id=member)
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(eaten_on__gte=date_from)
        if date_to:
            qs = qs.filter(eaten_on__lte=date_to)
        return qs

    @action(detail=False, methods=["post"], url_path="manual")
    def create_manual(self, request):
        serializer = ManualMealSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        member = member_for_user(request.user, member_id=data.get("member"))
        totals = totals_from_items(data["items"])
        entry = MealEntry.objects.create(
            member=member,
            eaten_on=data["eaten_on"],
            meal_type=data["meal_type"],
            source=MealEntry.Source.MANUAL,
            total_kcal=totals["kcal"],
            protein_g=totals["protein_g"],
            carbs_g=totals["carbs_g"],
            fat_g=totals["fat_g"],
            fiber_g=totals["fiber_g"],
            created_by=request.user,
        )
        from .models import MealItem

        for row in data["items"]:
            MealItem.objects.create(
                entry=entry,
                name=row["name"],
                quantity=row["quantity"],
                unit=row.get("unit") or "serving",
                grams=row.get("grams"),
                kcal=row["kcal"],
                protein_g=row.get("protein_g", 0),
                carbs_g=row.get("carbs_g", 0),
                fat_g=row.get("fat_g", 0),
                fiber_g=row.get("fiber_g", 0),
            )
        return Response(MealEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class NutritionSummaryView(APIView):
    permission_classes = [IsAuthenticated, RolePermission]
    read_roles = STAFF_AND_MEMBER

    def get(self, request):
        try:
            days = int(request.query_params.get("days", 7))
        except ValueError:
            days = 7
        days = min(max(days, 1), 90)

        member_id = request.query_params.get("member")
        if request.user.role == Role.MEMBER:
            member = member_for_user(request.user)
        else:
            if not member_id:
                raise ValidationError({"member": "Select a member."})
            member = member_for_user(request.user, member_id=int(member_id))

        today = timezone.localdate()
        start = today - timedelta(days=days - 1)
        rows = (
            MealEntry.objects.filter(member=member, eaten_on__gte=start, eaten_on__lte=today)
            .values("eaten_on")
            .annotate(
                kcal=Sum("total_kcal"),
                protein_g=Sum("protein_g"),
                carbs_g=Sum("carbs_g"),
                fat_g=Sum("fat_g"),
            )
            .order_by("eaten_on")
        )
        by_day = {row["eaten_on"]: row for row in rows}
        daily = []
        for offset in range(days):
            day = start + timedelta(days=offset)
            row = by_day.get(day, {})
            daily.append(
                {
                    "date": day.isoformat(),
                    "kcal": float(row.get("kcal") or 0),
                    "protein_g": float(row.get("protein_g") or 0),
                    "carbs_g": float(row.get("carbs_g") or 0),
                    "fat_g": float(row.get("fat_g") or 0),
                }
            )
        today_kcal = float(by_day.get(today, {}).get("kcal") or 0)
        return Response({"member": member.id, "days": days, "today_kcal": today_kcal, "daily": daily})


class NutritionStatusView(APIView):
    permission_classes = [IsAuthenticated, RolePermission]
    read_roles = ADMIN_STAFF

    def get(self, request):
        from .ai.registry import get_food_vision_provider

        provider = get_food_vision_provider()
        configured = settings.FOOD_AI_ENABLED and (
            settings.FOOD_AI_PROVIDER == "mock" or bool(settings.FOOD_AI_API_KEY)
        )
        pending = FoodScan.objects.filter(status=FoodScan.Status.PENDING).count()
        return Response(
            {
                "enabled": settings.FOOD_AI_ENABLED,
                "configured": configured,
                "provider": settings.FOOD_AI_PROVIDER,
                "model": settings.FOOD_AI_MODEL,
                "pending_scans": pending,
                "provider_healthy": provider.health() if configured else False,
            }
        )


class NutritionConsentView(APIView):
    permission_classes = [IsAuthenticated, RolePermission]
    write_roles = MEMBER_ONLY

    def post(self, request):
        member = member_for_user(request.user)
        if member.nutrition_consent_at is None:
            member.nutrition_consent_at = timezone.now()
            member.save(update_fields=["nutrition_consent_at"])
        return Response({"nutrition_consent_at": member.nutrition_consent_at})
