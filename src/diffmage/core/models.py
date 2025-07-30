from typing import Dict, Any
from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime


class ChangeType(str, Enum):
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    RENAMED = "renamed"


class FileType(str, Enum):
    SOURCE_CODE = "source_code"
    TEST_CODE = "test_code"
    DOCUMENTATION = "documentation"
    CONFIG = "config"
    UNKNOWN = "unknown"


class HunkLine(BaseModel):
    """Represents a line in a hunk"""

    line_type: str
    is_removed: bool
    is_added: bool
    is_context: bool
    content: str
    old_line_number: Optional[int]
    new_line_number: Optional[int]


class DiffHunk(BaseModel):
    """Represents a hunk in a diff"""

    old_start_line: int
    old_lines_count: int
    new_start_line: int
    new_lines_count: int
    section_header: str
    lines: list[HunkLine]

    @property
    def added_lines(self) -> list[str]:
        """Get only the added lines content of the hunk"""
        return [line.content for line in self.lines if line.is_added]

    @property
    def removed_lines(self) -> list[str]:
        """Get only the removed lines content of the hunk"""
        return [line.content for line in self.lines if line.is_removed]

    @property
    def context_lines(self) -> list[str]:
        """Get only the context lines (unchanged) of the hunk"""
        return [line.content for line in self.lines if line.is_context]


class FileDiff(BaseModel):
    """Represents changes to a single file in a git commit"""

    old_path: Optional[str]
    new_path: Optional[str]
    change_type: ChangeType
    file_type: FileType
    is_binary: bool
    lines_added: int
    lines_removed: int
    hunks: list[DiffHunk]

    @property
    def all_added_content(self) -> str:
        """Get all added content across all hunks"""
        lines = []
        for hunk in self.hunks:
            lines.extend(hunk.added_lines)
        return "\n".join(lines)

    @property
    def all_removed_content(self) -> str:
        """Get all removed content across all hunks"""
        lines = []
        for hunk in self.hunks:
            lines.extend(hunk.removed_lines)
        return "\n".join(lines)

    @property
    def get_ai_context(self) -> str:
        """Get context format for AI commit message generation

        Returns minimal git diff format focused on actual changes,
        not git plubming metadata.
        """

        if not self.hunks:
            return ""

        lines = []

        # Essential file info - what actually changed
        old_path = self.old_path or "/dev/null"
        new_path = self.new_path or "/dev/null"
        lines.extend(
            [
                f"--- {old_path}",
                f"+++ {new_path}",
            ]
        )

        # Diff content
        for hunk in self.hunks:
            # Hunk header with line numbers
            header = f"@@ -{hunk.old_start_line},{hunk.old_lines_count} +{hunk.new_start_line},{hunk.new_lines_count} @@"
            if hunk.section_header:
                header += f" {hunk.section_header}"
            lines.append(header)

            # Context, Removed, and Added lines
            for line in hunk.lines:
                lines.append(f"{line.line_type}{line.content}")

        return "\n".join(lines)


class CommitAnalysis(BaseModel):
    """Analysis of git commit changes for AI processing"""

    files: list[FileDiff]
    total_files: int
    total_lines_added: int
    total_lines_removed: int
    branch_name: str

    def to_ai_context(self) -> Dict[str, Any]:
        """Export structured data for AI processing"""
        return {
            "summary": {
                "files_changed": self.total_files,
                "lines_added": self.total_lines_added,
                "lines_removed": self.total_lines_removed,
            },
            "files": [
                {
                    "path": file_diff.new_path,
                    "type": file_diff.file_type.value,
                    "change_type": file_diff.change_type.value,
                    "lines_added": file_diff.lines_added,
                    "lines_removed": file_diff.lines_removed,
                    "is_binary": file_diff.is_binary,
                }
                for file_diff in self.files
            ],
            "context": {
                # TODO: Add more context about the repository
                "repository_context": f"Git repository analysis for branch {self.branch_name}",
                "timestamp": datetime.now().isoformat(),
            },
        }
