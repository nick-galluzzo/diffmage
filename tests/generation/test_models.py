"""
Tests for the generation models.
"""

from diffmage.generation.models import GenerationResult, GenerationRequest


class TestGenerationResult:
    """Test cases for GenerationResult model."""

    def test_generation_result_creation(self):
        """Test successful creation of GenerationResult."""
        result = GenerationResult(message="feat: add new feature")

        assert result.message == "feat: add new feature"

    def test_generation_result_validation_empty_message(self):
        """Test validation for empty message."""
        # Empty message should pass validation since there's no constraint
        result = GenerationResult(
            message=""  # Empty message should pass validation
        )

        assert result.message == ""

    def test_generation_result_validation_whitespace_message(self):
        """Test validation for whitespace-only message."""
        result = GenerationResult(
            message="   "  # Whitespace-only message should pass validation
        )

        assert result.message == "   "


class TestGenerationRequest:
    """Test cases for GenerationRequest model."""

    def test_generation_request_creation_with_default(self):
        """Test successful creation of GenerationRequest with default values."""
        request = GenerationRequest()

        assert request.repo_path == "."

    def test_generation_request_creation_with_custom_path(self):
        """Test successful creation of GenerationRequest with custom repository path."""
        request = GenerationRequest(repo_path="/custom/path")

        assert request.repo_path == "/custom/path"

    def test_generation_request_creation_with_empty_path(self):
        """Test successful creation of GenerationRequest with empty repository path."""
        request = GenerationRequest(repo_path="")

        assert request.repo_path == ""
