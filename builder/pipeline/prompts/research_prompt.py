from builder.pipeline.models import ExchangeResearch
from builder.pipeline.schema_walk import walk_schema

def generate_research_prompt(exchange: str = None, docs_url: str = None, output_path: str = None) -> str:
    schema = walk_schema(ExchangeResearch)

    intent = "a quantitative trading systems researcher"
    if exchange:
        intent = f"a researcher analyzing the {exchange} exchange"

    lines = [
        f"You are {intent}.",
        "",
        "TASK:",
        "Fill in the following schema using ONLY verifiable facts.",
    ]
    
    if docs_url:
        lines.append(f"Official Docs: {docs_url}")

    if output_path:
        lines.append(f"OUTPUT INSTRUCTION: Return ONLY the YAML content. The user intends to save this to: {output_path}")

    lines.extend([
        "",
        "RULES:",
        "- Use official docs or GitHub only",
        "- For 'venue_id', ALWAYS provide a value. If not found, use the UPPERCASE exchange name.",
        "- For 'price_precision' and 'quantity_precision', look for tick size or step size. If not found, make an educated guess (e.g., 8).",
        "- For other fields, if truly unknown, write EXACTLY: UNKNOWN",
        "- Preserve field names exactly",
        "- Output VALID YAML ONLY",
        "",
        *schema,
        "",
        "NO commentary. YAML only."
    ])

    return "\n".join(lines)
