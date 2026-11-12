from django.conf import settings

from .mock_provider import MockFoodVisionProvider
from .openai_compatible import OpenAICompatibleProvider


def get_food_vision_provider():
    name = settings.FOOD_AI_PROVIDER
    if name == "mock":
        return MockFoodVisionProvider()
    if name == "openai_compatible":
        return OpenAICompatibleProvider()
    raise ValueError(f"Unknown FOOD_AI_PROVIDER: {name}")
