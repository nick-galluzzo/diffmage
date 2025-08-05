"""
AI prompt management for commit message generation.
"""

from typing import Optional

# Generation prompts


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
  - Only return the commit message, nothing else.
  - Use imperative mood ("add", "fix", "update", not "added", "fixed", "updated")
  - Focus on WHAT changed and WHY, not HOW. Consider WHAT was impacted and WHY it was needed.

  Common types:
  - feat: New feature, enhancement, or functionality
  - fix: Bug fix or error correction
  - refactor: Code restructuring for readability, performance, or maintainability
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


def get_generation_system_prompt() -> str:
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


def get_why_context_prompt(preliminary_message: str, why_context: str) -> str:
    """
    Build the prompt for enhancing an existing commit message with external 'why' context.
    """
    return f"""
    You are a professional software engineer and an expert at writing concise, high-quality Git commit messages that follow the Conventional Commits specification.

    Your task is to refine and enhance the preliminary commit message by improving and expanding upon the "WHY" part of the commit message by integrating external context.

    Do not include any additional explanatory text, commentary, or conversational filler. The output should be ready to be copied and pasted directly into a `git commit` command.

    <PRELIMINARY_COMMIT_MESSAGE>
    {preliminary_message}
    </PRELIMINARY_COMMIT_MESSAGE>

    <EXTERNAL_CONTEXT>
    {why_context}
    </EXTERNAL_CONTEXT>

    <INSTRUCTION>
    Lead with the problem. Start the WHY by clearly stating the problem or issue that the change is solving, state the solution, and end with the benefit. Be concise but thorough.

    Based on the provided information, return the exact <preliminary_commit_message> with the enhanced "why" from the external context. Ensure the WHY follows the Conventional Commits format, ensuring the body clearly explains the problem and the benefit/impact of the change.

    Do not include any additional explanatory text, commentary, or conversational filler. The output should be ready to be copied and pasted directly into a `git commit` command.
    </INSTRUCTION>

    Final commit message:
    """


# Evaluation prompts


def get_evaluation_system_prompt() -> str:
    """
    System prompt that provides consistent context for commit message evaluation.
    """

    return """
  Your commit messages are:
  - Descriptive but brief
  - Written in imperative mood
  - Focused on the purpose and impact of changes
  """


def get_evaluation_prompt(commit_message: str, git_diff: str) -> str:
    """
    Chain of Thought evaluation prompt with few-shot examples.
    """

    return f"""You are an expert code reviewer evaluating commit message quality using Chain-of-Though reasoning.


    <EVALUATION_CRITERIA>
    - WHAT (1-5): How accurately and completely does the message describe the actual code changes?
        * 5 = All changes captured accurately and completely
        * 3 = Main changes described, some details missing
        * 1 = Major changes omitted or misrepresented
    - WHY (1-5): How clearly does it explain the purpose/reasoning/impact of the changes? Be more lenient on low impact changes.
    - Scale: 1=Very Poor, 2=Poor, 3=Average, 4=Good, 5=Excellent
    </EVALUATION_CRITERIA>

    <EXAMPLES>
    Example 1:
    COMMIT: "fix bug"

    DIFF:
        --- a/src/auth.py
    +++ b/src/auth.py
    @@ -15,1 +15,2 @@ def authenticate_user(username, password):
        user = get_user(username)
    -    return user.validate_password(password)
    +    if user:
    +        return user.validate_password(password)

    ANALYSIS:
    - WHAT: 2/5 - Too vague, doesn't specify what bug or where
    - WHY: 1/5 - No explanation of impact or reasoning

    Example 2:
    COMMIT: "feat(auth): add JWT authentication to secure API endpoints"
    DIFF:
    --- a/src/middleware/auth.py
    +++ b/src/middleware/auth.py
    @@ -0,0 +1,12 @@
    +import jwt
    +from flask import request, jsonify
    +
    +def require_auth(f):
    +    def decorated(*args, **kwargs):
    +        token = request.headers.get('Authorization')
    +        if not token:
    +            return jsonify({{'error': 'No token provided'}}), 401
    +        try:
    +            jwt.decode(token, app.config['SECRET_KEY'])
    +        except jwt.InvalidTokenError:
    +            return jsonify({{'error': 'Invalid token'}}), 401
    +        return f(*args, **kwargs)
    +    return decorated

    + def add_items_to_cart(cart, items):
    +    # adds items to the cart
    +    if not items:
    +        raise ValueError('No items to add')
    +    cart.add_items(items)

    ANALYSIS:
    - WHAT: 3/5 - The commit message is missing important added functionality (doesn't mention the add_items_to_cart function)
    - WHY: 4/5 - Clear security purpose, could detail specific benefits


    Example 3:
    COMMIT: "refactor: extract validation logic into UserService class"
    DIFF:
    --- a/src/controllers/user_controller.py
    +++ b/src/controllers/user_controller.py
    @@ -8,6 +8,4 @@ class UserController:
        def create_user(self, data):
    -        if not data.get('email'):
    -            raise ValueError('Email required')
    -        if len(data.get('password', '')) < 8:
    -            raise ValueError('Password too short')
    +        UserService.validate_user_data(data)
            return User.create(data)
    --- a/src/services/user_service.py
    +++ b/src/services/user_service.py
    @@ -0,0 +1,8 @@
    +class UserService:
    +    @staticmethod
    +    def validate_user_data(data):
    +        if not data.get('email'):
    +            raise ValueError('Email required')
    +        if len(data.get('password', '')) < 8:
    +            raise ValueError('Password too short')

    ANALYSIS:
    - WHAT: 5/5 - Exact description of the refactoring action
    - WHY: 4/5 - Good architectural reasoning (separation of concerns)
    </EXAMPLES>

    NOW EVALUATE THE FOLLOWING COMMIT MESSAGE:
    <COMMIT_MESSAGE>
    {commit_message}
    </COMMIT_MESSAGE>

    <GIT_DIFF>
    {git_diff}
    </GIT_DIFF>

    <CHAIN-OF-THOUGHT EVALUATION>
    1. What changes do I see in the diff? Analyze ALL of them.
    2. How accurately and completely does the commit message describe these changes? (WHAT score)
    3. What purpose/goal do these changes serve?
    4. How clearly does the message explain the reasoning? (WHY score)
    5. Overall assessment combining both dimensions
    </CHAIN-OF-THOUGHT EVALUATION>

    <REASONING_INSTRUCTIONS>
    - Focus on the commit message effectiveness, not implementation details
    - Evaluate clarity, completeness, and usefulness
    - Analyze the message quality - don't just repeat its contents
    - Be specific about what makes it good or bad
    - Ensure to define and mention the what and the why
    - Keep it concise (3-5 sentences)
    </REASONING_INSTRUCTIONS>

    REQUIRED JSON RESPONSE:
    {{
        "what_score": <1-5>,
        "why_score": <1-5>,
        "reasoning": "<reasoning>",
        "confidence": <0.0-1.0>
    }}"""
