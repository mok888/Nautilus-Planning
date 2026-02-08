from pathlib import Path
from builder.scaffold import scaffold_project

def test_scaffold_project(tmp_path):
    """Test scaffolding the full segregated project structure."""
    name = "TestExchange"
    output_dir = tmp_path
    
    scaffold_project(name, output_dir)
    
    # Check Rust Crate
    rust_path = output_dir / "crates/adapters" / name
    assert rust_path.exists(), f"Rust crate not found at {rust_path}"
    assert (rust_path / "Cargo.toml").exists()
    assert (rust_path / "src/lib.rs").exists()
    assert (rust_path / "src/common/mod.rs").exists()
    
    # Check Python Adapter
    python_path = output_dir / "nautilus_adapter/adapters" / name
    assert python_path.exists(), f"Python adapter not found at {python_path}"
    assert (python_path / "config.py").exists()
    assert (python_path / ".env_example").exists()
    assert (rust_path / ".env_example").exists()
    
    # Verify content replacement
    cargo_toml = (rust_path / "Cargo.toml").read_text()
    assert f'name = "{name.lower()}"' in cargo_toml
    
    lib_rs = (rust_path / "src/lib.rs").read_text()
    assert f'fn {name.lower()}' in lib_rs or name in lib_rs
