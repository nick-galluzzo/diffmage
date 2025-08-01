from litellm import completion
from litellm.types.utils import ModelResponse
from litellm.litellm_core_utils.streaming_handler import CustomStreamWrapper
from typing import Union
from diffmage.ai.models import get_model_by_name
from diffmage.ai.prompt_manager import (
    get_generation_system_prompt,
    get_evaluation_system_prompt,
)


class AIClient:
    """
    Client for interacting with AI models

    Methods:
        - generate_commit_message: Generate a commit message from a git analysis
        - evaluate_with_llm: Evaluate commit message quality using Chain of Thought reasoning
    """

    def __init__(
        self, model_name: str, temperature: float = 0.1, max_tokens: int = 1000
    ):
        self.model_config = get_model_by_name(model_name)
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate_commit_message(self, commit_prompt: str) -> str:
        """Generate commit message from git analysis"""

        try:
            response: Union[ModelResponse, CustomStreamWrapper] = completion(
                model=self.model_config.name,
                messages=[
                    {"role": "system", "content": get_generation_system_prompt()},
                    {"role": "user", "content": commit_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False,
            )

            return response.choices[0].message.content.strip()  # type: ignore

        except Exception as e:
            raise ValueError(f"Error generating commit message: {e}")

    def evaluate_with_llm(self, evaluation_prompt: str) -> str:
        """
        Execute LLM call for commit message evaluation.

        Args:
            evaluation_prompt: Complete evaluation prompt with a provided commit message and git diff

        Returns:
            str: Raw LLM response for parsing by LLMEvaluator

        Raises:
            ValueError: If LLM request fails
        """

        try:
            response: Union[ModelResponse, CustomStreamWrapper] = completion(
                model=self.model_config.name,
                messages=[
                    {"role": "system", "content": get_evaluation_system_prompt()},
                    {"role": "user", "content": evaluation_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False,
            )

            return response.choices[0].message.content.strip()  # type: ignore

        except Exception as e:
            raise ValueError(f"Error evaluating commit message: {e}")
