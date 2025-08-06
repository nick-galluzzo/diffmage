"""
Tests for the CommitMessageGenerator class.
"""

import pytest
from unittest.mock import Mock, patch
from diffmage.generation.commit_message_generator import CommitMessageGenerator
from diffmage.generation.models import GenerationResult
from diffmage.ai.client import AIClient


class TestCommitMessageGenerator:
    """Test cases for CommitMessageGenerator class."""

    def test_init_with_default_model(self):
        """Test CommitMessageGenerator initialization with default model."""
        with patch(
            "diffmage.generation.commit_message_generator.get_default_model"
        ) as mock_get_model:
            mock_model = Mock()
            mock_model.name = "openai/gpt-4o-mini"
            mock_get_model.return_value = mock_model

            generator = CommitMessageGenerator()

            assert generator.model_name == "openai/gpt-4o-mini"
            assert isinstance(generator.client, AIClient)
            assert generator.client.model_config.name == "openai/gpt-4o-mini"

    def test_init_with_custom_model(self):
        """Test CommitMessageGenerator initialization with custom model."""
        generator = CommitMessageGenerator(model_name="anthropic/claude-sonnet-4")

        assert generator.model_name == "anthropic/claude-sonnet-4"
        assert generator.client.model_config.name == "anthropic/claude-sonnet-4"

    def test_init_with_custom_temperature(self):
        """Test CommitMessageGenerator initialization with custom temperature."""
        generator = CommitMessageGenerator(temperature=0.5)

        assert generator.client.temperature == 0.5

    def test_generate_commit_message_success(self):
        """Test successful commit message generation."""
        generator = CommitMessageGenerator(model_name="openai/gpt-4o-mini")

        # Mock the AI client response
        mock_response = "feat: add user authentication"

        with patch.object(
            generator.client, "generate_commit_message", return_value=mock_response
        ):
            result = generator.generate_commit_message(
                "--- a/auth.py\n+++ b/auth.py\n@@ -1 +1 @@\n+def login(): pass",
                file_count=1,
                lines_added=1,
                lines_removed=0,
            )

            assert isinstance(result, GenerationResult)
            assert result.message == "feat: add user authentication"

    def test_generate_commit_message_empty_diff(self):
        """Test generation with empty git diff."""
        generator = CommitMessageGenerator()

        with pytest.raises(ValueError, match="No changes found in git diff"):
            generator.generate_commit_message("")

    def test_generate_commit_message_ai_error(self):
        """Test generation when AI call fails."""
        generator = CommitMessageGenerator()

        with patch.object(
            generator.client,
            "generate_commit_message",
            side_effect=Exception("API Error"),
        ):
            with pytest.raises(ValueError, match="Error generating commit message"):
                generator.generate_commit_message("test diff")

    def test_build_prompt(self):
        """Test prompt building."""
        generator = CommitMessageGenerator()

        # Mock the prompt manager
        with patch(
            "diffmage.generation.commit_message_generator.get_commit_prompt"
        ) as mock_get_prompt:
            mock_get_prompt.return_value = "Generated prompt"

            prompt = generator._build_prompt(
                "test diff", file_count=1, lines_added=5, lines_removed=2
            )

            assert prompt == "Generated prompt"
            mock_get_prompt.assert_called_once_with(
                diff_content="test diff", file_count=1, lines_added=5, lines_removed=2
            )

    def test_enhance_with_why_context_success(self):
        """Test successful enhancement with why context."""
        generator = CommitMessageGenerator(model_name="openai/gpt-4o-mini")
        initial_result = GenerationResult(message="feat: add authentication")
        why_context = "Implementing OAuth2 for better security compliance"

        with patch(
            "diffmage.generation.commit_message_generator.get_why_context_prompt"
        ) as mock_get_prompt:
            mock_get_prompt.return_value = "Enhanced prompt"

            with patch.object(
                generator.client,
                "generate_commit_message",
                return_value="feat: implement OAuth2 authentication for security compliance",
            ):
                result = generator.enhance_with_why_context(initial_result, why_context)

                assert isinstance(result, GenerationResult)
                assert (
                    result.message
                    == "feat: implement OAuth2 authentication for security compliance"
                )
                mock_get_prompt.assert_called_once_with(
                    "feat: add authentication", why_context
                )

    def test_enhance_with_why_context_empty_context(self):
        """Test enhancement with empty why context returns original result."""
        generator = CommitMessageGenerator()
        initial_result = GenerationResult(message="feat: add authentication")

        result = generator.enhance_with_why_context(initial_result, "")

        assert result is initial_result

    def test_enhance_with_why_context_ai_error(self):
        """Test enhancement when AI call fails."""
        generator = CommitMessageGenerator()
        initial_result = GenerationResult(message="feat: add authentication")
        why_context = "Adding for security"

        with patch(
            "diffmage.generation.commit_message_generator.get_why_context_prompt"
        ):
            with patch.object(
                generator.client,
                "generate_commit_message",
                side_effect=Exception("API Error"),
            ):
                with pytest.raises(
                    ValueError, match="Error enhancing commit message with why context"
                ):
                    generator.enhance_with_why_context(initial_result, why_context)
