from typing import Optional
from diffmage.evaluation.models import EvaluationResult
from diffmage.ai.models import get_default_model
from diffmage.evaluation.llm_evaluator import LLMEvaluator
from diffmage.git.diff_parser import GitDiffParser


class EvaluationService:
    """High level service for evaluating commit messages"""

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or get_default_model().name
        self.evaluator = LLMEvaluator(model_name=self.model_name)

    def evaluate_staged_changes(
        self, message: str, repo_path: str = "."
    ) -> tuple[EvaluationResult, str]:
        """Evaluate the staged changes in the repository"""
        parser = GitDiffParser(repo_path)
        analysis = parser.parse_staged_changes()
        git_diff = analysis.get_combined_diff()
        result = self.evaluator.evaluate_commit_message(message, git_diff)

        return result, message

    def evaluate_commit(
        self, commit_hash: str, repo_path: str = "."
    ) -> tuple[EvaluationResult, str]:
        """Evaluate a specific commit in the repository"""
        parser = GitDiffParser(repo_path)
        analysis, message = parser.parse_specific_commit(commit_hash)
        git_diff = analysis.get_combined_diff()
        result = self.evaluator.evaluate_commit_message(message, git_diff)

        return result, message
