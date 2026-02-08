# BUILDER PIPELINE KNOWLEDGE BASE

**Generated:** 2026-02-08

## OVERVIEW
LLM-driven adapter generation system with 6-phase gated workflow, entropy management, and multi-language code generation.

## STRUCTURE
```
builder/pipeline/
├── ast/              # AST validation (Python/Rust)
├── prompts/           # LLM prompt templates
├── utils/             # Helper utilities (AST, entropy)
├── models.py          # Pydantic ExchangeResearch models
├── generate.py         # LLM code generation with entropy guards
├── run_codegen.py      # Main orchestration with validation pipeline
├── retry.py           # Global retry logic with temperature decay
├── retry_per_file.py  # Per-file self-healing with entropy tracking
├── entropy.py          # EntropyPolicy for temperature management
├── entropy_state.py   # FileEntropyState for per-file tracking
├── guards.py           # EntropyViolation and ASTViolation guards
├── enforce_critical.py # Critical field validation
├── rust_cargo_check.py # Cargo check with auto mod.rs generation
├── snapshot.py        # Snapshot regression detection
├── snapshot_write.py  # Snapshot persistence
├── schema_walk.py     # Schema-driven prompt generation
├── exceptions.py       # BuilderError hierarchy
└── rag_ingest.py       # RAG ingestion for context
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| **LLM generation** | `generate.py`, `run_codegen.py` | Entropy guards, multi-sample strategy |
| **Validation pipeline** | `ast/validate_strict.py`, `rust_cargo_check.py` | AST validation, Cargo check, semantic gates |
| **Retry logic** | `retry.py`, `retry_per_file.py` | Temperature decay, per-file entropy tracking |
| **Snapshot system** | `snapshot.py`, `snapshot_write.py` | Custom regression testing (not syrupy) |
| **Prompts** | `prompts/research_prompt.py`, `prompts/rust_codegen_prompt.py` | Schema-driven generation |

## CODE MAP
| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `generate_with_guards()` | function | `generate.py` | Multi-sample entropy-based generation |
| `run_codegen()` | function | `run_codegen.py` | Main orchestration loop |
| `Entropolicy` | class | `entropy.py` | Temperature management (0.0 → 0.3) |
| `FileEntropyState` | class | `entropy_state.py` | Per-file temperature tracking |
| `BuilderError` | class | `exceptions.py` | Base exception hierarchy |
| `validate_ast_strict()` | function | `ast/validate_strict.py` | Python/Rust AST validation dispatcher |
| `rust_cargo_check()` | function | `rust_cargo_check.py` | Cargo validation with auto mod.rs generation |

## CONVENTIONS

### Validation Gates (Sequential)
1. **Pydantic Schema**: Validates YAML structure against `config/schema.yaml`
2. **Semantic Gate** (`enforce_critical.py`): Critical fields (venue_id, rest_base_url, auth_type, price_precision, quantity_precision) cannot be `UNKNOWN`
3. **AST Validation** (`ast/validate_strict.py`): Checks Python/Rust syntax before writing
4. **Cargo Check** (`rust_cargo_check.py`): Verifies Rust compilation, lifetimes, traits (ignores E0432/E0433)
5. **Entropy Guard** (`guards.py`): Enforces `min_similarity 0.97` with temperature decay on violation
6. **Snapshot Diff** (`snapshot.py`): Regression detection against golden snapshots

### Entropy Management Strategies

**Global Entropy** (`generate.py`):
- Samples N outputs (default: 1, configurable)
- Returns best output if similarity threshold met
- If violation: decay temperature by 0.85 factor and retry

**Per-File Entropy** (`retry_per_file.py`):
- Tracks failures per file in `FileEntropyState`
- Selective regeneration: only failed files get re-generated
- Temperature ramps from 0.0 → 0.3 (step 0.05)
- Preserves stable code (never regenerates)

### LLM Configuration
- **Provider**: OpenAI gpt-4-turbo-preview (configurable via `config/pipeline.yaml`)
- **Extraction Temp**: 0.0 (deterministic)
- **Generation Temp**: 0.15 (with decay to 0.3)
- **Similarity Threshold**: 0.97 (strict text similarity)
- **Max Attempts**: 4 (configurable)
- **Caching**: Enabled (`infra/llm_cache.py`)

### Error Handling Hierarchy
```
BuilderError (base)
├── CriticalFieldError (missing critical fields)
├── CodegenFailure (generation failed)
├── SnapshotMismatch (regression detected)
└── CargoCheckError (Rust compilation failed)

Custom Errors:
├── EntropyViolation (similarity threshold failed)
└── ASTViolation (syntax/structure error)
```

## ANTI-PATTERNS (THIS PROJECT)
- **DO NOT** use `reqwest` - it is not a dependency. Use `hyper 1.2`, `hyper-util 0.1`, `hyper-rustls 0.26`
- **DO NOT** use `nautilus_core` - it is not a dependency. Use `nautilus_common` or `nautilus_model`
- **Critical**: ALWAYS provide `venue_id` in research. If not found, use UPPERCASE exchange name

## UNIQUE STYLES
- **Self-healing codegen**: Per-file entropy tracking ensures only broken files are regenerated, stable code preserved
- **Dual entropy strategies**: Global multi-sample for initial output + per-file retry with temperature decay
- **Strict similarity enforcement**: 0.97 threshold prevents random generation, ensures reproducibility
- **Auto mod.rs generation**: `rust_cargo_check.py` automatically creates mod.rs files for missing directories
- **Custom snapshot system**: Uses `UPDATE_SNAPSHOTS` env var for golden master management (not external libraries)
- **Schema-driven prompts**: All codegen prompts generated from YAML schema via `schema_walk.py`
- **Feature-gated compilation**: Rust templates use `#[cfg(feature = "...")]` to enable/disable python/data/execution modules
- **Placeholder consistency**: Smart placeholder system (`{{EXCHANGE_NAME}}`, `{{EXCHANGE_UPPER}}`, etc.) ensures cross-language alignment

## COMMANDS
```bash
# Run full 6-phase pipeline
python -m builder.cli pipeline <exchange>

# Generate research prompt
python -m builder.cli research --exchange <name> --url <docs_url>

# Generate adapters from research
python -m builder.cli generate <research_file> --language rust --snapshots builder/snapshots/<exchange>/rust

# Validate generated code
python -m builder.cli snapshot <exchange> --check

# Run pipeline tests
cd builder && python -m pytest tests/
```

## NOTES
- **No external dependencies**: Uses OpenAI SDK directly via `infra/llm.py` (not LangChain)
- **Pipeline configuration**: All LLM settings in `builder/config/pipeline.yaml` (temperature, sampling, retry, cache)
- **Research schema**: Exchange specification defined in `builder/config/schema.yaml` with Pydantic models
- **Placeholder system**: Unified across Rust and Python templates for consistency
- **Critical field enforcement**: `venue_id` is mandatory - default to UPPERCASE exchange name if missing
- **Cargo check ignores**: E0432/E0433/E0412 errors expected (unresolved imports during generation)
- **Snapshot management**: Golden snapshots in `builder/snapshots/` directory structure matches generated output
