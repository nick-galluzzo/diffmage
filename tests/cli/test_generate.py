import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from diffmage.cli.shared import app
from diffmage.core.models import (
    CommitAnalysis,
    FileDiff,
    ChangeType,
    FileType,
    HunkLine,
    DiffHunk,
)
from diffmage.generation.models import GenerationResult


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_commit_analysis():
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
    hunk_line3 = HunkLine(
        line_type="-",
        is_removed=True,
        is_added=False,
        is_context=False,
        content="    print('Goodbye, world!')",
        old_line_number=2,
        new_line_number=None,
    )

    hunk = DiffHunk(
        old_start_line=1,
        old_lines_count=2,
        new_start_line=1,
        new_lines_count=2,
        section_header="",
        lines=[hunk_line1, hunk_line2, hunk_line3],
    )

    file_diff = FileDiff(
        old_path=None,
        new_path="test.py",
        change_type=ChangeType.MODIFIED,
        file_type=FileType.SOURCE_CODE,
        is_binary=False,
        lines_added=5,
        lines_removed=2,
        hunks=[hunk],
    )

    return CommitAnalysis(
        files=[file_diff],
        total_files=1,
        total_lines_added=5,
        total_lines_removed=2,
        branch_name="main",
    )


@patch("diffmage.cli.generate.GenerationService")
def test_generate_command_success(
    mock_generation_service_class, runner, mock_commit_analysis
):
    """Test successful generate command execution."""
    # Setup mocks
    mock_service = Mock()
    mock_result = GenerationResult(message="feat: add new feature")
    mock_service.generate_commit_message.return_value = mock_result
    mock_generation_service_class.return_value = mock_service

    # Run command
    result = runner.invoke(app, ["generate"])

    # Verify result
    assert result.exit_code == 0
    assert "Commit message: feat: add new feature" in result.stdout

    # Verify mocks were called correctly
    mock_generation_service_class.assert_called_once()
    mock_service.generate_commit_message.assert_called_once()


@patch("diffmage.cli.generate.GenerationService")
def test_generate_command_with_custom_model(
    mock_generation_service_class, runner, mock_commit_analysis
):
    """Test generate command with custom model."""
    # Setup mocks
    mock_service = Mock()
    mock_result = GenerationResult(message="fix: resolve bug")
    mock_service.generate_commit_message.return_value = mock_result
    mock_generation_service_class.return_value = mock_service

    # Run command with custom model
    result = runner.invoke(app, ["generate", "--model", "anthropic/claude-haiku"])

    # Verify result
    assert result.exit_code == 0
    assert "Commit message: fix: resolve bug" in result.stdout

    # Verify GenerationService was created with correct model
    mock_generation_service_class.assert_called_once()
    call_args = mock_generation_service_class.call_args
    assert call_args[1]["model_name"] == "anthropic/claude-haiku"


@patch("diffmage.cli.generate.GenerationService")
def test_generate_command_with_custom_repo(
    mock_generation_service_class, runner, mock_commit_analysis
):
    """Test generate command with custom repository path."""
    # Setup mocks
    mock_service = Mock()
    mock_result = GenerationResult(message="feat: add new feature")
    mock_service.generate_commit_message.return_value = mock_result
    mock_generation_service_class.return_value = mock_service

    # Run command with custom repo path
    result = runner.invoke(app, ["generate", "--repo", "/custom/path"])

    # Verify result
    assert result.exit_code == 0
    assert "Commit message: feat: add new feature" in result.stdout

    # Verify GenerationService was called with correct request
    mock_generation_service_class.assert_called_once()
    mock_service.generate_commit_message.assert_called_once()
    call_args = mock_service.generate_commit_message.call_args
    assert call_args[0][0].repo_path == "/custom/path"


@patch("diffmage.cli.generate.get_model_by_name")
def test_generate_command_invalid_model(mock_get_model_by_name, runner):
    """Test generate command with invalid model name."""
    # Setup mock to raise ValueError
    mock_get_model_by_name.side_effect = ValueError("Model invalid/model not found")

    # Run command with invalid model
    result = runner.invoke(app, ["generate", "--model", "invalid/model"])

    # Verify result
    assert result.exit_code == 1
    assert "Error: Model invalid/model not found" in result.stdout
    assert "Use --list-models to see available models" in result.stdout


@patch("diffmage.cli.generate.GenerationService")
def test_generate_command_ai_error(
    mock_generation_service_class, runner, mock_commit_analysis
):
    """Test generate command when AI service raises an error."""
    # Setup mocks
    mock_service = Mock()
    mock_service.generate_commit_message.side_effect = ValueError(
        "AI service unavailable"
    )
    mock_generation_service_class.return_value = mock_service

    # Run command
    result = runner.invoke(app, ["generate"])

    # Verify result
    assert result.exit_code == 1
    assert "AI service unavailable" in str(result.exception)


@patch("diffmage.cli.generate.GenerationService")
def test_generate_command_with_short_flags(
    mock_generation_service_class, runner, mock_commit_analysis
):
    """Test generate command with short flag versions."""
    # Setup mocks
    mock_service = Mock()
    mock_result = GenerationResult(message="feat: add new feature")
    mock_service.generate_commit_message.return_value = mock_result
    mock_generation_service_class.return_value = mock_service

    # Run command with short flags
    result = runner.invoke(
        app, ["generate", "-m", "anthropic/claude-haiku", "-r", "/custom/path"]
    )

    # Verify result
    assert result.exit_code == 0
    assert "Commit message: feat: add new feature" in result.stdout

    # Verify correct parameters were used
    mock_generation_service_class.assert_called_once_with(
        model_name="anthropic/claude-haiku"
    )
    mock_service.generate_commit_message.assert_called_once()
    call_args = mock_service.generate_commit_message.call_args
    assert call_args[0][0].repo_path == "/custom/path"


def test_generate_command_list_models(runner):
    """Test generate command with --list-models flag."""
    # Run command with list models flag
    result = runner.invoke(app, ["generate", "--list-models"])

    # Verify result
    assert result.exit_code == 0
    # Should contain table header
    assert "Available AI Models" in result.stdout
    # Should contain some model names
    assert "GPT-4o Mini" in result.stdout
    assert "Claude Haiku" in result.stdout


def test_generate_command_list_models_short_flag(runner):
    """Test generate command with short --list-models flag."""
    # Run command with list models flag (no short version available)
    result = runner.invoke(app, ["generate", "--list-models"])

    # Verify result
    assert result.exit_code == 0
    assert "Available AI Models" in result.stdout
