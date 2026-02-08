import shutil
import os
from pathlib import Path
from typing import Literal

TemplateType = Literal["python", "rust"]

def scaffold_project(name: str, output_dir: Path, template_type: TemplateType = "python", research_yaml: Path | None = None):
    """
    Scaffold a new Nautilus adapter project with segregated structure.
    
    Creates:
      output_dir/crates/adapters/<name>/
      output_dir/nautilus_adapter/adapters/<name>/
    """
    
    # Define target paths
    rust_root = output_dir / "crates/adapters" / name
    python_root = output_dir / "nautilus_adapter/adapters" / name
    
    # Ensure cleaner slate or create parents
    rust_root.parent.mkdir(parents=True, exist_ok=True)
    python_root.parent.mkdir(parents=True, exist_ok=True)

    templates_dir = Path(__file__).parent / "templates"
    
    # 1. Scaffold Rust Crate
    # We always start with the rust_crate_template as the base
    rust_src_template = templates_dir / "rust_crate_template"
    
    # Copy Rust crate content excluding the python wrapper folder
    if rust_root.exists():
        shutil.rmtree(rust_root)
    shutil.copytree(rust_src_template, rust_root, ignore=shutil.ignore_patterns("my_exchange"))
    
    # 2. Scaffold Python Adapter
    python_src_template = templates_dir / "python_adapter_template"
    if python_root.exists():
        shutil.rmtree(python_root)
    shutil.copytree(python_src_template, python_root)

    # Resolve URLs from research if available
    rest_url = "{{REST_URL_MAINNET}}"
    testnet_url = "{{REST_URL_TESTNET}}"
    ws_url = "{{WS_URL_PUBLIC}}"
    ws_private_url = "{{WS_URL_PRIVATE}}"
    venue_id = name.upper()
    
    if research_yaml and research_yaml.exists():
        from builder.infra.yaml_loader import load_research
        spec = load_research(research_yaml)
        rest_url = spec.rest_api.rest_base_url
        ws_url = spec.websocket_public.ws_public_url
        ws_private_url = spec.websocket_private.ws_private_url
        venue_id = spec.exchange_identity.venue_id
    
    # Rename placeholders in ALL scaffolded files
    placeholders = {
        "{{EXCHANGE_NAME}}": name,
        "{{EXCHANGE_UPPER}}": venue_id,
        "{{EXCHANGE_LOWER}}": name.lower(),
        "MyExchange": name,
        "MY_EXCHANGE": venue_id,
        "my_exchange": name.lower(),
        "myexchange": name.lower(),
        "{{REST_URL_MAINNET}}": rest_url,
        "{{REST_URL_TESTNET}}": testnet_url,
        "{{WS_URL_PUBLIC}}": ws_url,
        "{{WS_URL_PRIVATE}}": ws_private_url,
    }
    
    for root_dir in [rust_root, python_root]:
        for root, _, files in os.walk(root_dir):
            for file in files:
                file_path = Path(root) / file
                _apply_placeholders(file_path, placeholders)

    # 3. Create .env_example
    env_example = f"""# {name} Adapter Configuration
{name.upper()}_API_KEY=your_api_key_here
{name.upper()}_API_SECRET=your_secret_here
# {name.upper()}_PASSPHRASE=your_passphrase_if_required
"""
    (python_root / ".env_example").write_text(env_example)
    (rust_root / ".env_example").write_text(env_example)

def _apply_placeholders(path: Path, placeholders: dict[str, str]):
    if path.exists() and path.is_file():
        try:
            content = path.read_text()
            new_content = content
            for search, replace in placeholders.items():
                new_content = new_content.replace(search, replace)
            
            if new_content != content:
                path.write_text(new_content)
        except UnicodeDecodeError:
            pass # Skip binary files
