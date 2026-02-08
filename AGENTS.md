# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-08
**Commit:** N/A
**Branch:** N/A

## OVERVIEW
Nautilus-Dinger: LLM-driven NautilusTrader adapter generation system for crypto exchanges (Rust core + Python bindings)

## STRUCTURE
```
./
├── builder/           # Code generation pipeline
│   ├── pipeline/      # LLM orchestration, validation, retry
│   ├── templates/    # Adapter templates (Rust+Python)
│   ├── tests/         # Pipeline tests
│   ├── config/        # Pipeline & schema configs
│   └── docs/          # Documentation
├── nautilus-dinger/  # Rust workspace (adapters: Nado, Lighter)
│   ├── crates/adapters/{Exchange}/
│   └── nautilus_adapter/adapters/{Exchange}/  # Python bindings
└── scripts/           # Utility scripts
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| **Run full pipeline** | `python -m builder.cli pipeline <exchange>` | 6-phase workflow (doctor → research → scaffold → generate → snapshot) |
| **Generate research prompt** | `python -m builder.cli research --exchange <name>` | Emits schema-driven research prompt |
| **Generate adapters** | `python -m builder.cli generate <research_file>` | LLM code generation with entropy guards |
| **Template structure** | `builder/templates/rust_crate_template/` | Rust crate template with smart placeholders |
| **Pipeline configuration** | `builder/config/pipeline.yaml` | LLM provider, temperature, sampling, retry settings |
| **Research schema** | `builder/config/schema.yaml` | Exchange specification YAML structure |
| **Python bindings** | `nautilus_adapter/adapters/{Exchange}/` | NautilusTrader integration layer |
| **Rust core** | `crates/adapters/{Exchange}/src/` | Hyper 1.2 HTTP, tokio WebSocket, PyO3 bindings |
| **Test patterns** | `builder/tests/` | pytest with LLM mocking, snapshot regression |

## CONVENTIONS
- **Pipeline phases**: 6-phase gated workflow (doctor, research, scaffold, generate, snapshot, healing, CI)
- **Entropy management**: Global sampling (min_similarity 0.97) + per-file retry with temperature decay
- **Validation gates**: Pydantic schema → semantic gates → AST validation → cargo check → snapshot diff
- **Smart placeholders**: `{{EXCHANGE_NAME}}`, `{{EXCHANGE_UPPER}}`, `{{REST_URL_MAINNET}}` for cross-language consistency
- **Feature gates**: Rust modules conditional on `python`, `data`, `execution` features
- **Error handling**: Custom BuilderError hierarchy (CriticalFieldError, CodegenFailure, SnapshotMismatch, CargoCheckError)
- **Naming**: Exchange names PascalCase (Binance, Lighter), lowercase directories (binance, lighter)
- **Credentials**: Environment variable resolution (`LIGHTER_API_KEY`, `{EXCHANGE_UPPER}_API_SECRET`)
- **Rust patterns**: Hyper 1.2 (no reqwest), tokio full features, pyo3 0.20 for bindings
- **Python patterns**: async/await consistent, Pydantic config, msgspec Struct for high-performance decoding

## ANTI-PATTERNS (THIS PROJECT)
- **Forbidden**: DO NOT use `reqwest` - it is not a dependency. Use `hyper 1.2`, `hyper-util 0.1`, `hyper-rustls 0.26`
- **Forbidden**: DO NOT use `nautilus_core` - it is not a dependency. Use `nautilus_common` or `nautilus_model`
- **Critical**: ALWAYS provide `venue_id` in research. If not found, use UPPERCASE exchange name
- **CLI routing**: The actual CLI is at `builder/cli.py`; `nautilus-dinger/nautilus_adapter/cli.py` is a minimal wrapper that manipulates sys.path to import from parent

## UNIQUE STYLES
- **Template-driven architecture**: All adapters derive from `builder/templates/rust_crate_template/` with unified placeholder system
- **Self-healing codegen**: Per-file entropy tracking; only regenerate broken files, preserve stable code
- **Dual entropy strategies**: Global multi-sample generation for initial output + per-file retry with temperature decay
- **Snapshot regression**: Custom `snapshot_utils.py` with `UPDATE_SNAPSHOTS` env var control (not syrupy/snapshot-testing)
- **Deep module nesting**: Rust templates use 10-11 level depth (src/common/risk/ is deepest)
- **Conditionally compiled features**: Rust modules enable/disable via Cargo features (`python`, `data`, `execution`, `test_utils`)
- **Workspace pattern**: Rust workspace is nested in `nautilus-dinger/crates/` (not at project root)
- **Mixed monorepo**: Python builder at root, Rust workspace in `nautilus-dinger/`, Python adapters in `nautilus_adapter/adapters/`

## COMMANDS
```bash
# Run full pipeline
python -m builder.cli pipeline <exchange>

# Generate research prompt only
python -m builder.cli research --exchange <name> --url <docs_url>

# Generate adapters from research file
python -m builder.cli generate <research_file> --language rust --snapshots builder/snapshots/<exchange>/rust

# Run builder tests (Python pytest)
cd builder && python -m pytest tests/

# Run Rust tests (workspace)
cd nautilus-dinger && cargo test

# Run all tests (orchestrated)
cd nautilus-dinger && make test  # runs pytest ../builder/tests/ and cargo test
```

## NOTES
- **No root package config**: The `builder/` directory has no `pyproject.toml` at project root. The Python package is defined in `nautilus-dinger/pyproject.toml` (name: `nautilus_adapter`)
- **Import path issue**: `nautilus-dinger/nautilus_adapter/cli.py` manually adds `sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))` to import from `builder/cli.py` - this is fragile
- **Nado Cargo.toml corruption**: `/nautilus-dinger/crates/adapters/Nado/Cargo.toml` contains dependency tracking content instead of Cargo manifest
- **Snapshot management**: Golden snapshots are in `builder/snapshots/` but directory is mostly empty; snapshot system ready for use
- **CLI aliases**: Three CLI commands map to same entry point: `builder`, `dinger`, `nautilus-dinger` (all → `nautilus_adapter.cli:main`)
- **Template files committed**: `builder/templates/rust_crate_template/` and `builder/templates/python_adapter_template/` are in version control - should be gitignored?
- **No CI/CD**: No `.github/workflows/` directory exists despite having tests in both Python and Rust
- **Missing lint configs**: No `.ruff.toml`, `.pre-commit-config.yaml`, or `rustfmt.toml` - code generation quality depends on manual review
- **Mixed language boundary**: Python and Rust integration via PyO3 - Python layer uses NautilusTrader types, Rust core uses NautilusModel types
- **Workspace member pattern**: Cargo workspace includes only `crates/adapters/*` - no shared library crate
- **Feature parity**: Python modules exist unconditionally in `nautilus_adapter/`, but Rust equivalents are feature-gated in templates
