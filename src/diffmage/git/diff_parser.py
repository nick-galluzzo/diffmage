from typing import Optional
from pathlib import Path
import git
from unidiff import PatchSet, PatchedFile
from diffmage.core.models import CommitAnalysis, FileDiff, ChangeType, FileType


class GitDiffParser:
    """Parser using git diff to extract and parse file diffs"""

    def __init__(self, repo_path: str = "."):
        self.repo = git.Repo(repo_path)

    def parse_staged_changes(self) -> CommitAnalysis:
        """Parse staged changes from git using the unidiff library"""

        try:
            diff_text = self.repo.git.diff("--cached", "--no-color")
        except git.exc.GitCommandError:
            raise ValueError("Failed to get staged changes from git")

        if not diff_text.strip():
            raise ValueError("No staged changes found")

        try:
            patch_set = PatchSet(diff_text)
        except Exception:
            raise ValueError("Failed to parse staged changes")

        files = []
        total_lines_added = 0
        total_lines_removed = 0

        for patched_file in patch_set:
            file_diff = self._convert_patched_file(patched_file)
            if file_diff:
                files.append(file_diff)
                total_lines_added += file_diff.lines_added
                total_lines_removed += file_diff.lines_removed

        return CommitAnalysis(
            files=files,
            total_files=len(files),
            total_lines_added=total_lines_added,
            total_lines_removed=total_lines_removed,
            branch_name=self.repo.active_branch.name,
        )

    def _convert_patched_file(self, patched_file: PatchedFile) -> Optional[FileDiff]:
        """Convert a unidiff PatchedFile to a FileDiff object"""

        try:
            # Determine the change type
            # For files that are both renamed and modified,
            # we prioritize RENAMED since that's the structural change.
            if patched_file.is_rename:
                change_type = ChangeType.RENAMED
            elif patched_file.is_added_file:
                change_type = ChangeType.ADDED
            elif patched_file.is_removed_file:
                change_type = ChangeType.DELETED
            else:
                change_type = ChangeType.MODIFIED

            # Determine the file type
            file_type = self._detect_file_type(patched_file.path)

            return FileDiff(
                old_path=patched_file.source_file
                if patched_file.source_file != "/dev/null"
                else None,
                new_path=patched_file.target_file
                if patched_file.target_file != "/dev/null"
                else None,
                change_type=change_type,
                file_type=file_type,
                is_binary=patched_file.is_binary_file,
                lines_added=patched_file.added,
                lines_removed=patched_file.removed,
            )
        except Exception:
            # If we can't convert the file, return None to skip it
            return None

    def _detect_file_type(self, file_path: str) -> FileType:
        """Detect file type with early returns for clarity."""

        path = Path(file_path)
        ext = path.suffix.lower()
        name = path.name.lower()
        parts = path.parts

        # Test files
        is_test_file = (
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

        if is_test_file and ext in {".py", ".js", ".ts", ".java", ".cpp", ".rb", ".go"}:
            return FileType.TEST_CODE

        # Configuration files
        if ext in {
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
        }:
            return FileType.CONFIG

        # Source code
        if ext in {
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
        }:
            return FileType.SOURCE_CODE

        # Documentation
        if ext in {".md", ".txt", ".rst", ".tex"}:
            return FileType.DOCUMENTATION

        # Binary docs
        if ext in {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}:
            return FileType.DOCUMENTATION

        return FileType.UNKNOWN
