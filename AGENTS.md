# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-12
**Commit:** 5d7e712
**Branch:** master

## OVERVIEW
Monorepo for LLM-driven NautilusTrader adapter generation. Python builder orchestrates research/codegen/validation; Rust and Python adapters live under `nautilus-dinger/`.

## STRUCTURE
```
./
├── builder/                      # Generation pipeline + templates + snapshots
│   ├── pipeline/                 # Core orchestration and validation gates
│   ├── auth-scraper/             # Exchange auth/connectivity utility project
│   ├── templates/                # Rust/Python adapter templates
│   ├── snapshots/                # Golden generated outputs per exchange
│   └── tests/                    # Builder pytest suite + snapshot utility
├── nautilus-dinger/              # Nested Python package + Rust workspace
│   ├── crates/adapters/{Exchange}/
│   ├── nautilus_adapter/adapters/{Exchange}/
│   └── tests/
└── config/.codex/                # Local Codex config (tooling only)
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Full pipeline | `builder/cli.py` (`pipeline`) | doctor → research → scaffold → generate rust/python |
| Research prompt/schema | `builder/pipeline/prompts/research_prompt.py`, `builder/config/schema.yaml` | `venue_id` rule enforced |
| Rust codegen constraints | `builder/pipeline/prompts/rust_codegen_prompt.py` | hard dependency/anti-pattern rules |
| Quality gates | `builder/pipeline/enforce_critical.py`, `builder/pipeline/quality_checks.py`, `builder/pipeline/rust_cargo_check.py` | semantic + placeholder + cargo checks |
| Builder tests | `builder/tests/` | pytest with custom `snapshot_utils.py` |
| Rust adapters | `nautilus-dinger/crates/adapters/` | repeated `common/http/websocket/python` layout |
| Python adapters | `nautilus-dinger/nautilus_adapter/adapters/` | per-exchange client/config/factory modules |

## CONVENTIONS
- CLI source of truth is `builder/cli.py`; package entrypoints (`builder`, `dinger`, `nautilus-dinger`) route through `nautilus-dinger/nautilus_adapter/cli.py`.
- Pipeline defaults to incremental/per-file generation and entropy-managed retries.
- Validation order is schema/critical fields → quality checks → AST/cargo checks → snapshot compare.
- Exchange directories are mostly PascalCase in adapters (`ApexOmni`, `O1xyz`) and snake/lower in snapshots/research files.
- Test execution is split: Python builder tests at repo root pathing, Rust tests from nested workspace.

## ANTI-PATTERNS (THIS PROJECT)
- Do not use `reqwest` in generated Rust adapters; prompts enforce hyper stack usage.
- Do not omit `venue_id` in research outputs; use uppercase exchange name fallback when docs lack it.
- Do not run snapshot mutation flows in CI-style validation.
- Do not assume `builder/` is a standalone installable package; import path is anchored by wrapper scripts.

## UNIQUE STYLES
- Strong template-first generation with smart placeholders and per-file healing retries.
- Large committed snapshot tree under `builder/snapshots/*` mirrors generated Rust/Python outputs.
- Nested monorepo boundary: root Python tooling + nested package/workspace (`nautilus-dinger/`).
- Auth-scraper contains temporary/vendor-like trees (`temp_*`, `venv/`) that are not primary product code.

## COMMANDS
```bash
# Full exchange pipeline
python3 -m builder.cli pipeline <exchange>

# Research + generation
python3 -m builder.cli research --exchange <name> --url <docs_url>
python3 -m builder.cli generate builder/research/<exchange>.yaml --language rust --snapshots builder/snapshots/<exchange>/rust

# Builder tests
cd builder && python3 -m pytest tests/

# Workspace tests
cd nautilus-dinger && make test
cd nautilus-dinger && cargo test
```

## NOTES
- No `.github/workflows/` currently; CI orchestration is manual via CLI/Makefile.
- Root has `rustfmt.toml`; no root `pyproject.toml` for `builder/` package metadata.
- `nautilus-dinger/nautilus_adapter/cli.py` uses `sys.path` manipulation to import from root-level `builder`.
- Existing `builder/pipeline/AGENTS.md` is deep and module-specific; keep it as the pipeline-local authority.
