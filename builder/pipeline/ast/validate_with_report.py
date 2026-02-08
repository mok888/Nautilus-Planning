from builder.pipeline.ast.python_ast import validate_python_ast
from builder.pipeline.ast.rust_ast import validate_rust_ast

def validate_files_with_report(
    files: dict[str, str],
) -> tuple[bool, list[str]]:
    failed: list[str] = []

    for path, code in files.items():
        try:
            if path.endswith(".py"):
                validate_python_ast(code, path)
            elif path.endswith(".rs"):
                validate_rust_ast(code, path)
        except Exception:
            failed.append(path)

    return (len(failed) == 0, failed)
