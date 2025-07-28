from pydantic import BaseModel
from typing import Optional
from enum import Enum


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


class FileDiff(BaseModel):
    """Represents changes to a single file in a git commit"""

    old_path: Optional[str]
    new_path: Optional[str]
    change_type: ChangeType
    file_type: FileType
    is_binary: bool
    lines_added: int
    lines_removed: int


class CommitAnalysis(BaseModel):
    """Analysis of git commit changes for AI processing"""

    files: list[FileDiff]
    total_files: int
    total_lines_added: int
    total_lines_removed: int
    branch_name: str
