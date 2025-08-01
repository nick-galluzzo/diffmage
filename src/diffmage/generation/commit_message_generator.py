"""LLM based commit message generator"""

from typing import Optional
from diffmage.ai.client import AIClient
from diffmage.ai.models import get_default_model
from diffmage.ai.prompt_manager import get_commit_prompt
from diffmage.generation.models import GenerationResult


class CommitMessageGenerator:
    """
    LLM based commit message generator

    This specialist focuses solely on the generation logic and prompt handling
    """

    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.1):
        """
        Initialize the LLM Generator

        Args:
          model_name: The name of the model to use for generation
          temperature: The temperature to use for generation
        """
        self.model_name = model_name or get_default_model().name
        self.client = AIClient(model_name=self.model_name, temperature=temperature)

    def generate_commit_message(
        self,
        git_diff: str,
        file_count: int = 0,
        lines_added: int = 0,
        lines_removed: int = 0,
    ) -> GenerationResult:
        """
        Generate a commit message from code analysis.

        Args:
            analysis: Parsed git diff analysis
            request: Generation configuration

        Returns:
            GenerationResult with message and metadata
        """

        if not git_diff.strip():
            raise ValueError("No changes found in git diff")

        prompt = self._build_prompt(git_diff, file_count, lines_added, lines_removed)

        try:
            message = self.client.generate_commit_message(prompt)
            return GenerationResult(message=message.strip())

        except Exception as e:
            raise ValueError(f"Error generating commit message: {e}")

    def _build_prompt(
        self, git_diff: str, file_count: int, lines_added: int, lines_removed: int
    ) -> str:
        """
        Build the appropriate prompt
        """

        return get_commit_prompt(
            diff_content=git_diff,
            file_count=file_count,
            lines_added=lines_added,
            lines_removed=lines_removed,
        )
