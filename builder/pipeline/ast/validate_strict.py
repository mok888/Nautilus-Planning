from builder.pipeline.ast.python_ast import validate_python_ast
from builder.pipeline.ast.rust_ast import validate_rust_ast


def validate_generated_files(files: dict[str, str]) -> None:
    for path, code in files.items():
        if path.endswith(".py"):
            validate_python_ast(code, path)
        elif path.endswith(".rs"):
            validate_rust_ast(code, path)
