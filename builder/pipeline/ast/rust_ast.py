import subprocess
import tempfile
from pathlib import Path


class RustASTError(RuntimeError):
    pass


def validate_rust_ast(code: str, filename: str) -> None:
    """
    Lightweight Rust syntax check for a single file.

    We prefer `rustfmt --check` as a fast parser; if unavailable, fall back to
    `rustc --emit=metadata` in a temporary crate. This catches basic parse errors
    even when cargo check is skipped.
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            src = tmp / "snippet.rs"
            src.write_text(code)

            # Fast path: rustfmt parser
            fmt = subprocess.run(
                ["rustfmt", str(src)],
                capture_output=True,
                text=True,
            )
            if fmt.returncode == 0:
                return
            # If rustfmt missing, result.returncode will be 127 on many systems.
            if "not found" in (fmt.stderr or "").lower() or "unable to find" in (fmt.stderr or "").lower():
                # Fallback to rustc parse-only
                pass
            elif fmt.returncode != 0:
                raise RustASTError(
                    f"Invalid Rust syntax in {filename}:\n{fmt.stderr or fmt.stdout}"
                )

            # Fallback: rustc metadata compile in a temp crate
            crate_dir = Path(tmpdir) / "crate"
            crate_src = crate_dir / "src"
            crate_src.mkdir(parents=True, exist_ok=True)
            (crate_dir / "Cargo.toml").write_text(
                "[package]\nname = \"ast_check\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[lib]\npath = \"src/lib.rs\"\n"
            )
            (crate_src / "lib.rs").write_text(code)

            result = subprocess.run(
                ["cargo", "check", "--quiet"],
                cwd=crate_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise RustASTError(
                    f"Invalid Rust syntax in {filename}:\n{result.stderr}"
                )
    except FileNotFoundError as e:
        raise RustASTError("Rust toolchain not found for AST validation") from e
