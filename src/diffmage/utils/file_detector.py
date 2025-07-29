from pathlib import Path
from diffmage.core.models import FileType


class FileDetector:
    """Detects file types based on path, extension, and content patterns"""

    def __init__(self) -> None:
        pass

    def detect_file_type(self, file_path: str) -> FileType:
        """Detect file type with clear delegation to specialized methods."""
        path = Path(file_path)

        # Test files
        if self._is_test_file(path):
            return FileType.TEST_CODE

        # Configuration files
        if self._is_config_file(path):
            return FileType.CONFIG

        # Source code
        if self._is_source_code_file(path):
            return FileType.SOURCE_CODE

        # Documentation
        if self._is_documentation_file(path):
            return FileType.DOCUMENTATION

        # Binary docs
        if self._is_binary_file(path):
            return FileType.DOCUMENTATION

        return FileType.UNKNOWN

    def _is_test_file(self, path: Path) -> bool:
        """Check if a file is a test file based on path and name patterns"""
        name = path.name.lower()
        parts = path.parts

        return (
            any(part in ["test", "tests", "__tests__"] for part in parts)
            or name.startswith("test_")
            or name.endswith("_test")
            or name.endswith("_spec")
            or "_test." in name
            or "_test_" in name
            or ".test." in name
            or "_spec." in name
            or "_spec_" in name
            or ".spec." in name
        )

    def _is_config_file(self, path: Path) -> bool:
        """Check if a file is a configuration file based on path and name patterns"""
        ext = path.suffix.lower()
        name = path.name.lower()

        return ext in {
            ".yml",
            ".yaml",
            ".json",
            ".toml",
            ".ini",
            ".conf",
        } or name in {
            "dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            ".dockerignore",
            ".dockerfile",
            ".env",
            ".env.local",
        }

    def _is_source_code_file(self, path: Path) -> bool:
        """Check if a file is a source code file based on path and name patterns"""
        ext = path.suffix.lower()

        return ext in {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".rb",
            ".erb",
            ".go",
            ".rs",
            ".php",
            ".cs",
            ".swift",
        }

    def _is_documentation_file(self, path: Path) -> bool:
        """Check if a file is a documentation file based on path and name patterns"""
        ext = path.suffix.lower()

        return ext in {".md", ".txt", ".rst", ".tex"}

    def _is_binary_file(self, path: Path) -> bool:
        """Check if a file is a binary file based on path and name patterns"""
        ext = path.suffix.lower()

        return ext in {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}
