"""
Tests for the LLM-based commit message evaluator.
"""

import pytest
from unittest.mock import patch
from diffmage.evaluation.commit_message_evaluator import CommitMessageEvaluator
from diffmage.evaluation.models import EvaluationResult


class TestLLMEvaluator:
    """Test cases for LLMEvaluator class."""

    def test_init_with_custom_model(self):
        """Test LLMEvaluator initialization with custom model."""
        evaluator = CommitMessageEvaluator(model_name="anthropic/claude-sonnet-4")

        assert evaluator.model_name == "anthropic/claude-sonnet-4"
        assert evaluator.ai_client.model_config.name == "anthropic/claude-sonnet-4"

    def test_init_with_custom_temperature(self):
        """Test LLMEvaluator initialization with custom temperature."""
        evaluator = CommitMessageEvaluator(temperature=0.5)

        assert evaluator.ai_client.temperature == 0.5

    def test_evaluate_commit_message_success(self):
        """Test successful commit message evaluation."""
        evaluator = CommitMessageEvaluator(model_name="openai/gpt-4o-mini")

        # Mock the AI client response
        mock_response = """{
            "what_score": 4,
            "why_score": 5,
            "overall_score": 4.5,
            "reasoning": "The commit message accurately describes the changes and clearly explains the purpose.",
            "confidence": 0.9,
            "model_used": "openai/gpt-4o-mini",
            "dimension": "unified"
        }"""

        with patch.object(
            evaluator.ai_client, "evaluate_with_llm", return_value=mock_response
        ):
            result = evaluator.evaluate_commit_message(
                "feat: add user authentication",
                "--- a/auth.py\n+++ b/auth.py\n@@ -1 +1 @@\n+def login(): pass",
            )

            assert isinstance(result, EvaluationResult)
            assert result.what_score == 4
            assert result.why_score == 5
            assert result.overall_score == 4.5
            assert "accurately describes" in result.reasoning
            assert result.confidence == 0.9
            assert result.model_used == "openai/gpt-4o-mini"

    def test_evaluate_commit_message_empty_message(self):
        """Test evaluation with empty commit message."""
        evaluator = CommitMessageEvaluator()

        result = evaluator.evaluate_commit_message("", "some diff")
        assert result.what_score == 1.0
        assert result.why_score == 1.0
        assert result.overall_score == 1.0
        assert result.confidence == 1.0

    def test_evaluate_commit_message_empty_diff(self):
        """Test evaluation with empty git diff."""
        evaluator = CommitMessageEvaluator()

        result = evaluator.evaluate_commit_message("some message", "")
        assert result.what_score == 1.0
        assert result.why_score == 1.0
        assert result.overall_score == 1.0
        assert result.confidence == 1.0

    def test_evaluate_commit_message_llm_error(self):
        """Test evaluation when LLM call fails."""
        evaluator = CommitMessageEvaluator()

        with patch.object(
            evaluator.ai_client, "evaluate_with_llm", side_effect=Exception("API Error")
        ):
            with pytest.raises(ValueError, match="Failed to evaluate commit message"):
                evaluator.evaluate_commit_message("test message", "test diff")

    def test_evaluate_commit_message_invalid_json(self):
        """Test evaluation with invalid JSON response."""
        evaluator = CommitMessageEvaluator()

        with patch.object(
            evaluator.ai_client,
            "evaluate_with_llm",
            return_value="invalid json response",
        ):
            with pytest.raises(ValueError, match="Failed to parse evaluation response"):
                evaluator.evaluate_commit_message("test message", "test diff")

    def test_parse_evaluation_response_valid_json(self):
        """Test parsing valid JSON response."""
        evaluator = CommitMessageEvaluator()

        valid_json = """{
            "what_score": 3,
            "why_score": 4,
            "overall_score": 3.5,
            "reasoning": "Test reasoning",
            "confidence": 0.75,
            "model_used": "openai/gpt-4o-mini",
            "dimension": "unified"
        }"""

        result = evaluator._parse_evaluation_response(valid_json)

        assert isinstance(result, EvaluationResult)
        assert result.what_score == 3
        assert result.why_score == 4
        assert result.overall_score == 3.5
        assert result.reasoning == "Test reasoning"
        assert result.confidence == 0.75

    def test_parse_evaluation_response_missing_fields(self):
        """Test parsing JSON response with missing required fields."""
        evaluator = CommitMessageEvaluator()

        # Missing required fields should raise an error
        incomplete_json = '{"what_score": 3}'

        with pytest.raises(ValueError, match="Failed to parse evaluation response"):
            evaluator._parse_evaluation_response(incomplete_json)

    def test_parse_evaluation_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        evaluator = CommitMessageEvaluator()

        invalid_json = "this is not json"

        with pytest.raises(ValueError, match="Failed to parse evaluation response"):
            evaluator._parse_evaluation_response(invalid_json)
