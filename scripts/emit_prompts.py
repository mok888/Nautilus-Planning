from builder.pipeline.prompts.research_prompt import generate_research_prompt
from builder.pipeline.prompts.rust_codegen_prompt import generate_rust_codegen_prompt
from builder.pipeline.prompts.python_codegen_prompt import generate_python_codegen_prompt

print("=== RESEARCH PROMPT ===")
print(generate_research_prompt())

print("\n=== RUST CODEGEN PROMPT ===")
print(generate_rust_codegen_prompt())

print("\n=== PYTHON CODEGEN PROMPT ===")
print(generate_python_codegen_prompt())
