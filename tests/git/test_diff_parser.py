import pytest
from unittest.mock import Mock
from diffmage.git.diff_parser import GitDiffParser
from diffmage.core.models import ChangeType, FileType, FileDiff, CommitAnalysis
import git
from unidiff.errors import UnidiffParseError


@pytest.fixture
def parser():
    """Create a GitDiffParser instance for testing."""
    return GitDiffParser()


@pytest.fixture
def mock_repo():
    """Create a mock git repo for testing."""
    return Mock()


@pytest.fixture
def sample_file_diff():
    """Create a sample FileDiff object for testing."""
    return FileDiff(
        old_path="src/main.py",
        new_path="src/main.py",
        change_type=ChangeType.MODIFIED,
        file_type=FileType.SOURCE_CODE,
        is_binary=False,
        lines_added=1,
        lines_removed=0,
    )


def test_detect_file_type_source_code(parser):
    """Test detection of source code files"""

    # Python files
    assert parser._detect_file_type("src/main.py") == FileType.SOURCE_CODE
    assert parser._detect_file_type("app.py") == FileType.SOURCE_CODE

    # JavaScript files
    assert parser._detect_file_type("src/app.js") == FileType.SOURCE_CODE
    assert parser._detect_file_type("index.jsx") == FileType.SOURCE_CODE

    # TypeScript files
    assert parser._detect_file_type("src/app.ts") == FileType.SOURCE_CODE
    assert parser._detect_file_type("component.tsx") == FileType.SOURCE_CODE


def test_detect_file_type_test_files(parser):
    """Test detection of test files"""

    # Test files in test directories
    assert parser._detect_file_type("tests/test_main.py") == FileType.TEST_CODE
    assert parser._detect_file_type("test/unit_test.js") == FileType.TEST_CODE

    # Test files with test naming patterns
    assert parser._detect_file_type("src/test_main.py") == FileType.TEST_CODE
    assert parser._detect_file_type("src/main_test.py") == FileType.TEST_CODE
    assert parser._detect_file_type("src/main_spec.py") == FileType.TEST_CODE

    # Files with test in the middle of the name
    assert (
        parser._detect_file_type("src/integration_test_helper.py") == FileType.TEST_CODE
    )


def test_detect_file_type_config_files(parser):
    """Test detection of configuration files"""

    # YAML files
    assert parser._detect_file_type(".github/workflows/ci.yml") == FileType.CONFIG
    assert parser._detect_file_type("config.yaml") == FileType.CONFIG

    # JSON files
    assert parser._detect_file_type("package.json") == FileType.CONFIG
    assert parser._detect_file_type("tsconfig.json") == FileType.CONFIG

    # TOML files
    assert parser._detect_file_type("pyproject.toml") == FileType.CONFIG
    assert parser._detect_file_type("Cargo.toml") == FileType.CONFIG

    # Environment files
    assert parser._detect_file_type(".env") == FileType.CONFIG
    assert parser._detect_file_type(".env.local") == FileType.CONFIG

    # Docker files
    assert parser._detect_file_type("Dockerfile") == FileType.CONFIG
    assert parser._detect_file_type("docker-compose.yml") == FileType.CONFIG


def test_detect_file_type_documentation(parser):
    """Test detection of documentation files"""

    # Markdown files
    assert parser._detect_file_type("README.md") == FileType.DOCUMENTATION
    assert parser._detect_file_type("docs/guide.md") == FileType.DOCUMENTATION

    # Text files
    assert parser._detect_file_type("LICENSE.txt") == FileType.DOCUMENTATION
    assert parser._detect_file_type("notes.txt") == FileType.DOCUMENTATION

    # Binary documentation files
    assert parser._detect_file_type("document.pdf") == FileType.DOCUMENTATION
    assert parser._detect_file_type("presentation.pptx") == FileType.DOCUMENTATION


def test_detect_file_type_unknown(parser):
    """Test detection of unknown file types"""

    # Files with unknown extensions
    assert parser._detect_file_type("data.dat") == FileType.UNKNOWN
    assert parser._detect_file_type("temp.tmp") == FileType.UNKNOWN

    # Files without extensions
    assert parser._detect_file_type("LICENSE") == FileType.UNKNOWN
    assert parser._detect_file_type("Makefile") == FileType.UNKNOWN


def test_detect_file_type_edge_cases(parser):
    """Test edge cases in file type detection"""

    # File with "test" in name but not a test file
    # This should be classified as source code, not test code
    assert parser._detect_file_type("src/latest.py") == FileType.SOURCE_CODE
    assert parser._detect_file_type("src/contest.js") == FileType.SOURCE_CODE
    assert parser._detect_file_type("src/__tests__/main.py") == FileType.TEST_CODE
    assert parser._detect_file_type("src/file.test.py") == FileType.TEST_CODE


def test_convert_patched_file_added_file():
    """Test converting a PatchedFile representing an added file"""
    from unittest.mock import Mock

    parser = GitDiffParser()

    mock_patched_file = Mock()
    mock_patched_file.is_rename = False
    mock_patched_file.is_added_file = True
    mock_patched_file.is_removed_file = False
    mock_patched_file.path = "src/new_file.py"
    mock_patched_file.source_file = "/dev/null"
    mock_patched_file.target_file = "src/new_file.py"
    mock_patched_file.is_binary_file = False
    mock_patched_file.added = 10
    mock_patched_file.removed = 0

    parser._detect_file_type = Mock(return_value=FileType.SOURCE_CODE)

    file_diff = parser._convert_patched_file(mock_patched_file)

    assert file_diff is not None
    assert file_diff.old_path is None
    assert file_diff.new_path == "src/new_file.py"
    assert file_diff.change_type == ChangeType.ADDED
    assert file_diff.file_type == FileType.SOURCE_CODE
    assert file_diff.is_binary is False
    assert file_diff.lines_added == 10
    assert file_diff.lines_removed == 0


def test_convert_patched_file_modified_file():
    """Test converting a PatchedFile representing a modified file"""
    from unittest.mock import Mock

    parser = GitDiffParser()

    mock_patched_file = Mock()
    mock_patched_file.is_rename = False
    mock_patched_file.is_added_file = False
    mock_patched_file.is_removed_file = False
    mock_patched_file.path = "src/existing_file.py"
    mock_patched_file.source_file = "src/existing_file.py"
    mock_patched_file.target_file = "src/existing_file.py"
    mock_patched_file.is_binary_file = False
    mock_patched_file.added = 5
    mock_patched_file.removed = 3

    parser._detect_file_type = Mock(return_value=FileType.SOURCE_CODE)

    file_diff = parser._convert_patched_file(mock_patched_file)

    assert file_diff is not None
    assert file_diff.old_path == "src/existing_file.py"
    assert file_diff.new_path == "src/existing_file.py"
    assert file_diff.change_type == ChangeType.MODIFIED
    assert file_diff.file_type == FileType.SOURCE_CODE
    assert file_diff.is_binary is False
    assert file_diff.lines_added == 5
    assert file_diff.lines_removed == 3


def test_convert_patched_file_deleted_file():
    """Test converting a PatchedFile representing a deleted file"""
    from unittest.mock import Mock

    parser = GitDiffParser()

    mock_patched_file = Mock()
    mock_patched_file.is_rename = False
    mock_patched_file.is_added_file = False
    mock_patched_file.is_removed_file = True
    mock_patched_file.path = "src/deleted_file.py"
    mock_patched_file.source_file = "src/deleted_file.py"
    mock_patched_file.target_file = "/dev/null"
    mock_patched_file.is_binary_file = False
    mock_patched_file.added = 0
    mock_patched_file.removed = 8

    parser._detect_file_type = Mock(return_value=FileType.SOURCE_CODE)

    file_diff = parser._convert_patched_file(mock_patched_file)

    assert file_diff is not None
    assert file_diff.old_path == "src/deleted_file.py"
    assert file_diff.new_path is None
    assert file_diff.change_type == ChangeType.DELETED
    assert file_diff.file_type == FileType.SOURCE_CODE
    assert file_diff.is_binary is False
    assert file_diff.lines_added == 0
    assert file_diff.lines_removed == 8


def test_convert_patched_file_renamed_file():
    """Test converting a PatchedFile representing a renamed file"""
    from unittest.mock import Mock

    parser = GitDiffParser()

    mock_patched_file = Mock()
    mock_patched_file.is_rename = True
    mock_patched_file.is_added_file = False
    mock_patched_file.is_removed_file = False
    mock_patched_file.path = "src/new_name.py"
    mock_patched_file.source_file = "src/old_name.py"
    mock_patched_file.target_file = "src/new_name.py"
    mock_patched_file.is_binary_file = False
    mock_patched_file.added = 2
    mock_patched_file.removed = 1

    parser._detect_file_type = Mock(return_value=FileType.SOURCE_CODE)

    file_diff = parser._convert_patched_file(mock_patched_file)

    assert file_diff is not None
    assert file_diff.old_path == "src/old_name.py"
    assert file_diff.new_path == "src/new_name.py"
    assert file_diff.change_type == ChangeType.RENAMED
    assert file_diff.file_type == FileType.SOURCE_CODE
    assert file_diff.is_binary is False
    assert file_diff.lines_added == 2
    assert file_diff.lines_removed == 1


def test_convert_patched_file_exception_handling():
    """Test that exceptions in _convert_patched_file are handled gracefully"""
    from unittest.mock import Mock

    parser = GitDiffParser()

    mock_patched_file = Mock()
    mock_patched_file.path = "src/file.py"
    type(mock_patched_file).is_rename = Mock(side_effect=Exception("Test exception"))

    file_diff = parser._convert_patched_file(mock_patched_file)

    assert file_diff is None


def test_parse_staged_changes_normal_operation(parser, mock_repo, sample_file_diff):
    """Test parse_staged_changes with normal operation"""

    mock_repo.git.diff.return_value = """diff --git a/src/main.py b/src/main.py
    index 1234567..89abcde 100644
    --- a/src/main.py
    +++ b/src/main.py
    @@ -1,1 +1,2 @@
    def main():
    +    print("Hello, world!")
    """

    mock_repo.active_branch.name = "main"
    parser.repo = mock_repo

    parser._convert_patched_file = Mock(return_value=sample_file_diff)

    result = parser.parse_staged_changes()

    assert isinstance(result, CommitAnalysis)
    assert result.total_files == 1
    assert result.total_lines_added == 1
    assert result.total_lines_removed == 0
    assert result.branch_name == "main"
    assert len(result.files) == 1
    assert result.files[0].lines_added == 1
    assert result.files[0].lines_removed == 0


def test_parse_staged_changes_git_command_error():
    """Test parse_staged_changes when git command fails"""
    from unittest.mock import Mock
    import pytest

    parser = GitDiffParser()

    mock_repo = Mock()
    mock_repo.git.diff.side_effect = git.exc.GitCommandError(
        "git diff", "Git command failed"
    )
    parser.repo = mock_repo

    with pytest.raises(ValueError, match="Failed to get staged changes from git"):
        parser.parse_staged_changes()


def test_parse_staged_changes_no_staged_changes():
    """Test parse_staged_changes when no staged changes are found"""
    from unittest.mock import Mock
    import pytest

    parser = GitDiffParser()

    mock_repo = Mock()
    mock_repo.git.diff.return_value = ""
    mock_repo.active_branch.name = "main"
    parser.repo = mock_repo

    with pytest.raises(ValueError, match="No staged changes found"):
        parser.parse_staged_changes()


def test_parse_staged_changes_diff_parsing_error():
    """Test parse_staged_changes when diff parsing fails"""
    from unittest.mock import Mock
    import pytest

    parser = GitDiffParser()

    mock_repo = Mock()
    mock_repo.git.diff.return_value = "some text that will cause parsing to fail"
    mock_repo.active_branch.name = "main"
    parser.repo = mock_repo

    with pytest.MonkeyPatch().context() as m:
        m.setattr(
            "diffmage.git.diff_parser.PatchSet",
            Mock(side_effect=UnidiffParseError("Parse error")),
        )

        with pytest.raises(ValueError, match="Failed to parse staged changes"):
            parser.parse_staged_changes()


def test_parse_staged_changes_empty_file_list(parser, mock_repo):
    """Test parse_staged_changes when _convert_patched_file returns None for all files"""

    mock_repo.git.diff.return_value = """diff --git a/src/main.py b/src/main.py
    index 1234567..89abcde 100644
    --- a/src/main.py
    +++ b/src/main.py
    @@ -1,1 +1,2 @@
    def main():
    +    print("Hello, world!")
    """
    mock_repo.active_branch.name = "main"
    parser.repo = mock_repo

    parser._convert_patched_file = Mock(return_value=None)

    result = parser.parse_staged_changes()

    assert isinstance(result, CommitAnalysis)
    assert result.total_files == 0
    assert result.total_lines_added == 0
    assert result.total_lines_removed == 0
    assert result.branch_name == "main"
    assert len(result.files) == 0
