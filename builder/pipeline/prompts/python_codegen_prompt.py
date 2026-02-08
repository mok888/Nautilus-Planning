from builder.pipeline.models import ExchangeResearch
from builder.pipeline.schema_walk import walk_schema

def generate_python_codegen_prompt() -> str:
    schema = walk_schema(ExchangeResearch)

    return "\n".join([
        "You are a NautilusTrader adapter engineer.",
        "",
        "TASK:",
        "Generate the Python adapter layer for {EXCHANGE_NAME} from the schema.",
        "",
        "STRICT RULES:",
        "- Follow NautilusTrader adapter standards",
        "- Use smart placeholders (e.g., {{EXCHANGE_NAME}}, {{EXCHANGE_UPPER}}, {{EXCHANGE_LOWER}}, {{REST_URL_MAINNET}}, {{WS_URL_PUBLIC}}) in your generation where applicable, or replace them if they are in provided snippets",
        "- Proper inheritance",
        "- Typed methods",
        "- No placeholders",
        "",
        "OUTPUT FORMAT:",
        "{ \"python_files\": { \"<relative/path.py>\": \"<contents>\" } }",
        "",
        "REQUIRED FILES:",
        "- config.py",
        "- constants.py",
        "- data.py",
        "- execution.py",
        "- factories.py",
        "- providers.py",
        "",
        "SCHEMA:",
        *schema,
        "",
        "RESEARCH DATA:",
        "{SPEC_JSON}",
        "",
        "IMPORTANT:",
        "- UNKNOWN means unsupported",
        "- Use `{EXCHANGE_NAME}_API_KEY` and `{EXCHANGE_NAME}_API_SECRET` for environment variables",
        "- Do not invent behavior",
    ])
