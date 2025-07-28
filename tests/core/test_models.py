from diffmage.core.models import FileDiff, ChangeType, FileType, CommitAnalysis


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
    )
    assert file_diff.new_path == "test.py"
    assert file_diff.change_type.value == "added"

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
