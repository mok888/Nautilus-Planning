# BUILDER KNOWLEDGE BASE

## OVERVIEW
`builder/` is the generation control plane: research prompting, codegen orchestration, validation gates, scaffolding, and snapshot regression.

## STRUCTURE
```
builder/
├── cli.py                 # Main command surface
├── pipeline/              # Orchestration + validation gates (has its own AGENTS.md)
├── infra/                 # LLM, cache, YAML loading
├── config/                # pipeline.yaml + schema.yaml
├── templates/             # Rust/Python adapter templates
├── snapshots/             # Golden generated outputs per exchange
├── research/              # Exchange research YAML + prompt artifacts
├── auth-scraper/          # Auth/connectivity utility project
└── tests/                 # Builder pytest suite + snapshot utility
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Run full pipeline | `builder/cli.py` (`pipeline` command) | end-to-end exchange flow |
| Tune generation behavior | `builder/config/pipeline.yaml` | model, retries, entropy thresholds |
| Adjust research schema | `builder/config/schema.yaml` | required fields and structure |
| Add gate/check | `builder/pipeline/` | keep gate ordering intact |
| Update template output shape | `builder/templates/` | template-first source of truth |
| Validate snapshot behavior | `builder/pipeline/snapshot.py`, `builder/tests/snapshot_utils.py` | compare/update golden output |

## CONVENTIONS
- `builder/cli.py` is the authoritative command surface.
- Pipeline uses incremental/per-file generation by default.
- Research data is schema-validated before generation.
- Snapshots are intentional golden artifacts, not runtime sources.

## ANTI-PATTERNS
- Do not treat `builder/snapshots/` as hand-authored runtime code.
- Do not bypass critical-field checks (`venue_id`, auth, precision fields).
- Do not duplicate deep pipeline details here; use `builder/pipeline/AGENTS.md`.
