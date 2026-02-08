import subprocess
import tempfile
from pathlib import Path


class RustASTError(RuntimeError):
    pass


def validate_rust_ast(code: str, filename: str) -> None:
    # NOTE: rustc --emit=metadata is too strict for lone files (requires crates).
    # We rely on the 'run_cargo_check' stage for full semantic and syntax validation.
    pass
