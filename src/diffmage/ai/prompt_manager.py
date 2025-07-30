"""
AI prompt management for commit message generation.
"""

from typing import Optional


def get_commit_prompt(
    diff_content: str,
    file_count: Optional[int] = None,
    lines_added: Optional[int] = None,
    lines_removed: Optional[int] = None,
) -> str:
    """
    Generate a commit message prompt optimized for LLMS.
    """

    # Build context information
    context_parts = []
    if file_count is not None:
        context_parts.append(f"{file_count} file{'s' if file_count > 1 else ''}")
    if lines_added is not None and lines_removed is not None:
        context_parts.append(
            f"{lines_added} lines added, {lines_removed} lines removed"
        )

    context_info = f" ({', '.join(context_parts)})" if context_parts else ""

    prompt = f"""Analyze the following <git_diff> and generate a concise commit message {context_info}:

  Instructions:
  - Use conventional commits format:<type>(<optional scope>): <description>
  - Keep the description under 100 characters
  - Use imperative mood ("add", "fix", "update", not "added", "fixed", "updated")
  - Focus on WHAT changed and WHY, not HOW. Consider WHAT was impacted and WHY.

  Common types:
  - feat: New feature, enhancement, or functionality
  - fix: Bug fix or error correction
  - refactor: Code restructuring without changing functionality
  - docs: Documentation changes only
  - test: Adding or updating tests
  - chore: Maintenance, dependencies, build changes

  <git_diff>
  {diff_content}
  </git_diff>

  Generate the commit message, nothing else.

  Commit message:
  """

    return prompt


def get_system_prompt() -> str:
    """
    System prompt that provides consistent context for commit message generation.
    """

    return """
  Your commit messages are:
  - Descriptive but brief
  - Written in imperative mood
  - Focused on the purpose and impact of changes
  - Helpful for other developers and future maintenance
  - Following industry best practices for writing commit messages

  Analyze code changes carefully and generate commit messages that accurately describe what was changed and why.
  """
