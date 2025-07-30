from dataclasses import dataclass
from enum import Enum


@dataclass
class ModelConfig:
    name: str
    display_name: str
    description: str


class SupportedModels(Enum):
    # OpenAI Models
    GPT_4o_MINI = ModelConfig(
        name="openai/gpt-4o-mini",
        display_name="GPT-4o Mini",
        description="Fast, cheap, and accurate. Good for most use cases.",
    )

    GPT_4o = ModelConfig(
        name="openai/gpt-4o",
        display_name="GPT-4o",
        description="Higher quality, more expensive.",
    )

    # Anthropic Models
    CLAUDE_SONNET_4 = ModelConfig(
        name="anthropic/claude-sonnet-4",
        display_name="Claude Sonnet 4",
        description="Latest Claude, excellent for code.",
    )

    CLAUDE_HAIKU = ModelConfig(
        name="anthropic/claude-haiku",
        display_name="Claude Haiku",
        description="Fast and cheap Claude model.",
    )

    # OpenRouter Models

    # Free OpenRouter Models
    DEEPSEEK_V3_0324_FREE = ModelConfig(
        name="openrouter/deepseek/deepseek-chat-v3-0324:free",
        display_name="DeepSeek V3 0324 (Free)",
        description="685B parameter model, mixture of experts model. Performs well on a variety of tasks.",
    )

    QWEN_3_CODER_FREE = ModelConfig(
        name="openrouter/qwen/qwen3-coder:free",
        display_name="Qwen 3.5 Coder (Free)",
        description="480B (MoE) model that excels in code generation. It is optimized for agentic coding tasks such as function calling, tool use, and long context reasoning over repositories.",
    )

    DEEPSEEK_R1_0528_FREE = ModelConfig(
        name="openrouter/deepseek/deepseek-r1-0528:free",
        display_name="DeepSeek R1 0528 (Free)",
        description="671B parameters. Performance on par with OpenAI o1.",
    )

    Z_AI_GLM_4_5_AIR_FREE = ModelConfig(
        name="openrouter/z-ai/glm-4.5-air:free",
        display_name="Z-AI GLM 4.5 Air (Free)",
        description="Lightweight version of Z-AI GLM 4.5.",
    )

    # Paid OpenRouter Models
    QWEN_3_CODER = ModelConfig(
        name="openrouter/qwen/qwen3-coder",
        display_name="Qwen 3.5 Coder",
        description="480B (MoE) model that excels in code generation. It is optimized for agentic coding tasks such as function calling, tool use, and long context reasoning over repositories.",
    )

    LLAMA_4_MAVERICK = ModelConfig(
        name="openrouter/meta-llama/llama-4-maverick",
        display_name="Llama 4 Maverick",
        description="Llama 4 Maverick is a 17B (MoE). Supports multilingual text and image input and produces multilingual text and code. Tuned for assistant like behavior and general purpose multi-modal interaction.",
    )

    Z_AI_GLM_4_5 = ModelConfig(
        name="openrouter/z-ai/glm-4.5",
        display_name="Z-AI GLM 4.5",
        description="Reasoning, code generation, and agent alignment. Supports thinking and non thinking modes.",
    )

    Z_AI_GLM_4_5_AIR = ModelConfig(
        name="openrouter/z-ai/glm-4.5-air",
        display_name="Z-AI GLM 4.5 Air",
        description="Lightweight version of Z-AI GLM 4.5.",
    )


def get_model_by_name(name: str) -> ModelConfig:
    """Get model config by LiteLLM name"""
    for model in SupportedModels:
        if model.value.name == name:
            return model.value
    raise ValueError(f"Model {name} not found")


def get_default_model() -> ModelConfig:
    """Get default model"""
    return SupportedModels.QWEN_3_CODER_FREE.value
