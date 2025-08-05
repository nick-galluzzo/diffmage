from typing import Optional

from diffmage.git.diff_parser import GitDiffParser
from diffmage.core.models import CommitAnalysis
from diffmage.generation.commit_message_generator import CommitMessageGenerator
from diffmage.generation.models import GenerationResult, GenerationRequest


class GenerationService:
    """High level service for generating commit messages"""

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.generator = CommitMessageGenerator(model_name=model_name)

    def generate_commit_message(
        self, request: GenerationRequest, why_context: Optional[str] = None
    ) -> GenerationResult:
        """
        Generate a commit message from staged changes

        Args:
            request: Generation configuration

        Returns:
            GenerationResult with message and metadata
        """
        parser = GitDiffParser(repo_path=request.repo_path)
        analysis: CommitAnalysis = parser.parse_staged_changes()
        git_diff = analysis.get_combined_diff()
        file_count = analysis.total_files
        lines_added = analysis.total_lines_added
        lines_removed = analysis.total_lines_removed

        result: GenerationResult = self.generator.generate_commit_message(
            git_diff, file_count, lines_added, lines_removed
        )

        # handle why context separately to separate concerns and handle llm focus.
        # handling why context in the intial generate_commit_message was adding too
        # much noise to the commit message generation.
        if why_context:
            result: GenerationResult = self.generator.enhance_with_why_context(
                result, why_context
            )

        return result
