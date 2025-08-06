import pytest
from unittest.mock import Mock, patch
from diffmage.ai.client import AIClient
from diffmage.core.models import (
    CommitAnalysis,
    FileDiff,
    ChangeType,
    FileType,
    DiffHunk,
    HunkLine,
)
from diffmage.ai.models import get_default_model


@pytest.fixture
def mock_commit_analysis():
    """Create a mock CommitAnalysis for testing."""
    hunk_line = HunkLine(
        line_type="+",
        is_removed=False,
        is_added=True,
        is_context=False,
        content="def new_function():",
        old_line_number=None,
        new_line_number=1,
    )

    hunk = DiffHunk(
        old_start_line=1,
        old_lines_count=0,
        new_start_line=1,
        new_lines_count=1,
        section_header="",
        lines=[hunk_line],
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


@pytest.fixture
def mock_ai_response():
    """Create a mock AI response."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "feat: add new feature"
    return mock_response


def test_ai_client_initialization():
    """Test AIClient initialization with default parameters."""
    client = AIClient(model_name="openai/gpt-4o-mini")

    assert client.model_config.name == "openai/gpt-4o-mini"
    assert client.temperature == 0.0
    assert client.max_tokens == 1000


def test_ai_client_initialization_with_custom_params():
    """Test AIClient initialization with custom parameters."""
    client = AIClient(
        model_name="anthropic/claude-haiku", temperature=0.0, max_tokens=2000
    )

    assert client.model_config.name == "anthropic/claude-haiku"
    assert client.temperature == 0.0
    assert client.max_tokens == 2000


def test_ai_client_initialization_uses_default_model():
    """Test AIClient initialization uses default model when none specified."""
    default_model = get_default_model()
    client = AIClient(model_name=default_model.name)

    assert client.model_config.name == default_model.name


@patch("diffmage.ai.client.completion")
def test_generate_commit_message_success(mock_completion, mock_ai_response):
    """Test successful commit message generation."""
    # Setup mock
    mock_completion.return_value = mock_ai_response

    # Create client and generate message
    client = AIClient(model_name="openai/gpt-4o-mini")
    prompt = "test prompt"
    result = client.generate_commit_message(prompt)

    # Verify result
    assert result == "feat: add new feature"

    # Verify completion was called with correct parameters
    mock_completion.assert_called_once()
    call_args = mock_completion.call_args
    assert call_args[1]["model"] == "openai/gpt-4o-mini"
    assert call_args[1]["temperature"] == 0.0
    assert call_args[1]["max_tokens"] == 1000
    assert call_args[1]["stream"] is False

    # Verify messages structure
    messages = call_args[1]["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


@patch("diffmage.ai.client.completion")
def test_generate_commit_message_ai_error(mock_completion, mock_commit_analysis):
    """Test commit message generation when AI service fails."""
    # Setup mock to raise exception
    mock_completion.side_effect = Exception("AI service unavailable")

    client = AIClient(model_name="openai/gpt-4o-mini")

    with pytest.raises(
        ValueError, match="Error generating commit message: AI service unavailable"
    ):
        client.generate_commit_message(mock_commit_analysis)


@patch("diffmage.ai.client.completion")
def test_generate_commit_message_with_custom_params(
    mock_completion, mock_commit_analysis, mock_ai_response
):
    """Test commit message generation with custom client parameters."""
    # Setup mock
    mock_completion.return_value = mock_ai_response

    # Create client with custom parameters
    client = AIClient(
        model_name="anthropic/claude-haiku", temperature=0.0, max_tokens=1500
    )
    result = client.generate_commit_message(mock_commit_analysis)

    # Verify result
    assert result == "feat: add new feature"

    # Verify completion was called with custom parameters
    mock_completion.assert_called_once()
    call_args = mock_completion.call_args
    assert call_args[1]["model"] == "anthropic/claude-haiku"
    assert call_args[1]["temperature"] == 0.0
    assert call_args[1]["max_tokens"] == 1500


@patch("diffmage.ai.client.completion")
def test_generate_commit_message_strips_whitespace(
    mock_completion, mock_commit_analysis
):
    """Test that generated commit message has whitespace stripped."""
    # Setup mock with whitespace
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "  feat: add new feature  \n"
    mock_completion.return_value = mock_response

    client = AIClient(model_name="openai/gpt-4o-mini")
    result = client.generate_commit_message(mock_commit_analysis)

    # Verify whitespace is stripped
    assert result == "feat: add new feature"


@pytest.fixture
def mock_evaluation_response():
    """Create a mock evaluation response."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = """{
        "what_score": 4,
        "why_score": 5,
        "overall_score": 4.5,
        "reasoning": "The commit message accurately describes the changes and clearly explains the purpose.",
        "confidence": 0.9,
        "model_used": "openai/gpt-4o-mini",
        "dimension": "unified"
    }"""
    return mock_response


@patch("diffmage.ai.client.completion")
def test_evaluate_with_llm_success(mock_completion, mock_evaluation_response):
    """Test successful commit message evaluation."""
    # Setup mock
    mock_completion.return_value = mock_evaluation_response

    # Create client and evaluate
    client = AIClient(model_name="openai/gpt-4o-mini")
    evaluation_prompt = "test evaluation prompt"
    result = client.evaluate_with_llm(evaluation_prompt)

    # Verify result
    assert '"what_score": 4' in result
    assert '"why_score": 5' in result
    assert "reasoning" in result
    assert "confidence" in result

    # Verify completion was called with correct parameters
    mock_completion.assert_called_once()
    call_args = mock_completion.call_args
    assert call_args[1]["model"] == "openai/gpt-4o-mini"
    assert call_args[1]["temperature"] == 0.0
    assert call_args[1]["max_tokens"] == 1000
    assert call_args[1]["stream"] is False

    # Verify messages structure
    messages = call_args[1]["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert evaluation_prompt in messages[1]["content"]


@patch("diffmage.ai.client.completion")
def test_evaluate_with_llm_ai_error(mock_completion):
    """Test commit message evaluation when AI service fails."""
    # Setup mock to raise exception
    mock_completion.side_effect = Exception("AI service unavailable")

    client = AIClient(model_name="openai/gpt-4o-mini")
    evaluation_prompt = "test evaluation prompt"

    with pytest.raises(
        ValueError, match="Error evaluating commit message: AI service unavailable"
    ):
        client.evaluate_with_llm(evaluation_prompt)


@patch("diffmage.ai.client.completion")
def test_evaluate_with_llm_strips_whitespace(mock_completion):
    """Test that evaluation response has whitespace stripped."""
    # Setup mock with whitespace
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '  {"what_score": 4}  \n'
    mock_completion.return_value = mock_response

    client = AIClient(model_name="openai/gpt-4o-mini")
    evaluation_prompt = "test evaluation prompt"
    result = client.evaluate_with_llm(evaluation_prompt)

    # Verify whitespace is stripped
    assert result == '{"what_score": 4}'


@patch("diffmage.ai.client.completion")
def test_evaluate_with_llm_with_custom_params(
    mock_completion, mock_evaluation_response
):
    """Test commit message evaluation with custom client parameters."""
    # Setup mock
    mock_completion.return_value = mock_evaluation_response

    # Create client with custom parameters
    client = AIClient(
        model_name="anthropic/claude-haiku", temperature=0.0, max_tokens=1500
    )
    evaluation_prompt = "test evaluation prompt"
    result = client.evaluate_with_llm(evaluation_prompt)

    # Verify result
    assert '"what_score": 4' in result

    # Verify completion was called with custom parameters
    mock_completion.assert_called_once()
    call_args = mock_completion.call_args
    assert call_args[1]["model"] == "anthropic/claude-haiku"
    assert call_args[1]["temperature"] == 0.0
    assert call_args[1]["max_tokens"] == 1500
