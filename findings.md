# Findings

## Session Summary
`/init-deep` completed with exhaustive discovery (parallel background agents + direct tools) and produced a practical AGENTS hierarchy focused on real module boundaries.

## Key Discoveries

### Repository Shape
- Monorepo split is intentional: `builder/` (generation control plane) + `nautilus-dinger/` (runtime package/workspace).
- Existing deep authority file: `builder/pipeline/AGENTS.md`.

### High-Signal Documentation Boundaries
- `builder/` is where orchestration and policy live.
- `builder/auth-scraper/` is domain-specific and should be isolated from core generation docs.
- `builder/templates/` is canonical for output shape and placeholder policy.
- `builder/snapshots/` is golden regression space, not runtime source.
- `nautilus-dinger/` is runtime/package boundary; adapters split cleanly into Rust and Python trees.

### Adapter Patterns
- Rust adapters follow stable topology (`common/http/websocket/python/data/execution/testing`) with feature gates.
- Python adapters follow stable 7-file exchange layout (`config/constants/data/execution/factories/providers` + `__init__.py`).
- `Paradex` Python adapter is the most complete implementation reference.

### Command Surfaces
- Canonical CLI source: `builder/cli.py`.
- Entrypoint aliases in nested package route to the same CLI (`builder`, `dinger`, `nautilus-dinger`).
- Makefiles split concerns: workspace tests/build vs auth-scraper schema/test commands.

### Noise/Generated Zones (Document Minimally)
- `target/`, `venv/`, `temp_*_pkg/`, cache directories.
- These zones are large but low-value for architectural guidance.

## Produced AGENTS Hierarchy
- Updated: `AGENTS.md`
- Added:
  - `builder/AGENTS.md`
  - `builder/auth-scraper/AGENTS.md`
  - `builder/templates/AGENTS.md`
  - `builder/snapshots/AGENTS.md`
  - `nautilus-dinger/AGENTS.md`
  - `nautilus-dinger/crates/adapters/AGENTS.md`
  - `nautilus-dinger/nautilus_adapter/adapters/AGENTS.md`

## Documentation Style Decisions
- Kept child docs telegraphic and local-scope only.
- Avoided repeating deep pipeline internals already covered by `builder/pipeline/AGENTS.md`.
- Avoided creating AGENTS files in noisy/generated directories.
