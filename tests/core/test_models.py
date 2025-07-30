from diffmage.core.models import (
    FileDiff,
    ChangeType,
    FileType,
    CommitAnalysis,
    DiffHunk,
    HunkLine,
)


def test_models_basic_functionality():
    """Test core model creation and properties."""
    # Test FileDiff
    file_diff = FileDiff(
        old_path=None,
        new_path="test.py",
        change_type=ChangeType.ADDED,
        file_type=FileType.SOURCE_CODE,
        is_binary=False,
        lines_added=10,
        lines_removed=0,
        hunks=[],
    )
    assert file_diff.new_path == "test.py"
    assert file_diff.change_type.value == "added"
    assert len(file_diff.hunks) == 0

    # Test CommitAnalysis
    analysis = CommitAnalysis(
        files=[file_diff],
        total_files=1,
        total_lines_added=10,
        total_lines_removed=0,
        branch_name="main",
    )
    assert len(analysis.files) == 1
    assert analysis.total_files == 1


def test_commit_analysis_to_ai_context():
    """Test CommitAnalysis to_ai_context method."""
    file_diff = FileDiff(
        old_path=None,
        new_path="test.py",
        change_type=ChangeType.ADDED,
        file_type=FileType.SOURCE_CODE,
        is_binary=False,
        lines_added=10,
        lines_removed=0,
        hunks=[],
    )

    analysis = CommitAnalysis(
        files=[file_diff],
        total_files=1,
        total_lines_added=10,
        total_lines_removed=0,
        branch_name="main",
    )

    context = analysis.to_ai_context()

    assert "summary" in context
    assert "files" in context
    assert "context" in context

    assert context["summary"]["files_changed"] == 1
    assert context["summary"]["lines_added"] == 10
    assert context["summary"]["lines_removed"] == 0

    assert len(context["files"]) == 1
    assert context["files"][0]["path"] == "test.py"
    assert context["files"][0]["type"] == "source_code"
    assert context["files"][0]["change_type"] == "added"
    assert context["files"][0]["lines_added"] == 10
    assert context["files"][0]["lines_removed"] == 0
    assert context["files"][0]["is_binary"] is False

    assert "repository_context" in context["context"]
    assert "main" in context["context"]["repository_context"]
    assert "timestamp" in context["context"]


def test_commit_analysis_get_combined_diff():
    """Test CommitAnalysis get_combined_diff method."""
    # Test with empty files
    empty_analysis = CommitAnalysis(
        files=[],
        total_files=0,
        total_lines_added=0,
        total_lines_removed=0,
        branch_name="main",
    )
    assert empty_analysis.get_combined_diff() == ""

    # Test with binary file (should be excluded)
    binary_file_diff = FileDiff(
        old_path=None,
        new_path="test.bin",
        change_type=ChangeType.ADDED,
        file_type=FileType.UNKNOWN,
        is_binary=True,
        lines_added=10,
        lines_removed=0,
        hunks=[],
    )

    binary_analysis = CommitAnalysis(
        files=[binary_file_diff],
        total_files=1,
        total_lines_added=10,
        total_lines_removed=0,
        branch_name="main",
    )
    assert binary_analysis.get_combined_diff() == ""

    # Test with non-binary file with hunks
    hunk_line = HunkLine(
        line_type="+",
        is_removed=False,
        is_added=True,
        is_context=False,
        content="def new_function():",
        old_line_number=None,
        new_line_number=1,
    )

    hunk = DiffHunk(
        old_start_line=1,
        old_lines_count=0,
        new_start_line=1,
        new_lines_count=1,
        section_header="",
        lines=[hunk_line],
    )

    non_binary_file_diff = FileDiff(
        old_path=None,
        new_path="test.py",
        change_type=ChangeType.ADDED,
        file_type=FileType.SOURCE_CODE,
        is_binary=False,
        lines_added=1,
        lines_removed=0,
        hunks=[hunk],
    )

    non_binary_analysis = CommitAnalysis(
        files=[non_binary_file_diff],
        total_files=1,
        total_lines_added=1,
        total_lines_removed=0,
        branch_name="main",
    )

    combined_diff = non_binary_analysis.get_combined_diff()
    assert "--- /dev/null" in combined_diff
    assert "+++ test.py" in combined_diff
    assert "@@ -1,0 +1,1 @@" in combined_diff
    assert "+def new_function():" in combined_diff


def test_file_diff_get_ai_context():
    """Test FileDiff get_ai_context method."""
    # Test with empty hunks
    file_diff = FileDiff(
        old_path=None,
        new_path="test.py",
        change_type=ChangeType.ADDED,
        file_type=FileType.SOURCE_CODE,
        is_binary=False,
        lines_added=0,
        lines_removed=0,
        hunks=[],
    )
    assert file_diff.get_ai_context() == ""

    # Test with hunks
    hunk_line = HunkLine(
        line_type="+",
        is_removed=False,
        is_added=True,
        is_context=False,
        content="def new_function():",
        old_line_number=None,
        new_line_number=1,
    )

    hunk = DiffHunk(
        old_start_line=1,
        old_lines_count=0,
        new_start_line=1,
        new_lines_count=1,
        section_header="New function",
        lines=[hunk_line],
    )

    file_diff_with_hunks = FileDiff(
        old_path="old_test.py",
        new_path="new_test.py",
        change_type=ChangeType.MODIFIED,
        file_type=FileType.SOURCE_CODE,
        is_binary=False,
        lines_added=1,
        lines_removed=0,
        hunks=[hunk],
    )

    context = file_diff_with_hunks.get_ai_context()
    assert "--- old_test.py" in context
    assert "+++ new_test.py" in context
    assert "@@ -1,0 +1,1 @@ New function" in context
    assert "+def new_function():" in context


def test_file_diff_content_properties():
    """Test FileDiff content extraction properties."""
    # Create test hunks with different line types
    added_line = HunkLine(
        line_type="+",
        is_removed=False,
        is_added=True,
        is_context=False,
        content="def new_function():",
        old_line_number=None,
        new_line_number=1,
    )

    removed_line = HunkLine(
        line_type="-",
        is_removed=True,
        is_added=False,
        is_context=False,
        content="def old_function():",
        old_line_number=1,
        new_line_number=None,
    )

    context_line = HunkLine(
        line_type=" ",
        is_removed=False,
        is_added=False,
        is_context=True,
        content="",
        old_line_number=2,
        new_line_number=2,
    )

    hunk = DiffHunk(
        old_start_line=1,
        old_lines_count=2,
        new_start_line=1,
        new_lines_count=2,
        section_header="",
        lines=[added_line, removed_line, context_line],
    )

    file_diff = FileDiff(
        old_path=None,
        new_path="test.py",
        change_type=ChangeType.MODIFIED,
        file_type=FileType.SOURCE_CODE,
        is_binary=False,
        lines_added=1,
        lines_removed=1,
        hunks=[hunk],
    )

    # Test hunk properties
    assert hunk.added_lines == ["def new_function():"]
    assert hunk.removed_lines == ["def old_function():"]
    assert hunk.context_lines == [""]

    # Test file diff properties
    assert file_diff.all_added_content == "def new_function():"
    assert file_diff.all_removed_content == "def old_function():"


def test_diff_hunk_properties():
    """Test DiffHunk properties and methods."""
    # Test empty hunk
    empty_hunk = DiffHunk(
        old_start_line=1,
        old_lines_count=0,
        new_start_line=1,
        new_lines_count=0,
        section_header="",
        lines=[],
    )
    assert empty_hunk.added_lines == []
    assert empty_hunk.removed_lines == []
    assert empty_hunk.context_lines == []

    # Test hunk with mixed lines
    lines = [
        HunkLine(
            line_type="+",
            is_removed=False,
            is_added=True,
            is_context=False,
            content="new line",
            old_line_number=None,
            new_line_number=1,
        ),
        HunkLine(
            line_type="-",
            is_removed=True,
            is_added=False,
            is_context=False,
            content="old line",
            old_line_number=1,
            new_line_number=None,
        ),
        HunkLine(
            line_type=" ",
            is_removed=False,
            is_added=False,
            is_context=True,
            content="context",
            old_line_number=2,
            new_line_number=2,
        ),
    ]

    mixed_hunk = DiffHunk(
        old_start_line=1,
        old_lines_count=2,
        new_start_line=1,
        new_lines_count=2,
        section_header="Test section",
        lines=lines,
    )
    assert mixed_hunk.added_lines == ["new line"]
    assert mixed_hunk.removed_lines == ["old line"]
    assert mixed_hunk.context_lines == ["context"]


def test_hunk_line_creation():
    """Test HunkLine creation and properties."""
    # Test added line
    added_line = HunkLine(
        line_type="+",
        is_removed=False,
        is_added=True,
        is_context=False,
        content="new content",
        old_line_number=None,
        new_line_number=1,
    )
    assert added_line.line_type == "+"
    assert added_line.is_removed is False
    assert added_line.is_added is True
    assert added_line.is_context is False
    assert added_line.content == "new content"
    assert added_line.old_line_number is None
    assert added_line.new_line_number == 1

    # Test removed line
    removed_line = HunkLine(
        line_type="-",
        is_removed=True,
        is_added=False,
        is_context=False,
        content="old content",
        old_line_number=1,
        new_line_number=None,
    )
    assert removed_line.line_type == "-"
    assert removed_line.is_removed is True
    assert removed_line.is_added is False
    assert removed_line.is_context is False
    assert removed_line.content == "old content"
    assert removed_line.old_line_number == 1
    assert removed_line.new_line_number is None

    # Test context line
    context_line = HunkLine(
        line_type=" ",
        is_removed=False,
        is_added=False,
        is_context=True,
        content="context content",
        old_line_number=2,
        new_line_number=2,
    )
    assert context_line.line_type == " "
    assert context_line.is_removed is False
    assert context_line.is_added is False
    assert context_line.is_context is True
    assert context_line.content == "context content"
    assert context_line.old_line_number == 2
    assert context_line.new_line_number == 2
