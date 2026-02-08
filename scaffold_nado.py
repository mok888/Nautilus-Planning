from pathlib import Path
from builder.scaffold import scaffold_project

def run_scaffold():
    # Output to the nautilus-dinger directory
    output_dir = Path("nautilus-dinger")
    print(f"Scaffolding 'Nado' into {output_dir}...")
    
    scaffold_project("Nado", output_dir, template_type="rust")
    scaffold_project("Nado", output_dir, template_type="python")
    
    print("✅ Scaffolding complete.")
    print(f"Created: {output_dir / 'crates/adapters/Nado'}")
    print(f"Created: {output_dir / 'nautilus_adapter/adapters/Nado'}")

if __name__ == "__main__":
    run_scaffold()
