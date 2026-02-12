# NAUTILUS-DINGER KNOWLEDGE BASE

## OVERVIEW
`nautilus-dinger/` contains the nested Python package and Rust workspace for exchange adapters consumed by NautilusTrader.

## STRUCTURE
```
nautilus-dinger/
├── pyproject.toml                # Python package + CLI entry points
├── Cargo.toml                    # Rust workspace
├── nautilus_adapter/             # Python package source
│   └── adapters/                 # Per-exchange Python adapters
├── crates/
│   └── adapters/                 # Per-exchange Rust crates
├── scripts/                      # Runtime/check scripts (Paradex-focused)
└── tests/                        # Python adapter smoke/import tests
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Python CLI entrypoints | `nautilus-dinger/pyproject.toml`, `nautilus-dinger/nautilus_adapter/cli.py` | `builder`/`dinger`/`nautilus-dinger` aliases |
| Rust workspace boundaries | `nautilus-dinger/Cargo.toml` | members under `crates/adapters/*` |
| Adapter runtime scripts | `nautilus-dinger/scripts/` | canary/assert/strategy helpers |
| Combined test entry | `nautilus-dinger/Makefile` | pytest + cargo test |

## CONVENTIONS
- This directory is a nested package/workspace boundary, not the generation source.
- Adapter module layouts are repeated per exchange in Rust and Python trees.

## ANTI-PATTERNS
- Do not use `nautilus-dinger/target/` artifacts for architectural decisions.
- Do not duplicate generator logic here; keep it in `builder/`.
