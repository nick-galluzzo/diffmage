from diffmage.git.diff_parser import GitDiffParser
from diffmage.core.models import FileType


def test_detect_file_type_source_code():
    """Test detection of source code files"""
    parser = GitDiffParser()

    # Python files
    assert parser._detect_file_type("src/main.py") == FileType.SOURCE_CODE
    assert parser._detect_file_type("app.py") == FileType.SOURCE_CODE

    # JavaScript files
    assert parser._detect_file_type("src/app.js") == FileType.SOURCE_CODE
    assert parser._detect_file_type("index.jsx") == FileType.SOURCE_CODE

    # TypeScript files
    assert parser._detect_file_type("src/app.ts") == FileType.SOURCE_CODE
    assert parser._detect_file_type("component.tsx") == FileType.SOURCE_CODE


def test_detect_file_type_test_files():
    """Test detection of test files"""
    parser = GitDiffParser()

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


def test_detect_file_type_config_files():
    """Test detection of configuration files"""
    parser = GitDiffParser()

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


def test_detect_file_type_documentation():
    """Test detection of documentation files"""
    parser = GitDiffParser()

    # Markdown files
    assert parser._detect_file_type("README.md") == FileType.DOCUMENTATION
    assert parser._detect_file_type("docs/guide.md") == FileType.DOCUMENTATION

    # Text files
    assert parser._detect_file_type("LICENSE.txt") == FileType.DOCUMENTATION
    assert parser._detect_file_type("notes.txt") == FileType.DOCUMENTATION

    # Binary documentation files
    assert parser._detect_file_type("document.pdf") == FileType.DOCUMENTATION
    assert parser._detect_file_type("presentation.pptx") == FileType.DOCUMENTATION


def test_detect_file_type_unknown():
    """Test detection of unknown file types"""
    parser = GitDiffParser()

    # Files with unknown extensions
    assert parser._detect_file_type("data.dat") == FileType.UNKNOWN
    assert parser._detect_file_type("temp.tmp") == FileType.UNKNOWN

    # Files without extensions
    assert parser._detect_file_type("LICENSE") == FileType.UNKNOWN
    assert parser._detect_file_type("Makefile") == FileType.UNKNOWN


def test_detect_file_type_edge_cases():
    """Test edge cases in file type detection"""
    parser = GitDiffParser()

    # File with "test" in name but not a test file
    # This should be classified as source code, not test code
    assert parser._detect_file_type("src/latest.py") == FileType.SOURCE_CODE
    assert parser._detect_file_type("src/contest.js") == FileType.SOURCE_CODE

    # File in __tests__ directory
    assert parser._detect_file_type("src/__tests__/main.py") == FileType.TEST_CODE

    # File with multiple dots
    assert parser._detect_file_type("src/file.test.py") == FileType.TEST_CODE
