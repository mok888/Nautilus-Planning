import os
from pathlib import Path
from dotenv import load_dotenv

# MUST load env for LLM_PROVIDER and LLM_MODEL
load_dotenv()

from builder.infra.yaml_loader import load_research
from builder.pipeline.prompts.rust_codegen_prompt import generate_rust_codegen_prompt
from builder.pipeline.retry import generate_with_retry
from builder.pipeline.entropy import EntropyPolicy
from builder.pipeline.ast.validate_with_report import validate_files_with_report

def debug_nado_rust():
    research_yaml = Path("builder/research/nado.yaml")
    spec = load_research(research_yaml)
    prompt = generate_rust_codegen_prompt()
    full_prompt = f"{prompt}\n\nRESEARCH DATA (JSON):\n{spec.model_dump_json(indent=2)}"
    
    print("🚀 Running initial generation...")
    policy = EntropyPolicy()
    generated = generate_with_retry(full_prompt, policy)
    
    print(f"✅ Generated {len(generated)} files.")
    
    print("🔍 Validating AST...")
    ok, failed = validate_files_with_report(generated)
    
    if ok:
        print("✨ AST Validation PASSED")
    else:
        print(f"❌ AST Validation FAILED for {len(failed)} files:")
        for path in failed:
            print(f"  - {path}")

if __name__ == "__main__":
    debug_nado_rust()
