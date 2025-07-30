from litellm import completion
from litellm.types.utils import ModelResponse
from litellm.litellm_core_utils.streaming_handler import CustomStreamWrapper
from typing import Union
from diffmage.ai.models import get_model_by_name
from diffmage.ai.prompt_manager import get_commit_prompt, get_system_prompt
from diffmage.core.models import CommitAnalysis


class AIClient:
    def __init__(
        self, model_name: str, temperature: float = 0.3, max_tokens: int = 1000
    ):
        self.model_config = get_model_by_name(model_name)
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate_commit_message(self, analysis: CommitAnalysis) -> str:
        """Generate commit message from git analysis"""

        diff_ai_context = analysis.get_combined_diff()

        if not diff_ai_context:
            raise ValueError("No changes found to generate commit message for")

        prompt = get_commit_prompt(
            diff_content=diff_ai_context,
            file_count=analysis.total_files,
            lines_added=analysis.total_lines_added,
            lines_removed=analysis.total_lines_removed,
        )

        try:
            response: Union[ModelResponse, CustomStreamWrapper] = completion(
                model=self.model_config.name,
                messages=[
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False,
            )

            return response.choices[0].message.content.strip()  # type: ignore

        except Exception as e:
            raise ValueError(f"Error generating commit message: {e}")
