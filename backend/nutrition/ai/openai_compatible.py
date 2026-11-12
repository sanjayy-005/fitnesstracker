import base64
import json
import time

import httpx
from django.conf import settings

from .base import FoodVisionProvider, ProviderResult
from .prompts import SYSTEM_PROMPT, prompt_version, user_prompt
from .schema import FoodAnalysis, analysis_json_schema, normalize_analysis_payload


class OpenAICompatibleProvider(FoodVisionProvider):
    name = "openai_compatible"

    def __init__(self):
        self.base_url = settings.FOOD_AI_BASE_URL
        self.model = settings.FOOD_AI_MODEL
        self.api_key = settings.FOOD_AI_API_KEY
        self.timeout = settings.FOOD_AI_TIMEOUT_SECONDS
        self.structured = settings.FOOD_AI_STRUCTURED_OUTPUT

    def health(self) -> bool:
        return bool(self.api_key) or settings.FOOD_AI_PROVIDER == "mock"

    def analyze(self, image: bytes, mime_type: str, *, note: str = "", meal_type: str = "") -> ProviderResult:
        if not self.api_key:
            raise RuntimeError("FOOD_AI_API_KEY is not set.")

        b64 = base64.b64encode(image).decode("ascii")
        data_url = f"data:{mime_type};base64,{b64}"
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": user_prompt(meal_type=meal_type, note=note)},
                ],
            },
        ]
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 1200,
        }
        if self.structured == "json_schema":
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "food_analysis",
                    "strict": True,
                    "schema": analysis_json_schema(),
                },
            }
        elif self.structured == "json_object":
            body["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        start = time.perf_counter()
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/chat/completions", json=body, headers=headers)
            response.raise_for_status()
            payload = response.json()
        latency_ms = int((time.perf_counter() - start) * 1000)

        content = payload["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        parsed = json.loads(content)
        analysis = FoodAnalysis.model_validate(normalize_analysis_payload(parsed))
        return ProviderResult(
            analysis=analysis,
            raw=payload,
            model=self.model,
            latency_ms=latency_ms,
            prompt_version=prompt_version(),
        )
