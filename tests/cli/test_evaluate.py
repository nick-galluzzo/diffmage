"""
Tests for the evaluate CLI command.
"""

import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from diffmage.cli.shared import app
from diffmage.evaluation.models import EvaluationResult


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_evaluation_result():
    """Create a mock EvaluationResult for testing."""
    return EvaluationResult(
        what_score=4.0,
        why_score=3.5,
        reasoning="The commit message accurately describes the changes and provides clear context.",
        confidence=0.85,
        model_used="openai/gpt-4o-mini",
    )


@patch("diffmage.cli.evaluate.EvaluationService")
def test_evaluate_command_with_message(
    mock_evaluation_service_class, runner, mock_evaluation_result
):
    """Test successful evaluate command execution with a commit message."""
    # Setup mocks
    mock_service = Mock()
    mock_service.evaluate_staged_changes.return_value = (
        mock_evaluation_result,
        "feat: add new feature",
    )
    mock_evaluation_service_class.return_value = mock_service

    # Run command
    result = runner.invoke(app, ["evaluate", "feat: add new feature"])

    # Verify result
    assert result.exit_code == 0

    # Verify mocks were called correctly
    mock_evaluation_service_class.assert_called_once()
    mock_service.evaluate_staged_changes.assert_called_once_with(
        "feat: add new feature", "."
    )


@patch("diffmage.cli.evaluate.EvaluationService")
def test_evaluate_command_with_commit_hash(
    mock_evaluation_service_class, runner, mock_evaluation_result
):
    """Test successful evaluate command execution with a commit hash."""
    # Setup mocks
    mock_service = Mock()
    mock_service.evaluate_commit.return_value = (
        mock_evaluation_result,
        "feat: add new feature",
    )
    mock_evaluation_service_class.return_value = mock_service

    # Run command
    result = runner.invoke(app, ["evaluate", "--commit", "HEAD"])

    # Verify result
    assert result.exit_code == 0

    # Verify mocks were called correctly
    mock_evaluation_service_class.assert_called_once()
    mock_service.evaluate_commit.assert_called_once_with("HEAD", ".")


@patch("diffmage.cli.evaluate.EvaluationService")
def test_evaluate_command_with_custom_model(
    mock_evaluation_service_class, runner, mock_evaluation_result
):
    """Test evaluate command with custom model."""
    # Setup mocks
    mock_service = Mock()
    mock_service.evaluate_staged_changes.return_value = (
        mock_evaluation_result,
        "feat: add new feature",
    )
    mock_evaluation_service_class.return_value = mock_service

    # Run command with custom model
    result = runner.invoke(
        app,
        ["evaluate", "feat: add new feature", "--model", "anthropic/claude-sonnet-4"],
    )

    # Verify result
    assert result.exit_code == 0

    # Verify EvaluationService was created with correct model
    mock_evaluation_service_class.assert_called_once()
    call_args = mock_evaluation_service_class.call_args
    assert call_args[1]["model_name"] == "anthropic/claude-sonnet-4"


@patch("diffmage.cli.evaluate.EvaluationService")
def test_evaluate_command_with_custom_repo(
    mock_evaluation_service_class, runner, mock_evaluation_result
):
    """Test evaluate command with custom repository path."""
    # Setup mocks
    mock_service = Mock()
    mock_service.evaluate_staged_changes.return_value = (
        mock_evaluation_result,
        "feat: add new feature",
    )
    mock_evaluation_service_class.return_value = mock_service

    # Run command with custom repo path
    result = runner.invoke(
        app, ["evaluate", "feat: add new feature", "--repo", "/custom/path"]
    )

    # Verify result
    assert result.exit_code == 0

    # Verify EvaluationService was called with correct parameters
    mock_evaluation_service_class.assert_called_once()
    mock_service.evaluate_staged_changes.assert_called_once_with(
        "feat: add new feature", "/custom/path"
    )


@patch("diffmage.cli.evaluate.EvaluationService")
def test_evaluate_command_with_short_flags(
    mock_evaluation_service_class, runner, mock_evaluation_result
):
    """Test evaluate command with short flag versions."""
    # Setup mocks
    mock_service = Mock()
    mock_service.evaluate_staged_changes.return_value = (
        mock_evaluation_result,
        "feat: add new feature",
    )
    mock_evaluation_service_class.return_value = mock_service

    # Run command with short flags
    result = runner.invoke(
        app,
        [
            "evaluate",
            "feat: add new feature",
            "-m",
            "anthropic/claude-sonnet-4",
            "-r",
            "/custom/path",
        ],
    )

    # Verify result
    assert result.exit_code == 0

    # Verify correct parameters were used
    mock_evaluation_service_class.assert_called_once_with(
        model_name="anthropic/claude-sonnet-4"
    )
    mock_service.evaluate_staged_changes.assert_called_once_with(
        "feat: add new feature", "/custom/path"
    )


def test_evaluate_command_missing_message_and_commit(runner):
    """Test evaluate command when neither message nor commit hash is provided."""
    # Run command without message or commit hash
    result = runner.invoke(app, ["evaluate"])

    # Verify result
    assert result.exit_code == 1
    assert "Error: Commit message or commit hash is required" in result.stdout


@patch("diffmage.cli.evaluate.EvaluationService")
def test_evaluate_command_service_error(
    mock_evaluation_service_class, runner, mock_evaluation_result
):
    """Test evaluate command when evaluation service raises an error."""
    # Setup mocks
    mock_service = Mock()
    mock_service.evaluate_staged_changes.side_effect = ValueError(
        "Evaluation service unavailable"
    )
    mock_evaluation_service_class.return_value = mock_service

    # Run command
    result = runner.invoke(app, ["evaluate", "feat: add new feature"])

    # Verify result
    assert result.exit_code == 1
    assert "Evaluation service unavailable" in str(result.exception)
