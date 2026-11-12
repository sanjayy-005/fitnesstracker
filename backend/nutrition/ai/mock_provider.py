import time

from .base import FoodVisionProvider, ProviderResult
from .prompts import prompt_version
from .schema import FoodAnalysis, FoodItemEstimate


class MockFoodVisionProvider(FoodVisionProvider):
    name = "mock"

    def analyze(self, image: bytes, mime_type: str, *, note: str = "", meal_type: str = "") -> ProviderResult:
        start = time.perf_counter()
        items = [
            FoodItemEstimate(
                name="Rajma chawal",
                local_name="राजमा चावल",
                quantity=1,
                unit="plate",
                estimated_grams=350,
                calories_kcal=480,
                protein_g=16,
                carbs_g=78,
                fat_g=11,
                fiber_g=9,
                confidence="medium",
                assumptions="Home-style, moderate oil",
            ),
            FoodItemEstimate(
                name="Plain roti",
                local_name="रोटी",
                quantity=1,
                unit="roti",
                estimated_grams=40,
                calories_kcal=120,
                protein_g=3,
                carbs_g=22,
                fat_g=2,
                fiber_g=2,
                confidence="high",
                assumptions="Standard wheat roti",
            ),
        ]
        analysis = FoodAnalysis(
            is_food=True,
            items=items,
            warnings=["AI estimate — please verify portions before saving."],
        )
        latency_ms = int((time.perf_counter() - start) * 1000) + 400
        return ProviderResult(
            analysis=analysis,
            raw={"mock": True, "bytes": len(image), "mime": mime_type},
            model="mock/qwen2.5-vl-demo",
            latency_ms=latency_ms,
            prompt_version=prompt_version(),
        )
