from abc import ABC, abstractmethod
from dataclasses import dataclass

from .schema import FoodAnalysis


@dataclass
class ProviderResult:
    analysis: FoodAnalysis
    raw: dict
    model: str
    latency_ms: int
    prompt_version: str


class FoodVisionProvider(ABC):
    name: str

    @abstractmethod
    def analyze(self, image: bytes, mime_type: str, *, note: str = "", meal_type: str = "") -> ProviderResult:
        raise NotImplementedError

    def health(self) -> bool:
        return True
