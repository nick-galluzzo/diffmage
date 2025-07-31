from typing import Optional
import git
from diffmage.utils.file_detector import FileDetector
from unidiff import PatchSet, PatchedFile, Hunk
from diffmage.core.models import (
    CommitAnalysis,
    FileDiff,
    ChangeType,
    HunkLine,
    DiffHunk,
)


class GitDiffParser:
    """Parser using git diff to extract and parse file diffs"""

    def __init__(self, repo_path: str = "."):
        self.repo = git.Repo(repo_path)
        self.file_detector = FileDetector()

    def parse_staged_changes(self) -> CommitAnalysis:
        """Parse staged changes from git using the unidiff library"""

        try:
            diff_text = self.repo.git.diff("--cached", "--no-color")
        except git.GitCommandError:
            raise ValueError("Failed to get staged changes from git")

        analysis = self._parse_diff_text(diff_text, "staged changes")

        return analysis

    def parse_specific_commit(self, commit_hash: str) -> tuple[CommitAnalysis, str]:
        """
        Parse specific commit from git history.

        Args:
            commit_hash: Git commit hash (e.g., "HEAD", "abc123", "HEAD~1")

        Returns:
            Tuple of (CommitAnalysis, commit_message)

        Raises:
            ValueError: If commit doesn't exist or has no changes
        """
        try:
            commit = self.repo.commit(commit_hash)
            commit_message = str(commit.message).strip()

        except git.BadName:
            raise ValueError(f"Invalid commit hash: {commit_hash}")
        except git.GitCommandError as e:
            raise ValueError(f"Failed to get commit diff: {e}")

        diff_text = self._get_commit_diff_text(commit_hash, commit)

        analysis = self._parse_diff_text(diff_text, f"commit {commit_hash}")

        return analysis, commit_message

    def _get_commit_diff_text(self, commit_hash: str, commit) -> str:
        """Get diff text for a specific commit"""
        try:
            # Get diff between previous commit and specified commit
            return self.repo.git.diff(f"{commit_hash}~1", commit_hash, "--no-color")
        except git.GitCommandError:
            # Probably initial commit - compare to empty tree
            if len(commit.parents) == 0:
                return self.repo.git.diff(
                    "4b825dc642cb6eb9a060e54bf8d69288fbee4904",
                    commit_hash,
                    "--no-color",
                )
            else:
                raise

    def _parse_diff_text(
        self, diff_text: str, source_description: str
    ) -> CommitAnalysis:
        """
        Parse git diff text into CommitAnalysis object.

        Args:
            diff_text: Raw git diff output
            source_description: Description for error messages (e.g., "staged changes", "commit abc123")
        """
        if not diff_text.strip():
            raise ValueError(f"No changes found in {source_description}")

        try:
            patch_set = PatchSet(diff_text)
        except Exception as e:
            raise ValueError(f"Failed to parse {source_description}: {e}")

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
            change_type = self._determine_change_type(patched_file)
            file_type = self.file_detector.detect_file_type(patched_file.path)

            hunks = []
            if not patched_file.is_binary_file:
                for hunk in patched_file:
                    diff_hunk = self._convert_hunk(hunk)
                    if diff_hunk:
                        hunks.append(diff_hunk)

            return FileDiff(
                old_path=(
                    patched_file.source_file
                    if patched_file.source_file != "/dev/null"
                    else None
                ),
                new_path=(
                    patched_file.target_file
                    if patched_file.target_file != "/dev/null"
                    else None
                ),
                change_type=change_type,
                file_type=file_type,
                is_binary=patched_file.is_binary_file,
                lines_added=patched_file.added,
                lines_removed=patched_file.removed,
                hunks=hunks,
            )
        except Exception:
            # Skip files that we can't convert
            return None

    def _determine_change_type(self, patched_file: PatchedFile) -> ChangeType:
        """Detect the change type of a patched file"""
        # For files that are both renamed and modified,
        # we prioritize RENAMED since that's the structural change.
        if patched_file.is_rename:
            return ChangeType.RENAMED
        if patched_file.is_added_file:
            return ChangeType.ADDED
        if patched_file.is_removed_file:
            return ChangeType.DELETED
        return ChangeType.MODIFIED

    def _convert_hunk(self, hunk: Hunk) -> Optional[DiffHunk]:
        """Convert a unidiff Hunk to a DiffHunk object with line by line content"""
        try:
            lines = []

            for line in hunk:
                hunk_line = HunkLine(
                    line_type=line.line_type,  # '+', '-', or ' '
                    is_removed=line.is_removed,
                    is_added=line.is_added,
                    is_context=line.is_context,  # True if line is not a change
                    content=line.value.rstrip("\n"),  # Remove trailing newline
                    old_line_number=line.source_line_no
                    if line.source_line_no
                    else None,
                    new_line_number=line.target_line_no
                    if line.target_line_no
                    else None,
                )
                lines.append(hunk_line)

            return DiffHunk(
                old_start_line=hunk.source_start,
                old_lines_count=hunk.source_length,
                new_start_line=hunk.target_start,
                new_lines_count=hunk.target_length,
                section_header=hunk.section_header,
                lines=lines,
            )
        except Exception:
            return None
