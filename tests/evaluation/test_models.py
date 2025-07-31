"""
Tests for the evaluation models.
"""

import pytest
from pydantic import ValidationError
from diffmage.evaluation.models import EvaluationResult


class TestEvaluationResult:
    """Test cases for EvaluationResult model."""

    def test_evaluation_result_creation(self):
        """Test successful creation of EvaluationResult."""
        result = EvaluationResult(
            what_score=4.0,
            why_score=3.5,
            reasoning="Test reasoning for evaluation",
            confidence=0.8,
            model_used="openai/gpt-4o-mini",
        )

        assert result.what_score == 4.0
        assert result.why_score == 3.5
        assert result.reasoning == "Test reasoning for evaluation"
        assert result.confidence == 0.8
        assert result.model_used == "openai/gpt-4o-mini"

    def test_evaluation_result_overall_score(self):
        """Test overall score calculation."""
        result = EvaluationResult(
            what_score=4.0,
            why_score=3.0,
            reasoning="Test reasoning",
            confidence=0.7,
            model_used="openai/gpt-4o-mini",
        )

        assert result.overall_score == 3.5

    def test_evaluation_result_to_dict(self):
        """Test conversion to dictionary."""
        result = EvaluationResult(
            what_score=4.0,
            why_score=3.5,
            reasoning="Test reasoning",
            confidence=0.8,
            model_used="openai/gpt-4o-mini",
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["scores"]["what"] == 4.0
        assert result_dict["scores"]["why"] == 3.5
        assert result_dict["scores"]["overall"] == 3.75
        assert result_dict["reasoning"] == "Test reasoning"
        assert result_dict["confidence"] == 0.8
        assert result_dict["model"] == "openai/gpt-4o-mini"
        assert result_dict["dimension"] == "unified"

    def test_evaluation_result_is_high_quality(self):
        """Test high quality check."""
        # Test high quality score (> 3.5)
        high_quality_result = EvaluationResult(
            what_score=4.0,
            why_score=4.0,
            reasoning="Test reasoning",
            confidence=0.9,
            model_used="openai/gpt-4o-mini",
        )
        assert high_quality_result.is_high_quality is True

        # Test low quality score (<= 3.5)
        low_quality_result = EvaluationResult(
            what_score=3.0,
            why_score=3.0,
            reasoning="Test reasoning",
            confidence=0.5,
            model_used="openai/gpt-4o-mini",
        )
        assert low_quality_result.is_high_quality is False

    def test_evaluation_result_quality_level(self):
        """Test quality level assessment."""
        # Excellent: > 4.5
        excellent_result = EvaluationResult(
            what_score=5.0,
            why_score=5.0,
            reasoning="Test reasoning",
            confidence=0.95,
            model_used="openai/gpt-4o-mini",
        )
        assert excellent_result.quality_level == "Excellent"

        # Good: >= 3.5
        good_result = EvaluationResult(
            what_score=4.0,
            why_score=4.0,
            reasoning="Test reasoning",
            confidence=0.8,
            model_used="openai/gpt-4o-mini",
        )
        assert good_result.quality_level == "Good"

        # Average: >= 2.5
        average_result = EvaluationResult(
            what_score=3.0,
            why_score=3.0,
            reasoning="Test reasoning",
            confidence=0.6,
            model_used="openai/gpt-4o-mini",
        )
        assert average_result.quality_level == "Average"

        # Poor: >= 1.5
        poor_result = EvaluationResult(
            what_score=2.0,
            why_score=2.0,
            reasoning="Test reasoning",
            confidence=0.3,
            model_used="openai/gpt-4o-mini",
        )
        assert poor_result.quality_level == "Poor"

        # Very Poor: < 1.5
        very_poor_result = EvaluationResult(
            what_score=1.0,
            why_score=1.0,
            reasoning="Test reasoning",
            confidence=0.1,
            model_used="openai/gpt-4o-mini",
        )
        assert very_poor_result.quality_level == "Very Poor"

    def test_evaluation_result_validation_what_score_too_low(self):
        """Test validation for what_score below minimum."""
        with pytest.raises(ValidationError):
            EvaluationResult(
                what_score=0.5,  # Below minimum of 1.0
                why_score=3.5,
                reasoning="Test reasoning",
                confidence=0.8,
                model_used="openai/gpt-4o-mini",
            )

    def test_evaluation_result_validation_what_score_too_high(self):
        """Test validation for what_score above maximum."""
        with pytest.raises(ValidationError):
            EvaluationResult(
                what_score=5.5,  # Above maximum of 5.0
                why_score=3.5,
                reasoning="Test reasoning",
                confidence=0.8,
                model_used="openai/gpt-4o-mini",
            )

    def test_evaluation_result_validation_why_score_too_low(self):
        """Test validation for why_score below minimum."""
        with pytest.raises(ValidationError):
            EvaluationResult(
                what_score=4.0,
                why_score=0.5,  # Below minimum of 1.0
                reasoning="Test reasoning",
                confidence=0.8,
                model_used="openai/gpt-4o-mini",
            )

    def test_evaluation_result_validation_why_score_too_high(self):
        """Test validation for why_score above maximum."""
        with pytest.raises(ValidationError):
            EvaluationResult(
                what_score=4.0,
                why_score=5.5,  # Above maximum of 5.0
                reasoning="Test reasoning",
                confidence=0.8,
                model_used="openai/gpt-4o-mini",
            )

    def test_evaluation_result_validation_confidence_too_low(self):
        """Test validation for confidence below minimum."""
        with pytest.raises(ValidationError):
            EvaluationResult(
                what_score=4.0,
                why_score=3.5,
                reasoning="Test reasoning",
                confidence=-0.1,  # Below minimum of 0.0
                model_used="openai/gpt-4o-mini",
            )

    def test_evaluation_result_validation_confidence_too_high(self):
        """Test validation for confidence above maximum."""
        with pytest.raises(ValidationError):
            EvaluationResult(
                what_score=4.0,
                why_score=3.5,
                reasoning="Test reasoning",
                confidence=1.1,  # Above maximum of 1.0
                model_used="openai/gpt-4o-mini",
            )

    def test_evaluation_result_validation_reasoning_too_short(self):
        """Test validation for reasoning that's too short."""
        with pytest.raises(ValidationError):
            EvaluationResult(
                what_score=4.0,
                why_score=3.5,
                reasoning="Short",  # Less than minimum of 10 characters
                confidence=0.8,
                model_used="openai/gpt-4o-mini",
            )

    def test_evaluation_result_validation_empty_model_used(self):
        """Test validation for empty model_used."""
        with pytest.raises(ValidationError):
            EvaluationResult(
                what_score=4.0,
                why_score=3.5,
                reasoning="Test reasoning",
                confidence=0.8,
                model_used="",  # Empty string should not be allowed
            )
