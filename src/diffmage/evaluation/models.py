"""
Data models for commit message evaluation system
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class ScoreThresholds:
    """Score thresholds for quality ratings"""

    EXCELLENT = 4.5
    GOOD = 3.5
    AVERAGE = 2.5
    POOR = 1.5


class QualityRater:
    """Quality Rating"""

    @staticmethod
    def get_quality_level(score: float) -> str:
        """Human readable quality assessment"""
        if score > ScoreThresholds.EXCELLENT:
            return "Excellent"
        elif score >= ScoreThresholds.GOOD:
            return "Good"
        elif score >= ScoreThresholds.AVERAGE:
            return "Average"
        elif score >= ScoreThresholds.POOR:
            return "Poor"
        else:
            return "Very Poor"

    @staticmethod
    def is_high_quality(score: float) -> bool:
        """Check if score represents high quality"""
        return score > ScoreThresholds.GOOD


class EvaluationResult(BaseModel):
    """Result of LLM based commit message evaluation with validation"""

    what_score: float = Field(
        ge=1.0, le=5.0, description="Accuracy of change description"
    )
    why_score: float = Field(ge=1.0, le=5.0, description="Clarity of rationale")
    reasoning: str = Field(min_length=10, description="Chain-of-thought explanation")
    confidence: float = Field(
        ge=0.0, le=1.0, description="LLM confidence in evaluation"
    )
    model_used: str = Field(description="Model used for evaluation")

    @property
    def overall_score(self) -> float:
        return round((self.what_score + self.why_score) / 2, 2)

    @property
    def quality_level(self) -> str:
        """Human readable quality assessment"""
        return QualityRater.get_quality_level(self.overall_score)

    @property
    def is_high_quality(self) -> bool:
        """Check if score represents high quality"""
        return QualityRater.is_high_quality(self.overall_score)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "scores": {
                "what": self.what_score,
                "why": self.why_score,
                "overall": self.overall_score,
            },
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "model": self.model_used,
            "quality_level": self.quality_level,
        }
