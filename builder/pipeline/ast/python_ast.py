import ast


class PythonASTError(RuntimeError):
    pass


def validate_python_ast(code: str, filename: str) -> None:
    try:
        ast.parse(code, filename=filename)
    except SyntaxError as e:
        raise PythonASTError(
            f"Invalid Python AST in {filename}: {e}"
        ) from e
