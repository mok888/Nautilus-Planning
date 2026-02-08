from pathlib import Path


def write_snapshots(
    generated: dict[str, str],
    snapshot_root: Path,
) -> None:
    for rel_path, code in generated.items():
        path = snapshot_root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code)
