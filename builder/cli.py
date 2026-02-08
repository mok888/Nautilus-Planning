from pathlib import Path
import typer
import json
import sys
import subprocess
from typing import Annotated, Optional
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

from builder.pipeline.prompts.research_prompt import generate_research_prompt
from builder.pipeline.prompts.rust_codegen_prompt import generate_rust_codegen_prompt
from builder.pipeline.prompts.python_codegen_prompt import generate_python_codegen_prompt
from builder.pipeline.run_codegen import run_codegen
from builder.pipeline.snapshot_write import write_snapshots
from builder.pipeline.exceptions import BuilderError

app = typer.Typer(
    name="builder",
    help="LLM-driven NautilusTrader adapter builder",
    add_completion=False,
)


@app.command()
def research(
    exchange: Annotated[Optional[str], typer.Option("--exchange", "-e", help="Exchange name for filename generation")] = None,
    docs_url: Annotated[Optional[str], typer.Option("--url", "-u", help="Documentation URL")] = None,
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Write research prompt to file")] = None,
    auto_save: Annotated[bool, typer.Option("--save", "-s", help="Auto-save to Research_task_<Exchange>.txt")] = False,
):
    """
    Emit schema-driven research prompt.
    """
    try:
        prompt = generate_research_prompt(exchange, docs_url)

        target_file = output
        if auto_save and exchange:
            target_file = Path(f"Research_task_{exchange}.txt")

        if target_file:
            target_file.write_text(prompt)
            typer.echo(f"✅ Research prompt written to {target_file}")
        else:
            typer.echo(prompt)
    except Exception as e:
        typer.echo(f"ERROR: {e}", err=True)
        sys.exit(1)


@app.command(name="research-auto")
def research_auto(
    exchange: Annotated[str, typer.Argument(help="Exchange name (e.g. Nado, OKX)")],
    docs_url: Annotated[Optional[str], typer.Option("--url", "-u", help="URL to official API documentation")] = None,
    prompt_file: Annotated[Optional[Path], typer.Option("--prompt-file", "-p", help="Use content of this file as prompt")] = None,
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Save resulting YAML to file")] = None,
):
    """
    Perform automated research using the configured LLM provider.
    """
    from builder.infra.llm import ask_llm
    
    try:
        if prompt_file:
            full_prompt = prompt_file.read_text()
        else:
            base_prompt = generate_research_prompt(exchange, docs_url)
            context = f"Exchange: {exchange}\n"
            if docs_url:
                context += f"Documentation URL: {docs_url}\n"
            full_prompt = f"{base_prompt}\n\nCONTEXT:\n{context}"
        typer.echo(f"🚀 Performing automated research for {exchange}...")
        result = ask_llm(full_prompt, temperature=0.0)
        
        # Clean up Markdown backticks if necessary
        clean_yaml = result.replace("```yaml", "").replace("```", "").strip()
        
        if output:
            output.write_text(clean_yaml)
            typer.echo(f"✅ Research YAML written to {output}")
        else:
            typer.echo(clean_yaml)
            
    except Exception as e:
        typer.echo(f"ERROR: {e}", err=True)
        sys.exit(1)


@app.command()
def generate(
    research_yaml: Annotated[Path, typer.Argument(exists=True, readable=True, help="Validated research YAML file")],
    language: Annotated[str, typer.Option("--language", "-l", help="Target language: python | rust")],
    snapshots: Annotated[Path, typer.Option("--snapshots", "-s", help="Snapshot root directory")],
):
    """
    Generate adapter code and validate against snapshots.
    """
    try:
        if language == "python":
            prompt = generate_python_codegen_prompt()
        elif language == "rust":
            prompt = generate_rust_codegen_prompt()
        else:
            raise typer.BadParameter("language must be python or rust")

        files = run_codegen(
            research_yaml=research_yaml,
            prompt=prompt,
            snapshot_root=snapshots,
        )

        typer.echo(
            f"Codegen successful ({len(files)} files). Snapshots match."
        )
        
        # Write to project structure
        # We need to know the exchange name to determine the path
        from builder.infra.yaml_loader import load_research
        spec = load_research(research_yaml)
        
        # Correctly access the exchange name from the complex research object
        exchange_name = spec.exchange_identity.exchange_name
        
        if language == "rust":
            base_dir = Path("nautilus-dinger/crates/adapters") / exchange_name
        else:
            base_dir = Path("nautilus-dinger/nautilus_adapter/adapters") / exchange_name
            
        if base_dir.exists():
            for rel, content in files.items():
                target = base_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
            typer.echo(f"✅ Code written to {base_dir}")
        else:
             typer.echo(f"⚠️  Target directory {base_dir} does not exist. Skipping write. (Run scaffold first?)")

    except BuilderError as e:
        typer.echo(f"ERROR: {e}", err=True)
        sys.exit(1)


@app.command()
def snapshot(
    research_yaml: Annotated[Path, typer.Argument(exists=True, readable=True, help="Validated research YAML file")],
    language: Annotated[str, typer.Option("--language", "-l", help="Target language: python | rust")],
    snapshots: Annotated[Path, typer.Option("--snapshots", "-s", help="Snapshot root directory")],
):
    """
    Regenerate and WRITE snapshots (intentional mutation).
    """
    try:
        if language == "python":
            prompt = generate_python_codegen_prompt()
        elif language == "rust":
            prompt = generate_rust_codegen_prompt()
        else:
            raise typer.BadParameter("language must be python or rust")

        files = run_codegen(
            research_yaml=research_yaml,
            prompt=prompt,
            snapshot_root=None,  # bypass compare
        )

        write_snapshots(files, snapshots)
        typer.echo(
            f"Snapshots updated ({len(files)} files)."
        )

    except BuilderError as e:
        typer.echo(f"ERROR: {e}", err=True)
        sys.exit(1)


@app.command()
def scaffold(
    exchange: Annotated[str, typer.Argument(help="Exchange name (e.g. Nado, OKX)")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Root directory for the project")] = Path("nautilus-dinger"),
    research_yaml: Annotated[Optional[Path], typer.Option("--research", "-r", help="Research YAML for placeholder data")] = None,
):
    """
    Scaffold the directory structure for a new adapter.
    """
    from builder.scaffold import scaffold_project
    try:
        scaffold_project(exchange, output, research_yaml=research_yaml)
        typer.echo(f"✅ Scaffolded {exchange} adapter in {output}")
        typer.echo(f"   - crates/adapters/{exchange}")
        typer.echo(f"   - nautilus_adapter/adapters/{exchange}")
    except Exception as e:
        typer.echo(f"ERROR: {e}", err=True)
        sys.exit(1)


@app.command()
def doctor(
    json: Annotated[bool, typer.Option("--json", help="Output machine-readable JSON (CI mode)")] = False,
    fix: Annotated[bool, typer.Option("--fix", help="Print install instructions for missing tools")] = False,
    fail_fast: Annotated[bool, typer.Option("--fail-fast", help="Exit immediately on first failure")] = False,
):
    """
    Validate local environment (rustc, cargo, env vars).
    """
    from builder.cli_doctor import run_doctor

    run_doctor(
        json_output=json,
        fix=fix,
        fail_fast=fail_fast,
    )


@app.command()
def pipeline(
    exchange: Annotated[str, typer.Argument(help="Exchange name (e.g. Lighter, Nado)")],
    url: Annotated[Optional[str], typer.Option("--url", "-u", help="Documentation URL")] = None,
    update_snapshots: Annotated[bool, typer.Option("--snapshot", "-s", help="Initialize or update snapshots")] = False,
    run_tests: Annotated[bool, typer.Option("--test", "-t", help="Run automated tests after generation")] = False,
):
    """
    Run the full end-to-end pipeline: Doctor -> Research -> Scaffold -> Generate (Rust & Python).
    """
    try:
        # Phase 0: Doctor
        typer.secho(f"\n--- Phase 0: Doctor Check ---", fg=typer.colors.CYAN, bold=True)
        from builder.cli_doctor import run_doctor
        try:
            run_doctor(json_output=False, fix=False, fail_fast=False)
        except SystemExit as e:
             if e.code != 0:
                 typer.secho("❌ Doctor check failed. Fix environment before running pipeline.", fg=typer.colors.RED)
                 sys.exit(1)

        # 1. Research
        research_yaml = Path(f"builder/research/{exchange.lower()}.yaml")
        research_yaml.parent.mkdir(parents=True, exist_ok=True)
        
        typer.secho(f"\n--- Phase 1: Research ({exchange}) ---", fg=typer.colors.CYAN, bold=True)
        research_auto(exchange=exchange, docs_url=url, output=research_yaml)
        
        # 2. Scaffold
        typer.secho(f"\n--- Phase 2: Scaffolding ---", fg=typer.colors.CYAN, bold=True)
        scaffold(exchange=exchange, research_yaml=research_yaml)
        
        # 3. Generate Rust
        typer.secho(f"\n--- Phase 3: Generating Rust Core ---", fg=typer.colors.CYAN, bold=True)
        rust_snapshots = Path(f"builder/snapshots/{exchange.lower()}/rust")
        if update_snapshots:
            snapshot(research_yaml=research_yaml, language="rust", snapshots=rust_snapshots)
        else:
            generate(research_yaml=research_yaml, language="rust", snapshots=rust_snapshots)
        
        # Rust Linting & Testing
        rust_dir = Path("nautilus-dinger/crates/adapters") / exchange
        if rust_dir.exists():
            typer.echo("🦀 Running Cargo Clippy...")
            try:
                subprocess.run(["cargo", "clippy", "--fix", "--allow-dirty"], cwd=rust_dir, capture_output=True)
                typer.echo("🦀 Running Cargo Test...")
                subprocess.run(["cargo", "test"], cwd=rust_dir, capture_output=True)
            except Exception as e:
                typer.secho(f"⚠️  Rust linting/testing skipped: {e}", fg=typer.colors.YELLOW)

        # 4. Generate Python
        typer.secho(f"\n--- Phase 4: Generating Python Layer ---", fg=typer.colors.CYAN, bold=True)
        python_snapshots = Path(f"builder/snapshots/{exchange.lower()}/python")
        if update_snapshots:
            snapshot(research_yaml=research_yaml, language="python", snapshots=python_snapshots)
        else:
            generate(research_yaml=research_yaml, language="python", snapshots=python_snapshots)

        # Python Linting & Testing
        python_dir = Path("nautilus-dinger/nautilus_adapter/adapters") / exchange
        if python_dir.exists():
            typer.echo("🐍 Running Ruff Format/Check...")
            try:
                subprocess.run(["ruff", "format", "."], cwd=python_dir, capture_output=True)
                subprocess.run(["ruff", "check", "--fix", "."], cwd=python_dir, capture_output=True)
                typer.echo("🐍 Running Pytest (Local)...")
                subprocess.run(["pytest", "."], cwd=python_dir, capture_output=True)
            except Exception as e:
                typer.secho(f"⚠️  Python linting/testing skipped: {e}", fg=typer.colors.YELLOW)

        # 5. Global Automated Tests
        if run_tests:
            typer.secho(f"\n--- Phase 5: Global Integration Testing ---", fg=typer.colors.CYAN, bold=True)
            try:
                import os
                env = os.environ.copy()
                env["PYTHONPATH"] = f".:{env.get('PYTHONPATH', '')}"
                subprocess.run(["pytest", "builder/tests/"], check=True, env=env)
                typer.secho("✅ Integration tests passed!", fg=typer.colors.GREEN)
            except subprocess.CalledProcessError:
                typer.secho("❌ Integration tests failed.", fg=typer.colors.RED)
                sys.exit(1)
        
        typer.secho(f"\n✨ Pipeline complete for {exchange}! ✨", fg=typer.colors.GREEN, bold=True)
        
    except Exception as e:
        typer.echo(f"ERROR: {e}", err=True)
        sys.exit(1)


def main():
    app()


if __name__ == "__main__":
    main()
