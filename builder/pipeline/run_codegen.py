from pathlib import Path
import os
import json

from builder.pipeline.entropy import EntropyPolicy # Keep for initial generated batch? 
# actually user wants FileEntropyState which is inside retry_per_file or entropy_state
from builder.pipeline.retry import generate_with_retry # Initial global gen
from builder.pipeline.retry_per_file import regenerate_failed_files
from builder.pipeline.generate_per_file import generate_files_incremental, FileGenState
from builder.pipeline.snapshot import compare_snapshots
from builder.pipeline.snapshot_write import write_snapshots
from builder.pipeline.enforce_critical import enforce_critical_fields
from builder.infra.yaml_loader import load_research
from builder.pipeline.rust_cargo_check import run_cargo_check
from builder.pipeline.exceptions import CodegenFailure, CriticalFieldError, SnapshotMismatch, CargoCheckError
from builder.pipeline.quality_checks import ensure_no_unresolved_placeholders, ensure_no_todo_markers
from builder.pipeline.ast.validate_strict import validate_generated_files


def run_codegen(
    research_yaml: Path,
    prompt: str,
    snapshot_root: Path = None,
    update_snapshots: bool = False,
    strict: bool = False,
    skip_cargo_check: bool = False,
    incremental: bool = True,  # NEW: per-file generation (default)
    resume: bool = False,       # NEW: resume from state file
    language: str = "rust",     # NEW: "rust" or "python"
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

    # Extract name for replacement
    exchange_name = spec.exchange_identity.exchange_name
    exchange_upper = exchange_name.upper()
    exchange_lower = exchange_name.lower()
    rest_url = spec.rest_api.rest_base_url
    ws_public_url = spec.websocket_public.ws_public_url
    
    # Optionally reduce prompt size
    if os.getenv("LLM_MIN_SPEC", "").strip().lower() in {"1", "true", "yes"}:
        minimal = {
            "exchange_identity": spec.exchange_identity.model_dump(),
            "rest_api": {"rest_base_url": rest_url},
            "websocket_public": {"ws_public_url": ws_public_url},
        }
        spec_json = json.dumps(minimal, indent=2)
    else:
        spec_json = spec.model_dump_json(indent=2)

    # ========== INCREMENTAL MODE (per-file generation) ==========
    if incremental:
        console.print(f"[cyan]🔧 Running in INCREMENTAL mode (per-file generation)[/cyan]")
        
        # Determine template directory
        if language == "rust":
            template_dir = Path("builder/templates/rust_crate_template/src")
        else:
            template_dir = Path("builder/templates/python_adapter_template")
        
        # State file for resumability
        state_file = Path(f"builder/.state/{exchange_name.lower()}_{language}_gen.json")
        
        generated, failed_files = generate_files_incremental(
            research_yaml=research_yaml,
            template_dir=template_dir,
            language=language,
            state_file=state_file,
            resume=resume,
        )
        
        if failed_files:
            raise CodegenFailure(
                f"Failed to generate {len(failed_files)} file(s): {', '.join(failed_files)}"
            )
        
        console.print(f"[green]✅ Generated {len(generated)} files (incremental).[/green]")
    
    # ========== BATCH MODE (legacy single-call generation) ==========
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            
            # 1. Global Generation
            task1 = progress.add_task(description="🧠 Generating Initial Codebase...", total=None)
            
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

            # Specific prompt overrides for Paradex
            if exchange_upper == "PARADEX":
                full_prompt += "\n\nIMPORTANT PARADEX AUTH INSTRUCTIONS:\n"
                full_prompt += "- Use `PARADEX_SUBKEY_PRIVATE_KEY` and `PARADEX_MAIN_ACCOUNT_L2_ADDRESS` for env vars.\n"
                full_prompt += "- Implement `ParadexSubkey` authentication (L2 only).\n"
                full_prompt += "- Do NOT use standard API Key/Secret patterns.\n"
                full_prompt += "- Starknet signatures are required (use `paradex-py` logic or equivalent).\n"

            # Specific prompt overrides for EdgeX
            if exchange_upper == "EDGEX":
                full_prompt += "\n\nIMPORTANT EDGEX AUTH INSTRUCTIONS:\n"
                full_prompt += "- Use `EDGEX_ACCOUNT_ID` and `EDGEX_STARK_PRIVATE_KEY` for env vars.\n"
                full_prompt += "- Authentication uses **StarkEx ECDSA** (Stark Curve), NOT standard HMAC or EthSign.\n"
                full_prompt += "- You MUST interpret `authType: STARKEX_ECDSA` from the research.\n"
                full_prompt += "- Use `edgex-python-sdk` (Official: `edgex-Tech/edgex-python-sdk`) for signing where possible.\n"
                full_prompt += "- Implement a fallback manual signer using `ecdsa` (SECP256k1) if the SDK is missing.\n"
                full_prompt += "- The signature format is 128-char hex (r+s).\n"
                full_prompt += "- Refer to `src/auth_builders.py` for the reference implementation.\n"

            # Specific prompt overrides for Nado
            if exchange_upper == "NADO":
                full_prompt += "\n\nIMPORTANT NADO AUTH INSTRUCTIONS:\n"
                full_prompt += "- Use `NADO_PRIVATE_KEY` and `NADO_SUBACCOUNT_ID` for env vars.\n"
                full_prompt += "- Public endpoints (e.g., `subaccount_info`) typically require query params but NO auth headers.\n"
                full_prompt += "- Write endpoints require **EIP-712 Signing** inside the JSON payload.\n"
                full_prompt += "- **DO NOT** use the `nado-protocol` SDK due to Pydantic v1 conflicts.\n"
                full_prompt += "- Implement signature logic using `eth_account` and `encode_structured_data`.\n"
                full_prompt += "- Refer to `src/auth_builders.py` (`nado_sign`) for the exact EIP-712 types and domain structure.\n"

            # Specific prompt overrides for Apex Omni
            if exchange_upper == "APEX_OMNI":
                full_prompt += "\n\nIMPORTANT APEX OMNI AUTH INSTRUCTIONS:\n"
                full_prompt += "- Use `APEX_API_KEY`, `APEX_API_KEY_SECRET`, `APEX_API_KEY_PASSPHRASE` and `APEX_OMNI_KEY_SEED`.\n"
                full_prompt += "- Use the official `apexomni` SDK (v3.1.7+) for authentication where possible.\n"
                full_prompt += "- Initialize `HttpPrivate_v3` with `api_key_credentials` dictionary.\n"
                full_prompt += "- The SDK handles the complex ZK key derivation from the seed internally.\n"
                full_prompt += "- Do NOT attempt to reimplement ZK key derivation manually unless necessary.\n"

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
            progress.update(task1, completed=True)
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

        # 2.5 Template Placeholder Guard
        ensure_no_unresolved_placeholders(generated)

        if strict:
            ensure_no_todo_markers(generated)

        # 3. Semantic Gate: Cargo Check (Rust only)
        rust_files = {k: v for k, v in generated.items() if k.endswith(".rs")}
        if rust_files and not skip_cargo_check:
            task3 = progress.add_task(description="🦀 Running Cargo Check...", total=None)
            run_cargo_check(rust_files, strict=strict)
            progress.update(task3, COMPLETED=True)
            console.print("[green]🛡️ Cargo Check Passed[/green]")

    # Post-processing for incremental path (batch already validated above)
    if incremental:
        # Syntax/AST validation
        validate_generated_files(generated)

        # Template placeholder guard
        ensure_no_unresolved_placeholders(generated)

        if strict:
            ensure_no_todo_markers(generated)

        # Rust semantic gate
        rust_files = {k: v for k, v in generated.items() if k.endswith(".rs")}
        if rust_files and not skip_cargo_check:
            run_cargo_check(rust_files, strict=strict)

    if snapshot_root:
        if update_snapshots:
            # Intentional update
            write_snapshots(generated, snapshot_root)
        else:
            # CI regression guard
            compare_snapshots(generated, snapshot_root)

    return generated
