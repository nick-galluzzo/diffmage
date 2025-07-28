"""
Test script demonstrating usage of the core models with dummy data.
This script can be run to verify model functionality and serialization.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.diffmage.core.models import ChangeType, FileType, FileDiff, CommitAnalysis


def create_dummy_file_diffs() -> list[FileDiff]:
    """Create a list of dummy FileDiff objects for testing."""
    return [
        FileDiff(
            old_path="src/old_file.py",
            new_path="src/new_file.py",
            change_type=ChangeType.MODIFIED,
            file_type=FileType.SOURCE_CODE,
            is_binary=False,
            lines_added=15,
            lines_removed=5,
        ),
        FileDiff(
            old_path=None,
            new_path="tests/new_test.py",
            change_type=ChangeType.ADDED,
            file_type=FileType.TEST_CODE,
            is_binary=False,
            lines_added=50,
            lines_removed=0,
        ),
        FileDiff(
            old_path="deprecated.py",
            new_path=None,
            change_type=ChangeType.DELETED,
            file_type=FileType.SOURCE_CODE,
            is_binary=False,
            lines_added=0,
            lines_removed=30,
        ),
        FileDiff(
            old_path="src/old_name.py",
            new_path="src/new_name.py",
            change_type=ChangeType.RENAMED,
            file_type=FileType.SOURCE_CODE,
            is_binary=False,
            lines_added=2,
            lines_removed=2,
        ),
        FileDiff(
            old_path="assets/image.png",
            new_path="assets/image.png",
            change_type=ChangeType.MODIFIED,
            file_type=FileType.UNKNOWN,
            is_binary=True,
            lines_added=0,
            lines_removed=0,
        ),
    ]


def create_dummy_commit_analysis() -> CommitAnalysis:
    """Create a dummy CommitAnalysis object for testing."""
    file_diffs = create_dummy_file_diffs()

    return CommitAnalysis(
        files=file_diffs,
        total_files=len(file_diffs),
        total_lines_added=sum(f.lines_added for f in file_diffs),
        total_lines_removed=sum(f.lines_removed for f in file_diffs),
        branch_name="feature/test-branch",
    )


def main():
    """Main function to demonstrate model usage."""
    print("Creating dummy data for models...")

    # Create dummy data
    commit_analysis = create_dummy_commit_analysis()

    # Demonstrate model functionality
    print(f"Created CommitAnalysis with {commit_analysis.total_files} files")
    print(f"Total lines added: {commit_analysis.total_lines_added}")
    print(f"Total lines removed: {commit_analysis.total_lines_removed}")
    print(f"Branch: {commit_analysis.branch_name}")

    print("\nFile details:")
    for i, file_diff in enumerate(commit_analysis.files, 1):
        print(
            f"  {i}. {file_diff.change_type.value} - {file_diff.new_path or file_diff.old_path}"
        )

    ai_context = commit_analysis.to_ai_context()
    print("\nAI Context JSON:")
    print(json.dumps(ai_context, indent=2))

    Path(".tmp").mkdir(parents=True, exist_ok=True)
    output_file = ".tmp/to_ai_context_output.json"
    with open(output_file, "w") as f:
        json.dump(ai_context, f, indent=2)

    print(f"\nAI context saved to {output_file}")


if __name__ == "__main__":
    main()
