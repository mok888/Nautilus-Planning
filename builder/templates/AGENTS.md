# TEMPLATE KNOWLEDGE BASE

## OVERVIEW
`builder/templates/` defines canonical generated adapter structure. Changes here propagate to both snapshot outputs and runtime adapter code.

## STRUCTURE
```
builder/templates/
├── rust_crate_template/        # Canonical Rust adapter layout
└── python_adapter_template/    # Canonical Python adapter layout
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Rust module skeleton | `builder/templates/rust_crate_template/src/` | common/http/websocket/python/data/execution/testing |
| Rust dependency policy | `builder/templates/rust_crate_template/Cargo.toml` | enforced stack and features |
| Python adapter skeleton | `builder/templates/python_adapter_template/` | config/constants/data/execution/factories/providers |
| Placeholder surface | both template roots | `{{EXCHANGE_*}}`, URL placeholders |

## CONVENTIONS
- Template files are canonical sources for generated adapter shape.
- Placeholder naming must remain consistent across Rust and Python templates.
- Keep template structure aligned with generated adapters and snapshots.

## ANTI-PATTERNS
- Do not hardcode exchange-specific values in templates.
- Do not introduce dependencies forbidden by pipeline prompts.
- Do not edit generated adapters first when pattern fixes belong in templates.
