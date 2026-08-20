from abc import ABC, abstractmethod
from pydantic import BaseModel


class AIAnalysisResult(BaseModel):
    priority: str  # "urgent", "important", "normal", "low"
    confidence: float  # 0.0 to 1.0
    explanation: str | None = None  # 1-2 sentences explaining priority
    summary: str | None = None
    recommended_actions: list[str] = []
    tasks_extracted: list[dict] = []
    deadlines: list[str] = []


class BaseLLMProvider(ABC):
    @abstractmethod
    async def analyze(self, message: str) -> AIAnalysisResult:
        pass
