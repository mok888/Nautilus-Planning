import ast, hashlib

def fingerprint(code: str) -> str:
    """
    Generate a structural fingerprint of Python code, ignoring formatting/comments.
    Returns SHA256 of the AST dump.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # If code is invalid python (or not python), fallback to text hash
        return hashlib.sha256(code.encode()).hexdigest()

    # Clear location info to make it formatting-invariant
    for n in ast.walk(tree):
        for a in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
            if hasattr(n, a):
                setattr(n, a, None)
                
    return hashlib.sha256(ast.dump(tree).encode()).hexdigest()
