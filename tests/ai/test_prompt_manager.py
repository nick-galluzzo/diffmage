from diffmage.ai.prompt_manager import (
    get_commit_prompt,
    get_generation_system_prompt,
    get_evaluation_system_prompt,
    get_evaluation_prompt,
)


def test_get_generation_system_prompt():
    """Test that generation system prompt is properly formatted and contains expected content."""
    system_prompt = get_generation_system_prompt()

    assert isinstance(system_prompt, str)
    assert len(system_prompt) > 0
    assert "commit messages" in system_prompt.lower()
    assert "descriptive" in system_prompt.lower()
    assert "imperative mood" in system_prompt.lower()


def test_get_evaluation_system_prompt():
    """Test that evaluation system prompt is properly formatted and contains expected content."""
    system_prompt = get_evaluation_system_prompt()

    assert isinstance(system_prompt, str)
    assert len(system_prompt) > 0
    assert "commit messages are:" in system_prompt.lower()
    assert "descriptive" in system_prompt.lower()
    assert "imperative mood" in system_prompt.lower()
    assert "purpose and impact" in system_prompt.lower()


def test_get_evaluation_prompt_basic():
    """Test basic evaluation prompt generation."""
    commit_message = "feat: add user authentication"
    git_diff = "--- a/auth.py\n+++ b/auth.py\n@@ -1 +1 @@\n+def login(): pass"

    prompt = get_evaluation_prompt(commit_message, git_diff)

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert commit_message in prompt
    assert git_diff in prompt
    assert "EVALUATION_CRITERIA" in prompt
    assert "WHAT (1-5)" in prompt
    assert "WHY (1-5)" in prompt
    assert "EXAMPLES" in prompt
    assert "CHAIN-OF-THOUGHT EVALUATION" in prompt
    assert "JSON RESPONSE" in prompt


def test_get_evaluation_prompt_with_complex_message():
    """Test evaluation prompt with complex commit message."""
    commit_message = "refactor(auth): extract validation logic into UserService class and add comprehensive error handling"
    git_diff = "--- a/src/controllers/user_controller.py\n+++ b/src/controllers/user_controller.py\n@@ -8,6 +8,4 @@ class UserController:\n        def create_user(self, data):\n-        if not data.get('email'):\n-            raise ValueError('Email required')\n-        if len(data.get('password', '')) < 8:\n-            raise ValueError('Password too short')\n+        UserService.validate_user_data(data)\n            return User.create(data)"

    prompt = get_evaluation_prompt(commit_message, git_diff)

    assert commit_message in prompt
    assert git_diff in prompt
    assert "EVALUATION_CRITERIA" in prompt


def test_get_evaluation_prompt_empty_inputs():
    """Test evaluation prompt with empty inputs."""
    commit_message = ""
    git_diff = ""

    prompt = get_evaluation_prompt(commit_message, git_diff)

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "<COMMIT_MESSAGE>" in prompt
    assert "</COMMIT_MESSAGE>" in prompt
    assert "<GIT_DIFF>" in prompt
    assert "</GIT_DIFF>" in prompt


def test_get_evaluation_prompt_contains_required_sections():
    """Test that evaluation prompt contains all required sections."""
    commit_message = "test: simple commit"
    git_diff = "--- a/test.py\n+++ b/test.py\n@@ -1 +1 @@\n+print('hello')"

    prompt = get_evaluation_prompt(commit_message, git_diff)

    # Check for required sections
    required_sections = [
        "EVALUATION_CRITERIA",
        "WHAT (1-5)",
        "WHY (1-5)",
        "EXAMPLES",
        "CHAIN-OF-THOUGHT EVALUATION",
        "JSON RESPONSE",
    ]

    for section in required_sections:
        assert section in prompt, f"Missing required section: {section}"


def test_get_evaluation_prompt_json_format():
    """Test that evaluation prompt specifies correct JSON format."""
    commit_message = "feat: add feature"
    git_diff = "--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n+code"

    prompt = get_evaluation_prompt(commit_message, git_diff)

    # Check for JSON format specification
    assert '"what_score"' in prompt
    assert '"why_score"' in prompt
    assert '"reasoning"' in prompt
    assert '"confidence"' in prompt
    assert "<1-5>" in prompt


def test_get_commit_prompt_basic():
    """Test basic commit prompt generation without context."""
    diff_content = "--- a/test.py\n+++ b/test.py\n@@ -1,3 +1,4 @@\n def hello():\n-    print('hi')\n+    print('hello')\n"

    prompt = get_commit_prompt(diff_content=diff_content)

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert diff_content in prompt
    assert "conventional commits format" in prompt
    assert "feat:" in prompt
    assert "fix:" in prompt
    assert "refactor:" in prompt


def test_get_commit_prompt_with_file_count():
    """Test commit prompt generation with file count context."""
    diff_content = "--- a/test.py\n+++ b/test.py\n@@ -1,3 +1,4 @@\n def hello():\n-    print('hi')\n+    print('hello')\n"

    prompt = get_commit_prompt(diff_content=diff_content, file_count=1)

    assert "1 file" in prompt
    assert diff_content in prompt


def test_get_commit_prompt_with_multiple_files():
    """Test commit prompt generation with multiple files context."""
    diff_content = "--- a/test.py\n+++ b/test.py\n@@ -1,3 +1,4 @@\n def hello():\n-    print('hi')\n+    print('hello')\n"

    prompt = get_commit_prompt(diff_content=diff_content, file_count=3)

    assert "3 files" in prompt
    assert diff_content in prompt


def test_get_commit_prompt_with_line_changes():
    """Test commit prompt generation with line changes context."""
    diff_content = "--- a/test.py\n+++ b/test.py\n@@ -1,3 +1,4 @@\n def hello():\n-    print('hi')\n+    print('hello')\n"

    prompt = get_commit_prompt(
        diff_content=diff_content, lines_added=5, lines_removed=2
    )

    assert "5 lines added, 2 lines removed" in prompt
    assert diff_content in prompt


def test_get_commit_prompt_with_full_context():
    """Test commit prompt generation with all context parameters."""
    diff_content = "--- a/test.py\n+++ b/test.py\n@@ -1,3 +1,4 @@\n def hello():\n-    print('hi')\n+    print('hello')\n"

    prompt = get_commit_prompt(
        diff_content=diff_content, file_count=2, lines_added=10, lines_removed=3
    )

    assert "2 files, 10 lines added, 3 lines removed" in prompt
    assert diff_content in prompt


def test_get_commit_prompt_empty_diff():
    """Test commit prompt generation with empty diff content."""
    prompt = get_commit_prompt(diff_content="")

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "<git_diff>" in prompt
    assert "</git_diff>" in prompt


def test_get_commit_prompt_contains_instructions():
    """Test that commit prompt contains all required instructions."""
    diff_content = "some diff content"
    prompt = get_commit_prompt(diff_content=diff_content)

    # Check for key instructions
    assert "conventional commits format" in prompt
    assert "Keep the description under 100 characters" in prompt
    assert "imperative mood" in prompt
    assert "WHAT changed and WHY" in prompt
    assert "feat:" in prompt
    assert "fix:" in prompt
    assert "refactor:" in prompt
    assert "docs:" in prompt
    assert "test:" in prompt
    assert "chore:" in prompt


def test_get_commit_prompt_xml_tags():
    """Test that commit prompt properly uses XML tags for diff content."""
    diff_content = "some diff content"
    prompt = get_commit_prompt(diff_content=diff_content)

    assert "<git_diff>" in prompt
    assert "</git_diff>" in prompt
    # Find the content between the tags
    start_tag = "<git_diff>"
    end_tag = "</git_diff>"
    start_idx = prompt.find(start_tag) + len(start_tag)
    end_idx = prompt.find(end_tag)
    content_between_tags = prompt[start_idx:end_idx]
    assert diff_content in content_between_tags
