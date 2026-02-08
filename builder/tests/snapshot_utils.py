from pathlib import Path
import os
import difflib

def assert_snapshot(content: str, snapshot_path: Path):
    """
    Compare generated content against a stored snapshot.
    If UPDATE_SNAPSHOTS env var is set, verify/write the snapshot.
    """
    snapshot_path = Path(snapshot_path)
    
    if os.getenv("UPDATE_SNAPSHOTS") or not snapshot_path.exists():
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(content)
        return

    expected = snapshot_path.read_text()
    
    # Normalize line endings
    content = content.replace("\r\n", "\n").strip()
    expected = expected.replace("\r\n", "\n").strip()
    
    if content != expected:
        diff = difflib.unified_diff(
            expected.splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile=str(snapshot_path),
            tofile="generated",
        )
        diff_text = "".join(diff)
        raise AssertionError(f"Snapshot mismatch for {snapshot_path}:\n{diff_text}")
