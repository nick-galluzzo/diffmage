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
    return f"""You are a Git expert. Your task is to decide whether to enhance a commit message with external context.

    STRICT EVALUATION CRITERIA:
    - Does the context explain a USER PROBLEM or BUSINESS NEED that's not obvious from the code changes?
    - Does it add meaningful insight about WHY this change was necessary?
    - Does it avoid redundant technical implementation details already clear from the diff?

    <ORIGINAL_COMMIT_MESSAGE>
    {preliminary_message}
    </ORIGINAL_COMMIT_MESSAGE>

    <EXTERNAL_CONTEXT>
    {why_context}
    </EXTERNAL_CONTEXT>

    <INSTRUCTIONS>
    1. First decide: Does this <EXTERNAL_CONTEXT> add valuable WHY information that explains user problems, business needs, or meaningful impact?

    2. If NO (context is technical details, obvious info, or redundant):
    - Return the <ORIGINAL_COMMIT_MESSAGE> EXACTLY as provided

    3. If YES (<EXTERNAL_CONTEXT> explains real user problems, value, impact, reasoning, intent, context, background, implications):
    - Add 1-5 concise sentences after the bullet points
    - Focus on: What problem did this solve? What was the reasoning and intent? What is the context or background? What are the implications and impact?
        - A gold standard "WHY" of a commit message explains the rationale and intent behind the changes made in a git commit. It goes beyond simply stating what was changed and delves into why those changes were necessary.
    - Focus on this scenario: If a developer is to come across this in a git blame months down the road, what would they want and need to know?
    - Keep it under 150 words total addition
    </INSTRUCTIONS>

    EXAMPLES OF GOOD <EXTERNAL_CONTEXT> TO CONSIDER:
    - "Users were experiencing 3-second page load delays during peak traffic"
    - "Support team received 50+ tickets weekly about login failures"
    - "Business requirement to comply with GDPR by Q2"

    EXAMPLES OF BAD <EXTERNAL_CONTEXT> TO IGNORE:
    - "The previous implementation passed the full result object instead of just the message content"
    - "This ensures proper test coverage for the new feature"
    - "Using result.message to follow the pydantic structure"

    Output the final commit message only:"""


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
        * 5 = All high impactchanges captured accurately and completely with precise details.
        * 4 = Main changes described accurately and clearly, only minor details missing
        * 3 = Core changes described, some important details missing
        * 2 = Basic changes mentioned, significant gaps in description
        * 1 = Major changes omitted or misrepresented

    - WHY (1-5): How clearly does it explain the PURPOSE/REASONING/IMPACT of the changes?
        * 5 = Clear user problem + impact, intent, reasoning, context, background, implications explained.
        * 4 = Good rationale with clear benefit/motivation
        * 3 = Basic purpose explained, could be clearer, minimal impact context
        * 2 = Minimal or technical-only reasoning, no user problem, impact, intent, reasoning, context, background, implications explained
        * 1 = No explanation of purpose/impact beyond obvious technical changes
    </EVALUATION_CRITERIA>

    <EXAMPLES>
    Example 1:
    COMMIT: "update config"

    DIFF:
    --- a/config/database.yml
    +++ b/config/database.yml
    @@ -5,7 +5,7 @@ production:
    adapter: postgresql
    encoding: unicode
    database: myapp_production
    -  pool: 5
    +  pool: 25
    username: <%= ENV['DATABASE_USER'] %>
    password: <%= ENV['DATABASE_PASS'] %>

    ANALYSIS:
    - WHAT: 2/5 - Basic changes mentioned but significant gaps: doesn't specify what config change or why pool size matters
    - WHY: 1/5 - No explanation of purpose/impact beyond obvious technical changes

    Example 2:
    COMMIT: "chore: upgrade React from v16 to v18 for better performance

    Updates all React dependencies and components to use new APIs. Improves rendering
    performance and enables concurrent features for smoother user interactions."

    DIFF:
    --- a/package.json
    +++ b/package.json
    @@ -10,8 +10,8 @@
    "dependencies":
    -    "react": "^16.14.0",
    -    "react-dom": "^16.14.0",
    +    "react": "^18.2.0",
    +    "react-dom": "^18.2.0",
        "react-router": "^6.0.0"

    --- a/src/App.jsx
    +++ b/src/App.jsx
    @@ -1,4 +1,4 @@
    -import (render) from 'react-dom';
    +import (createRoot) from 'react-dom/client';

    -(render)(<App />, document.getElementById('root'));
    +(const root = createRoot(document.getElementById('root'));
    +root.render(<App />);

    ANALYSIS:
    - WHAT: 4/5 - Main changes described accurately: version upgrade and API updates, minor implementation details missing
    - WHY: 3/5 - Basic purpose explained (performance, concurrent features) but could be clearer about specific benefits

    Example 3:
    COMMIT: "fix: correct email validation regex to prevent invalid addresses

    Email validation was accepting malformed addresses like 'user@' and 'invalid.email',
    causing downstream errors in the notification system and user registration failures."

    DIFF:
    --- a/src/utils/validation.js
    +++ b/src/utils/validation.js
    @@ -8,7 +8,7 @@ export const validateEmail = (email) => (
        return false;

    -  const emailRegex = /S+@S+/;
    +  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{(2,)}$/;
    return emailRegex.test(email)

    ANALYSIS:
    - WHAT: 4/5 - Main changes described clearly: email validation fix with specific problem examples
    - WHY: 4/5 - Good rationale with clear benefit: prevents downstream errors and registration issues

    Example 4:
    COMMIT: "feat: implement caching layer reducing API response time by 75%

    Added Redis caching for frequently accessed product data after observing
    average API response times of 2.4 seconds affecting user experience.
    Cache hits now serve requests in 300ms, improving page load performance
    and reducing database load by 60%.

    Implements TTL of 1 hour with automatic cache invalidation on product updates."

    DIFF:
    --- a/src/services/productService.js
    +++ b/src/services/productService.js
    @@ -1,4 +1,5 @@
    const database = require('../database');
    +const redis = require('redis');
    +const client = redis.createClient();

    class ProductService (
    async getProduct(id)
    +    // Check cache first
    +    const cached = await client.get(`product:$(id)`);
    +    if (cached) )
    +      return JSON.parse(cached);
    +    )
    +
        const product = await database.query('SELECT * FROM products WHERE id = ?', [id]);
    +
    +    // Cache for 1 hour
    +    await client.setex(`product:$(id)`, 3600, JSON.stringify(product));
        return product;
    )
    )

    ANALYSIS:
    - WHAT: 5/5 - All high impact changes captured with precise details: Redis integration, caching logic, TTL configuration
    - WHY: 5/5 - Clear user problem (2.4s response times) + quantified impact (75% reduction, 300ms response) + comprehensive context (database load reduction)

    Example 5:
    COMMIT: "test: add unit tests for password hashing utility"

    DIFF:
    --- /dev/null
    +++ b/tests/utils/passwordUtils.test.js
    @@ -0,0 +1,25 @@
    +const ( hashPassword, verifyPassword ) = require('../../src/utils/passwordUtils');
    +
    +describe('Password Utils', () => (
    +  test('should hash password correctly', () => (
    +    const password = 'testpassword123';
    +    const hash = hashPassword(password);
    +    expect(hash).toBeDefined();
    +    expect(hash).not.toBe(password);
    +  )
    +
    +  test('should verify correct password', () => (
    +    const password = 'testpassword123';
    +    const hash = hashPassword(password);
    +    expect(verifyPassword(password, hash)).toBe(true);
    +  )
    +);

    ANALYSIS:
    - WHAT: 3/5 - Core changes described: test addition for password utility, some important details missing about test coverage
    - WHY: 2/5 - Minimal reasoning: no explanation of why tests were needed or what problems they prevent
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
