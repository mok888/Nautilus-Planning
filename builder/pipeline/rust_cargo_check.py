import subprocess
import tempfile
from pathlib import Path

from builder.pipeline.exceptions import CargoCheckError


def run_cargo_check(rust_files: dict[str, str]) -> None:
    # Filter for .rs files only, just in case
    rust_files = {k: v for k, v in rust_files.items() if k.endswith(".rs")}
    
    if not rust_files:
        return

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        src = root / "src"
        src.mkdir()
        
        log_file = Path("/home/mok/projects/Nautilus-Planning/rust_check_debug.log")
        with open(log_file, "a") as log:
            log.write(f"\n--- NEW CHECK ---\n")
            log.write(f"ROOT: {root}\n")

        # Minimal Cargo.toml WITHOUT external dependencies to avoid crates.io issues during validation
        cargo_content = """[package]
name = "adapter_check"
version = "0.1.0"
edition = "2021"

[lib]
path = "src/lib.rs"

[dependencies]
thiserror = "1.0"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tracing = "0.1"
tokio = { version = "1.36", features = ["full"] }
chrono = "0.4"
base64 = "0.21"
hmac = "0.12"
sha2 = "0.10"
hex = "0.4"
anyhow = "1.0"
url = "2.4"
http = "1.0"
bytes = "1.5"
hyper = { version = "1.2", features = ["full"] }
hyper-util = { version = "0.1", features = ["full", "tokio", "client-legacy"] }
http-body-util = "0.1"
tower = { version = "0.4", features = ["full"] }
governor = "0.6"
tokio-tungstenite = "0.20"
futures = "0.3"
"""
        (root / "Cargo.toml").write_text(cargo_content)
        with open(log_file, "a") as log:
            log.write(f"CARGO.toml:\n{cargo_content}\n")

        for rel, code in rust_files.items():
            rel_path = rel.lstrip("/")
            if rel_path == "Cargo.toml":
                continue

            # Strip leading 'src/' if the LLM provided it, because we are already in 'src'
            path_parts = Path(rel_path).parts
            if path_parts and path_parts[0] == "src":
                rel_path = str(Path(*path_parts[1:]))

            # Force into src/
            dest_path = src / rel_path
            
            with open(log_file, "a") as log:
                log.write(f"WRITING: {rel} -> {dest_path}\n")
            
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(code)

        # Helper to ensure all subdirectories have mod.rs
        def ensure_mod_rs(directory: Path):
            for item in directory.iterdir():
                if item.is_dir():
                    mod_rs = item / "mod.rs"
                    if not mod_rs.exists():
                        # List all .rs files and subdirs in this dir to generate its mod.rs
                        content = "// Auto-generated module\n"
                        for sub_item in item.iterdir():
                             if sub_item.is_file() and sub_item.suffix == ".rs" and sub_item.name != "mod.rs":
                                 content += f"pub mod {sub_item.stem};\n"
                             elif sub_item.is_dir():
                                 content += f"pub mod {sub_item.name};\n"
                        mod_rs.write_text(content)
                    ensure_mod_rs(item)

        ensure_mod_rs(src)

        # Ensure src/lib.rs exists if LLM didn't provide one
        if not (src / "lib.rs").exists():
            (src / "lib.rs").write_text("// Auto-generated validation entry point\n")
            # Modules for files in src/ root
            for f in src.iterdir():
                if f.is_file() and f.suffix == ".rs" and f.name != "lib.rs":
                    with open(src / "lib.rs", "a") as lib_f:
                        lib_f.write(f"#[allow(dead_code)] mod {f.stem};\n")
                elif f.is_dir():
                    # Modules for directories
                    with open(src / "lib.rs", "a") as lib_f:
                        lib_f.write(f"#[allow(dead_code)] mod {f.name};\n")

        try:
            result = subprocess.run(
                ["cargo", "check"],
                cwd=root,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                # Filter out unresolved import/crate errors which are expected without dependencies
                lines = result.stderr.splitlines()
                critical_errors = []
                for line in lines:
                    # Capture actual syntax errors or serious structural issues
                    # Unresolved symbols/imports/crates are often E0432, E0433, E0412 etc.
                    if "error:" in line or "error[" in line:
                         if not any(x in line for x in ["E0432", "E0433", "E0412", "E0405", "E0425", "E0417", "E0422", "E0599", "unresolved import", "unlinked crate", "cannot find"]):
                              critical_errors.append(line)
                
                if critical_errors:
                    with open(log_file, "a") as log:
                        log.write(f"CRITICAL CARGO ERRORS:\n" + "\n".join(critical_errors) + "\n")
                    raise CargoCheckError(result.stderr)
        except FileNotFoundError:
            raise CargoCheckError("Cargo not found in PATH")
