"""
Per-file code generation with state persistence for resumability.

This module enables incremental code generation where each file is generated
by a separate LLM call, with state saved after each file for crash recovery.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from builder.infra.llm import ask_llm
from builder.infra.yaml_loader import load_research
from builder.pipeline.ast.python_ast import validate_python_ast
from builder.pipeline.ast.rust_ast import validate_rust_ast


@dataclass
class FileGenState:
    """
    Persisted state for incremental file generation.
    Allows resuming after interruption.
    """
    exchange_name: str
    language: str  # "rust" or "python"
    target_files: list[str] = field(default_factory=list)
    completed_files: dict[str, str] = field(default_factory=dict)
    failed_files: list[str] = field(default_factory=list)
    
    def save(self, path: Path) -> None:
        """Save state to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2))
    
    @classmethod
    def load(cls, path: Path) -> "FileGenState":
        """Load state from JSON file."""
        data = json.loads(path.read_text())
        return cls(**data)
    
    @property
    def pending_files(self) -> list[str]:
        """Files not yet completed or failed."""
        done = set(self.completed_files.keys()) | set(self.failed_files)
        return [f for f in self.target_files if f not in done]
    
    @property
    def progress_pct(self) -> float:
        """Completion percentage."""
        if not self.target_files:
            return 0.0
        return len(self.completed_files) / len(self.target_files) * 100


def _create_file_prompt(
    filename: str,
    template_content: str,
    exchange_name: str,
    research_json: str,
    language: str,
) -> str:
    """
    Create a focused prompt for generating a single file.
    Much smaller than the full batch prompt.
    """
    exchange_upper = exchange_name.upper()
    exchange_lower = exchange_name.lower()
    
    if language == "rust":
        lang_instructions = """
Generate Rust code following NautilusTrader adapter patterns.
Use PyO3 0.27 Bound API where applicable.
Module imports should use `nautilus_common::live::get_runtime` for async runtime.
"""
    else:
        lang_instructions = """
Generate Python code following NautilusTrader adapter patterns.
Use type hints and dataclasses where appropriate.
"""

    paradex_override = ""
    if exchange_upper == "PARADEX":
        paradex_override = """
IMPORTANT PARADEX AUTH INSTRUCTIONS:
- Use `PARADEX_SUBKEY_PRIVATE_KEY` and `PARADEX_MAIN_ACCOUNT_L2_ADDRESS` for env vars.
- Implement `ParadexSubkey` authentication (L2 only).
- Do NOT use standard API Key/Secret patterns.
- Starknet signatures are required (use `paradex-py` logic or equivalent).
"""
    if exchange_upper == "EDGEX":
        paradex_override = """
IMPORTANT EDGEX AUTH INSTRUCTIONS:
- Use `EDGEX_ACCOUNT_ID` and `EDGEX_STARK_PRIVATE_KEY` for env vars.
- Authentication uses **StarkEx ECDSA** (Stark Curve), NOT standard HMAC or EthSign.
- You MUST interpret `authType: STARKEX_ECDSA` from the research.
- Use `edgex-python-sdk` (Official: `edgex-Tech/edgex-python-sdk`) for signing where possible.
- Implement a fallback manual signer using `ecdsa` (SECP256k1) if the SDK is missing.
- The signature format is 128-char hex (r+s).
- Refer to `src/auth_builders.py` for the reference implementation of `edgex_sign`.
"""
    
    prompt = f"""You are generating a single file for the {exchange_name} adapter.

FILE TO GENERATE: {filename}

{lang_instructions}

EXCHANGE INFO:
- Name: {exchange_name}
- Upper: {exchange_upper}
- Lower: {exchange_lower}

TEMPLATE (customize for {exchange_name}):
```
{template_content}
```

RESEARCH DATA:
```json
{research_json}
```

{paradex_override}

INSTRUCTIONS:
1. Customize the template for {exchange_name}
2. Replace all placeholder names (ExchangeName, EXCHANGE_NAME, etc.) with {exchange_name}
3. Return ONLY the file content, no markdown fences, no explanation
4. Ensure valid {language.title()} syntax

OUTPUT (raw file content only):
"""
    return prompt


def generate_single_file(
    filename: str,
    template_content: str,
    exchange_name: str,
    research_json: str,
    language: str,
    max_retries: int = 2,
) -> Optional[str]:
    """
    Generate a single file using LLM.
    
    Returns generated content or None if all retries fail.
    """
    prompt = _create_file_prompt(
        filename=filename,
        template_content=template_content,
        exchange_name=exchange_name,
        research_json=research_json,
        language=language,
    )
    
    for attempt in range(max_retries + 1):
        try:
            # Shorter timeout for single file
            result = ask_llm(
                prompt=prompt,
                temperature=0.1 + (attempt * 0.05),  # Slight temp increase on retry
                cache=True,
            )
            
            # Clean up any markdown fences
            content = result.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                # Remove first and last line if they're fences
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)
            
            # Basic validation
            if language == "rust":
                # Check for common Rust syntax elements
                if "fn " in content or "struct " in content or "mod " in content or "use " in content:
                    try:
                        validate_rust_ast(content, filename)
                        return content
                    except Exception:
                        # try another sample
                        continue
            else:
                # Check for common Python syntax
                if "def " in content or "class " in content or "import " in content:
                    try:
                        validate_python_ast(content, filename)
                        return content
                    except Exception:
                        continue
            
            # If no recognizable syntax, return anyway (might be a mod.rs with just `mod` statements)
            if content and len(content) > 10:
                try:
                    if language == "rust":
                        validate_rust_ast(content, filename)
                    else:
                        validate_python_ast(content, filename)
                    return content
                except Exception:
                    continue
                
        except Exception as e:
            if attempt == max_retries:
                print(f"  ⚠️ Failed to generate {filename}: {e}")
                return None
    
    return None


def generate_files_incremental(
    research_yaml: Path,
    template_dir: Path,
    language: str,
    state_file: Optional[Path] = None,
    resume: bool = False,
) -> tuple[dict[str, str], list[str]]:
    """
    Generate files one-by-one with state persistence.
    
    Args:
        research_yaml: Path to research YAML file
        template_dir: Path to template directory (rust_crate_template or python_adapter_template)
        language: "rust" or "python"
        state_file: Optional path to save/load state (for resumability)
        resume: If True and state_file exists, resume from saved state
        
    Returns:
        Tuple of:
          - dictionary of filename -> content for all successfully generated files
          - list of filenames that failed to generate
    """
    console = Console()
    spec = load_research(research_yaml)
    exchange_name = spec.exchange_identity.exchange_name
    research_json = spec.model_dump_json(indent=2)
    
    # Determine file extension
    ext = ".rs" if language == "rust" else ".py"
    
    # Discover template files
    template_files = {}
    for f in template_dir.rglob(f"*{ext}"):
        rel_path = f.relative_to(template_dir)
        template_files[str(rel_path)] = f.read_text()
    
    # Initialize or resume state
    if resume and state_file and state_file.exists():
        state = FileGenState.load(state_file)
        console.print(f"[yellow]📂 Resuming from state: {len(state.completed_files)}/{len(state.target_files)} files done[/yellow]")
    else:
        state = FileGenState(
            exchange_name=exchange_name,
            language=language,
            target_files=list(template_files.keys()),
            completed_files={},
            failed_files=[],
        )
    
    pending = state.pending_files
    if not pending:
        console.print("[green]✅ All files already generated[/green]")
        return state.completed_files, state.failed_files
    
    console.print(f"[cyan]🔧 Generating {len(pending)} {language} files for {exchange_name}...[/cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            description=f"Generating {language} files",
            total=len(pending),
        )
        
        for filename in pending:
            progress.update(task, description=f"[cyan]{filename}[/cyan]")
            
            template_content = template_files.get(filename, "")
            
            content = generate_single_file(
                filename=filename,
                template_content=template_content,
                exchange_name=exchange_name,
                research_json=research_json,
                language=language,
            )
            
            if content:
                state.completed_files[filename] = content
                progress.console.print(f"  [green]✓[/green] {filename}")
            else:
                state.failed_files.append(filename)
                progress.console.print(f"  [red]✗[/red] {filename}")
            
            # Save state after each file
            if state_file:
                state.save(state_file)
            
            progress.advance(task)
    
    # Summary
    console.print(f"\n[green]✅ Generated {len(state.completed_files)}/{len(state.target_files)} files[/green]")
    if state.failed_files:
        console.print(f"[red]❌ Failed: {', '.join(state.failed_files)}[/red]")
    
    return state.completed_files, state.failed_files


def retry_failed_files(
    state_file: Path,
    template_dir: Path,
    research_yaml: Path,
) -> dict[str, str]:
    """
    Retry only the failed files from a previous run.
    """
    if not state_file.exists():
        raise FileNotFoundError(f"State file not found: {state_file}")
    
    state = FileGenState.load(state_file)
    spec = load_research(research_yaml)
    research_json = spec.model_dump_json(indent=2)
    
    console = Console()
    console.print(f"[yellow]🔄 Retrying {len(state.failed_files)} failed files...[/yellow]")
    
    ext = ".rs" if state.language == "rust" else ".py"
    
    for filename in list(state.failed_files):
        template_path = template_dir / filename
        template_content = template_path.read_text() if template_path.exists() else ""
        
        content = generate_single_file(
            filename=filename,
            template_content=template_content,
            exchange_name=state.exchange_name,
            research_json=research_json,
            language=state.language,
            max_retries=3,  # More retries for previously failed files
        )
        
        if content:
            state.completed_files[filename] = content
            state.failed_files.remove(filename)
            console.print(f"  [green]✓[/green] {filename}")
        else:
            console.print(f"  [red]✗[/red] {filename} (still failing)")
        
        state.save(state_file)
    
    return state.completed_files
