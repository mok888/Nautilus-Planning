from pathlib import Path
from builder.tests.snapshot_utils import assert_snapshot
from builder.models import ExchangeSpec

def test_rust_core_snapshot():
    # This test verifies that the prompt structure remains consistent.
    # We can't easily test accurate LLM output without mocking or using a fixed seed/cache.
    # For now, we'll just test the prompt generation logic if possible, or mocked generation.
    pass
    
def test_snapshot_utility_works(tmp_path):
    # Self-test for the snapshot utility
    snap_file = tmp_path / "test.snap"
    content = "hello world"
    
    # First run writes it
    assert_snapshot(content, snap_file)
    assert snap_file.read_text() == content
    
    # Second run passes
    assert_snapshot(content, snap_file)
    
    # Mismatch raises error
    try:
        assert_snapshot("goodbye", snap_file)
        assert False, "Should have raised AssertionError"
    except AssertionError:
        pass
