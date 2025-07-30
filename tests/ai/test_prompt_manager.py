from diffmage.ai.prompt_manager import get_commit_prompt, get_system_prompt


def test_get_system_prompt():
    """Test that system prompt is properly formatted and contains expected content."""
    system_prompt = get_system_prompt()

    assert isinstance(system_prompt, str)
    assert len(system_prompt) > 0
    assert "commit messages" in system_prompt.lower()
    assert "descriptive" in system_prompt.lower()
    assert "imperative mood" in system_prompt.lower()


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
