"""
LLM based commit message evaluator using Chain-of-Thought reasoning.
Based on research achieving 0.65/0.79 Spearman correlation with human judgment.

Evaluating Generated Commit Messages with Large Language Models:
https://arxiv.org/pdf/2507.10906
"""

import json

from diffmage.ai.prompt_manager import get_evaluation_prompt
from diffmage.evaluation.models import EvaluationResult
from diffmage.ai.models import get_default_model
from diffmage.ai.client import AIClient
from typing import Optional


class CommitMessageEvaluator:
    """
    LLM based commit message quality evaluator using Chain of Thought Reasoning

    Evaluates commit message quality  across two dimensions:
    - WhHAT: How accurately the message describes the code changes
    - WHY: How clearly it explains the purpose/reasoning/impact of the changes

    """

    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.7):
        """
        Initialize the LLM evaluator.

        Args:
            model_name: LLM model to use for evaluation.
            temperature: Sampling temperature (0.0-1.0).
                        Low values (0.1) recommended for consistent evaluation.
        """

        if model_name is None:
            self.model_name = get_default_model().name
        else:
            self.model_name = model_name

        self.ai_client = AIClient(model_name=self.model_name, temperature=temperature)

    def evaluate_commit_message(
        self, commit_message: str, git_diff: str
    ) -> EvaluationResult:
        """
        Analyzes how well the commit message describes WHAT changed and WHY,
        providing scores (1-5 scale) with detailed reasoning.

        Args:
            commit_message: The commit message to evaluate.
                            Can be single line or multi-line format.
            git_diff: Git diff in unified format showing the actual changes.
        """

        if not commit_message.strip():
            return EvaluationResult(
                what_score=1.0,
                why_score=1.0,
                reasoning="Empty commit message provides no information",
                confidence=1.0,
                model_used=self.model_name,
            )

        if not git_diff.strip():
            return EvaluationResult(
                what_score=1.0,
                why_score=1.0,
                reasoning="No diff provided. Cannot assess commit content",
                confidence=1.0,
                model_used=self.model_name,
            )

        try:
            evaluation_prompt = get_evaluation_prompt(commit_message, git_diff)
            response = self.ai_client.evaluate_with_llm(evaluation_prompt)
        except Exception as e:
            raise ValueError(f"Failed to evaluate commit message: {e}")

        return self._parse_evaluation_response(response)

    def _parse_evaluation_response(self, response: str) -> EvaluationResult:
        """Parse LLM JSON response into EvaluationResult"""

        try:
            data = json.loads(response)
            data["model_used"] = self.model_name

            return EvaluationResult(**data)
        except Exception as e:
            raise ValueError(f"Failed to parse evaluation response: {e}")
