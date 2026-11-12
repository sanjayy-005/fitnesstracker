from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .ai.registry import get_food_vision_provider
from .ai.schema import FoodAnalysis, FoodItemEstimate
from .models import FoodScan, MealEntry, MealItem


def macro_kcal(item: FoodItemEstimate) -> Decimal:
    return Decimal(str(4 * item.protein_g + 4 * item.carbs_g + 9 * item.fat_g))


def item_needs_review(item: FoodItemEstimate) -> bool:
    stated = Decimal(str(item.calories_kcal))
    if stated <= 0:
        return True
    computed = macro_kcal(item)
    if computed <= 0:
        return False
    diff_ratio = abs(stated - computed) / max(stated, Decimal("1"))
    return diff_ratio > Decimal("0.25")


def validate_analysis(analysis: FoodAnalysis) -> tuple[FoodAnalysis, list[str]]:
    warnings = list(analysis.warnings)
    if not analysis.is_food or not analysis.items:
        warnings.append("No food detected in this image.")
        return analysis, warnings

    for item in analysis.items:
        if item.estimated_grams > 2000 or item.calories_kcal > 2500:
            warnings.append(f"Unusually large portion for {item.name}.")
        if item_needs_review(item):
            warnings.append(f"Calorie/macro mismatch for {item.name} — please review.")

    total_kcal = sum(i.calories_kcal for i in analysis.items)
    if total_kcal > 6000:
        warnings.append("Total meal calories look very high.")

    return analysis, warnings


def scan_status_from_analysis(analysis: FoodAnalysis, warnings: list[str]) -> str:
    if not analysis.is_food or not analysis.items:
        return FoodScan.Status.FAILED
    if warnings:
        return FoodScan.Status.NEEDS_REVIEW
    if any(i.confidence == "low" for i in analysis.items):
        return FoodScan.Status.NEEDS_REVIEW
    return FoodScan.Status.SUCCEEDED


@transaction.atomic
def run_food_scan(scan: FoodScan, image_bytes: bytes, mime_type: str) -> FoodScan:
    provider = get_food_vision_provider()
    try:
        result = provider.analyze(
            image_bytes,
            mime_type,
            note=scan.note,
            meal_type=scan.meal_type,
        )
        analysis, warnings = validate_analysis(result.analysis)
        status = scan_status_from_analysis(analysis, warnings)
        analysis_dict = analysis.model_dump()
        analysis_dict["warnings"] = list(dict.fromkeys(warnings + analysis_dict.get("warnings", [])))
        scan.status = status
        scan.provider = provider.name
        scan.model_name = result.model
        scan.prompt_version = result.prompt_version
        scan.raw_response = result.raw
        scan.analysis = analysis_dict
        scan.error = "" if status != FoodScan.Status.FAILED else "No food detected."
        scan.latency_ms = result.latency_ms
    except Exception as exc:
        scan.status = FoodScan.Status.FAILED
        scan.error = str(exc)
    scan.completed_at = timezone.now()
    scan.save()
    return scan


def ensure_scanning_configured():
    if not settings.FOOD_AI_ENABLED:
        raise RuntimeError("Food scanning is disabled.")
    if settings.FOOD_AI_PROVIDER == "openai_compatible" and not settings.FOOD_AI_API_KEY:
        raise RuntimeError("Food scanning is not configured (missing FOOD_AI_API_KEY).")


def totals_from_items(items_data: list[dict]) -> dict:
    fields = ("kcal", "protein_g", "carbs_g", "fat_g", "fiber_g")
    totals = {field: Decimal("0") for field in fields}
    for row in items_data:
        for field in fields:
            totals[field] += Decimal(str(row.get(field, 0)))
    return totals


@transaction.atomic
def confirm_scan(scan: FoodScan, *, eaten_on, meal_type: str, items_data: list[dict], user, edited: bool) -> MealEntry:
    if scan.status not in (FoodScan.Status.SUCCEEDED, FoodScan.Status.NEEDS_REVIEW):
        raise ValueError("This scan cannot be confirmed.")
    if hasattr(scan, "meal_entry"):
        raise ValueError("This scan was already saved as a meal.")

    totals = totals_from_items(items_data)
    entry = MealEntry.objects.create(
        member=scan.member,
        scan=scan,
        eaten_on=eaten_on,
        meal_type=meal_type,
        source=MealEntry.Source.AI_EDITED if edited else MealEntry.Source.AI,
        total_kcal=totals["kcal"],
        protein_g=totals["protein_g"],
        carbs_g=totals["carbs_g"],
        fat_g=totals["fat_g"],
        fiber_g=totals["fiber_g"],
        created_by=user,
    )
    for row in items_data:
        MealItem.objects.create(
            entry=entry,
            name=row["name"],
            quantity=Decimal(str(row["quantity"])),
            unit=row.get("unit") or "serving",
            grams=Decimal(str(row["grams"])) if row.get("grams") not in (None, "") else None,
            kcal=Decimal(str(row["kcal"])),
            protein_g=Decimal(str(row.get("protein_g", 0))),
            carbs_g=Decimal(str(row.get("carbs_g", 0))),
            fat_g=Decimal(str(row.get("fat_g", 0))),
            fiber_g=Decimal(str(row.get("fiber_g", 0))),
            confidence=row.get("confidence") or "",
            was_edited=bool(row.get("was_edited")),
        )
    return entry
