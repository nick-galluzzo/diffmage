"""
Data models for commit message evaluation system
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


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
        }

    @property
    def is_high_quality(self) -> bool:
        """Quick quality check - above 3.5/5 threshold"""
        return self.overall_score > 3.5

    @property
    def quality_level(self) -> str:
        """Human readable quality assessment"""
        if self.overall_score > 4.5:
            return "Excellent"
        elif self.overall_score >= 3.5:
            return "Good"
        elif self.overall_score >= 2.5:
            return "Average"
        elif self.overall_score >= 1.5:
            return "Poor"
        else:
            return "Very Poor"
