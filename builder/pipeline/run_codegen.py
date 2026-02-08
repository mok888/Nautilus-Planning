from pathlib import Path

from builder.pipeline.entropy import EntropyPolicy # Keep for initial generated batch? 
# actually user wants FileEntropyState which is inside retry_per_file or entropy_state
from builder.pipeline.retry import generate_with_retry # Initial global gen
from builder.pipeline.retry_per_file import regenerate_failed_files
from builder.pipeline.snapshot import compare_snapshots
from builder.pipeline.snapshot_write import write_snapshots
from builder.pipeline.enforce_critical import enforce_critical_fields
from builder.infra.yaml_loader import load_research
from builder.pipeline.rust_cargo_check import run_cargo_check
from builder.pipeline.exceptions import CodegenFailure, CriticalFieldError, SnapshotMismatch, CargoCheckError


def run_codegen(
    research_yaml: Path,
    prompt: str,
    snapshot_root: Path = None,
    update_snapshots: bool = False,
) -> dict[str, str]:
    spec = load_research(research_yaml)

    # Semantic gate
    enforce_critical_fields(spec)
    
    # Inject Research Data into Prompt
    # The prompt usually contains the Schema definition but not the data values.
    # We strip any potential placeholders just in case, or we rely on appending.
    # Initial Generation (Global Batch)
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.console import Console
    console = Console()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        
        # 1. Global Generation
        task1 = progress.add_task(description="🧠 Generating Initial Codebase...", total=None)
        
        # Extract name for replacement
        exchange_name = spec.exchange_identity.exchange_name
        exchange_upper = exchange_name.upper()
        exchange_lower = exchange_name.lower()
        rest_url = spec.rest_api.rest_base_url
        ws_public_url = spec.websocket_public.ws_public_url
        spec_json = spec.model_dump_json(indent=2)
        
        # Perform replacements on the base prompt
        full_prompt = prompt.replace("{EXCHANGE_NAME}", exchange_name) \
                            .replace("{EXCHANGE_UPPER}", exchange_upper) \
                            .replace("{EXCHANGE_LOWER}", exchange_lower) \
                            .replace("{{EXCHANGE_NAME}}", exchange_name) \
                            .replace("{{EXCHANGE_UPPER}}", exchange_upper) \
                            .replace("{{EXCHANGE_LOWER}}", exchange_lower) \
                            .replace("{{REST_URL_MAINNET}}", rest_url) \
                            .replace("{{WS_URL_PUBLIC}}", ws_public_url) \
                            .replace("{SPEC_JSON}", spec_json) \
                            .replace("{MARKDOWN}", spec_json) # Fallback markdown to JSON for now
        
        # Append Footer just in case the prompt didn't have placeholders
        if "{SPEC_JSON}" not in prompt and "{MARKDOWN}" not in prompt:
            full_prompt += f"\n\nRESEARCH DATA (JSON):\n{spec_json}"

        # Optional: Inject SKILL.md or RULES.md
        skill_file = Path("SKILL.md")
        if skill_file.exists():
            console.print(f"[blue]ℹ️ Found {skill_file}: Injecting custom rules.[/blue]")
            full_prompt += f"\n\nUSER DEFINED SKILLS / RULES:\n{skill_file.read_text()}"
        
        policy = EntropyPolicy() 
        try:
            generated = generate_with_retry(full_prompt, policy)
        except Exception as e:
            raise e
        progress.update(task1, COMPLETED=True)
        console.print(f"[green]✅ Generated {len(generated)} files.[/green]")

        # 2. File-Level Repair Loop (AST)
        file_prompts = {
            filename: f"{full_prompt}\n\nIMPORTANT: Please regenerate ONLY the file '{filename}'." 
            for filename in generated.keys()
        }
        
        task2 = progress.add_task(description="🔧 Validating & Repairing Syntax...", total=None)
        generated = regenerate_failed_files(
            initial_files=generated,
            prompts=file_prompts,
            max_rounds=6
        )
        progress.update(task2, COMPLETED=True)
        console.print("[green]✨ Syntax Validation Passed[/green]")

        # 3. Semantic Gate: Cargo Check (Rust only)
        rust_files = {k: v for k, v in generated.items() if k.endswith(".rs")}
        if rust_files:
            task3 = progress.add_task(description="🦀 Running Cargo Check...", total=None)
            run_cargo_check(rust_files)
            progress.update(task3, COMPLETED=True)
            console.print("[green]🛡️ Cargo Check Passed[/green]")

    if snapshot_root:
        if update_snapshots:
            # Intentional update
            write_snapshots(generated, snapshot_root)
        else:
            # CI regression guard
            compare_snapshots(generated, snapshot_root)

    return generated
