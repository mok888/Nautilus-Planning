import re
from difflib import SequenceMatcher

def normalize(code: str) -> str:
    """Normalize code for comparison (strip comments/docstrings/whitespace)."""
    # Remove docstrings (simple approximation)
    code = re.sub(r'""".*?"""', "", code, flags=re.S)
    code = re.sub(r"'''.*?'''", "", code, flags=re.S)
    # Remove usage of # comments
    code = re.sub(r"#.*", "", code)
    # Normalize whitespace
    return "\n".join(l.strip() for l in code.splitlines() if l.strip())

def similarity(a: str, b: str) -> float:
    """Calculate similarity ratio between two code strings."""
    return SequenceMatcher(None, a, b).ratio()
