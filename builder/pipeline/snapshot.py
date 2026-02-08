from pathlib import Path
import difflib

from builder.pipeline.exceptions import SnapshotMismatch


def compare_snapshots(
    generated: dict[str, str],
    snapshot_root: Path,
) -> None:
    if not snapshot_root.exists():
        return # New snapshot case or snapshotting disabled

    for rel_path, code in generated.items():
        expected = snapshot_root / rel_path

        if not expected.exists():
            # If snapshot root exists but file doesn't, it's a mismatch (missing file)
            # Or we can treat it as a new file to be approved.
            # Strict mode: mismatch.
            raise SnapshotMismatch(
                f"Missing snapshot: {rel_path}"
            )

        expected_code = expected.read_text()

        if code != expected_code:
            diff = "\n".join(
                difflib.unified_diff(
                    expected_code.splitlines(),
                    code.splitlines(),
                    fromfile="expected",
                    tofile="generated",
                )
            )

            raise SnapshotMismatch(
                f"Snapshot diff for {rel_path}:\n{diff}"
            )
