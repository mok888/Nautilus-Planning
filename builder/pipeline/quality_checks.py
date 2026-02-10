from __future__ import annotations

import re
from typing import Dict, List

from builder.pipeline.exceptions import CodegenFailure


_PLACEHOLDER_RE = re.compile(r"\{\{[A-Za-z0-9_]+\}\}")
_TODO_RE = re.compile(r"\b(TODO|FIXME|TBD)\b")


def ensure_no_unresolved_placeholders(files: Dict[str, str]) -> None:
    offenders: Dict[str, List[str]] = {}
    for path, content in files.items():
        matches = sorted(set(_PLACEHOLDER_RE.findall(content)))
        if matches:
            offenders[path] = matches

    if not offenders:
        return

    lines = ["Unresolved template placeholders found:"]
    for path, matches in offenders.items():
        lines.append(f"- {path}: {', '.join(matches)}")
    raise CodegenFailure("\n".join(lines))


def ensure_no_todo_markers(files: Dict[str, str]) -> None:
    hits: List[str] = []
    for path, content in files.items():
        for lineno, line in enumerate(content.splitlines(), start=1):
            if _TODO_RE.search(line):
                hits.append(f"{path}:{lineno}: {line.strip()}")

    if not hits:
        return

    sample = hits[:25]
    suffix = "" if len(hits) <= 25 else f"\n... and {len(hits) - 25} more"
    raise CodegenFailure("TODO/FIXME/TBD markers found:\n" + "\n".join(sample) + suffix)
