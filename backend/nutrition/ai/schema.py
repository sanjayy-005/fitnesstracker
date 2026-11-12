"""JSON schema for vision LLM food analysis (Pydantic v2)."""
import re
from typing import Literal

from pydantic import BaseModel, Field

PROMPT_VERSION = "2"

CONFIDENCE = Literal["high", "medium", "low"]
UNIT = Literal[
    "g",
    "ml",
    "piece",
    "roti",
    "katori",
    "cup",
    "bowl",
    "plate",
    "tbsp",
    "tsp",
    "slice",
    "glass",
    "serving",
]


class FoodItemEstimate(BaseModel):
    name: str = Field(max_length=200)
    local_name: str = Field(default="", max_length=200)
    quantity: float = Field(default=1, gt=0, le=50)
    unit: UNIT = "serving"
    estimated_grams: float = Field(default=100, gt=0, le=5000)
    calories_kcal: float = Field(default=0, ge=0, le=5000)
    protein_g: float = Field(default=0, ge=0, le=500)
    carbs_g: float = Field(default=0, ge=0, le=500)
    fat_g: float = Field(default=0, ge=0, le=500)
    fiber_g: float = Field(default=0, ge=0, le=200)
    confidence: CONFIDENCE = "medium"
    assumptions: str = Field(default="", max_length=500)


class FoodAnalysis(BaseModel):
    is_food: bool = True
    items: list[FoodItemEstimate] = Field(default_factory=list, max_length=12)
    warnings: list[str] = Field(default_factory=list, max_length=10)


def analysis_json_schema() -> dict:
    return FoodAnalysis.model_json_schema()


UNIT_VALUES = set(UNIT.__args__)  # type: ignore[attr-defined]


def _coerce_quantity(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"[\d.]+", value.replace(",", ""))
        if match:
            return float(match.group())
    return 1.0


def _coerce_unit(value) -> str:
    text = (value or "serving").strip().lower()
    if text in UNIT_VALUES:
        return text
    if "slice" in text:
        return "slice"
    if "cup" in text or "katori" in text:
        return "katori" if "katori" in text else "cup"
    if "plate" in text or "bowl" in text:
        return "plate" if "plate" in text else "bowl"
    if "piece" in text or "tuber" in text or "whole" in text:
        return "piece"
    if text in {"g", "gram", "grams"}:
        return "g"
    return "serving"


def normalize_analysis_payload(data: dict) -> dict:
    """Map common LLM quirks (Groq, etc.) into our strict schema."""
    if not isinstance(data, dict):
        return {"is_food": False, "items": [], "warnings": ["Invalid model response."]}
    items = data.get("items") or []
    if not isinstance(items, list):
        items = []
    normalized = []
    for row in items[:12]:
        if not isinstance(row, dict):
            continue
        row = dict(row)
        row["quantity"] = _coerce_quantity(row.get("quantity", 1))
        row["unit"] = _coerce_unit(row.get("unit"))
        conf = str(row.get("confidence", "medium")).lower()
        if conf not in ("high", "medium", "low"):
            row["confidence"] = "medium"
        normalized.append(row)
    return {
        "is_food": bool(data.get("is_food", True)),
        "items": normalized,
        "warnings": list(data.get("warnings") or [])[:10],
    }
