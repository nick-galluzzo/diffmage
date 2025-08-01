"""
Tests for the GenerationService class.
"""

import pytest
from unittest.mock import Mock, patch
from diffmage.generation.service import GenerationService
from diffmage.generation.models import GenerationResult, GenerationRequest
from diffmage.core.models import (
    CommitAnalysis,
    FileDiff,
    ChangeType,
    FileType,
    DiffHunk,
    HunkLine,
)


class TestGenerationService:
    """Test cases for GenerationService class."""

    @pytest.fixture
    def mock_commit_analysis(self):
        """Create a mock CommitAnalysis for testing."""
        # Create a mock hunk with some content
        hunk_line1 = HunkLine(
            line_type=" ",
            is_removed=False,
            is_added=False,
            is_context=True,
            content="def example_function():",
            old_line_number=1,
            new_line_number=1,
        )
        hunk_line2 = HunkLine(
            line_type="+",
            is_removed=False,
            is_added=True,
            is_context=False,
            content="    print('Hello, world!')",
            old_line_number=None,
            new_line_number=2,
        )

        hunk = DiffHunk(
            old_start_line=1,
            old_lines_count=1,
            new_start_line=1,
            new_lines_count=2,
            section_header="",
            lines=[hunk_line1, hunk_line2],
        )

        file_diff = FileDiff(
            old_path=None,
            new_path="test.py",
            change_type=ChangeType.MODIFIED,
            file_type=FileType.SOURCE_CODE,
            is_binary=False,
            lines_added=1,
            lines_removed=0,
            hunks=[hunk],
        )

        return CommitAnalysis(
            files=[file_diff],
            total_files=1,
            total_lines_added=1,
            total_lines_removed=0,
            branch_name="main",
        )

    @patch("diffmage.generation.service.CommitMessageGenerator")
    @patch("diffmage.generation.service.GitDiffParser")
    def test_generate_commit_message_success(
        self, mock_git_parser_class, mock_generator_class, mock_commit_analysis
    ):
        """Test successful commit message generation through service."""
        # Setup mocks
        mock_parser = Mock()
        mock_parser.parse_staged_changes.return_value = mock_commit_analysis
        mock_git_parser_class.return_value = mock_parser

        mock_generator = Mock()
        mock_result = GenerationResult(message="feat: add new feature")
        mock_generator.generate_commit_message.return_value = mock_result
        mock_generator_class.return_value = mock_generator

        # Create service and request
        service = GenerationService(model_name="openai/gpt-4o-mini")
        request = GenerationRequest(repo_path=".")

        # Execute
        result = service.generate_commit_message(request)

        # Verify
        assert isinstance(result, GenerationResult)
        assert result.message == "feat: add new feature"

        # Verify mocks were called correctly
        mock_git_parser_class.assert_called_once_with(repo_path=".")
        mock_parser.parse_staged_changes.assert_called_once()
        mock_generator_class.assert_called_once_with(model_name="openai/gpt-4o-mini")
        mock_generator.generate_commit_message.assert_called_once()

        # Verify the generator was called with correct parameters
        call_args = mock_generator.generate_commit_message.call_args
        assert call_args[0][0] == mock_commit_analysis.get_combined_diff()
        assert call_args[0][1] == mock_commit_analysis.total_files
        assert call_args[0][2] == mock_commit_analysis.total_lines_added
        assert call_args[0][3] == mock_commit_analysis.total_lines_removed
