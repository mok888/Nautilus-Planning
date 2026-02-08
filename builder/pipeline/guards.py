from builder.pipeline.utils.entropy import normalize, similarity
from builder.pipeline.utils.ast_utils import fingerprint

class EntropyViolation(RuntimeError):
    pass

class ASTViolation(RuntimeError):
    pass

def enforce_entropy(outputs: list[str], min_similarity: float) -> str:
    """
    Ensure all outputs are textually similar enough.
    Returns the first output if consistent.
    """
    if not outputs:
        raise ValueError("No outputs to check")
        
    base = normalize(outputs[0])
    for o in outputs[1:]:
        sim = similarity(base, normalize(o))
        if sim < min_similarity:
            raise EntropyViolation(f"Entropy violation: similarity {sim:.2f} < {min_similarity}")
            
    return outputs[0]

def enforce_ast(outputs: list[str]) -> str:
    """
    Ensure all outputs have identical AST structure.
    Returns the first output if consistent.
    """
    if not outputs:
        raise ValueError("No outputs to check")
        
    base = fingerprint(outputs[0])
    for o in outputs[1:]:
        if fingerprint(o) != base:
            raise ASTViolation("AST violation: structures do not match")
            
    return outputs[0]
