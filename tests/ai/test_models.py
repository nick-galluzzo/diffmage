import pytest
from diffmage.ai.models import (
    SupportedModels,
    ModelConfig,
    get_model_by_name,
    get_default_model,
)


def test_supported_models_enum():
    """Test that all supported models have proper configuration."""
    # Test that we can access all models
    assert len(SupportedModels) > 0

    # Test that each model has the required attributes
    for model in SupportedModels:
        config = model.value
        assert isinstance(config, ModelConfig)
        assert config.name
        assert config.display_name
        assert config.description
        assert isinstance(config.name, str)
        assert isinstance(config.display_name, str)
        assert isinstance(config.description, str)


def test_get_model_by_name_success():
    """Test successful model lookup by name."""
    # Test with a known model
    model_config = get_model_by_name("openai/gpt-4o-mini")
    assert model_config.name == "openai/gpt-4o-mini"
    assert model_config.display_name == "GPT-4o Mini"

    # Test with another known model
    model_config = get_model_by_name("anthropic/claude-haiku")
    assert model_config.name == "anthropic/claude-haiku"
    assert model_config.display_name == "Claude Haiku"


def test_get_model_by_name_failure():
    """Test model lookup with invalid name."""
    with pytest.raises(ValueError, match="Model invalid/model not found"):
        get_model_by_name("invalid/model")


def test_get_default_model():
    """Test that default model is properly configured."""
    default_model = get_default_model()
    assert isinstance(default_model, ModelConfig)
    assert default_model.name
    assert default_model.display_name
    assert default_model.description

    # Verify it's one of the supported models
    model_names = [model.value.name for model in SupportedModels]
    assert default_model.name in model_names


def test_model_configs_have_valid_names():
    """Test that all model configs have valid LiteLLM-compatible names."""
    for model in SupportedModels:
        config = model.value
        # Should contain provider/model format
        assert "/" in config.name
        assert len(config.name.split("/")) >= 2


def test_openrouter_models_have_correct_prefix():
    """Test that OpenRouter models have the correct prefix."""
    openrouter_models = [
        SupportedModels.DEEPSEEK_V3_0324_FREE,
        SupportedModels.QWEN_3_CODER_FREE,
        SupportedModels.DEEPSEEK_R1_0528_FREE,
        SupportedModels.Z_AI_GLM_4_5_AIR_FREE,
        SupportedModels.LLAMA_4_MAVERICK,
        SupportedModels.Z_AI_GLM_4_5,
        SupportedModels.Z_AI_GLM_4_5_AIR,
    ]

    for model in openrouter_models:
        config = model.value
        assert config.name.startswith("openrouter/")
