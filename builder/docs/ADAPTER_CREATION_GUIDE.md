# Master Guide: Building NautilusTrader Adapters (Nautilus Dinger)

This guide documents the standardized, high-discipline workflow for building production-ready exchange adapters using the **Nautilus Dinger** builder.

## Workflow Overview

The creation process follows a strict 6-phase pipeline designed to eliminate "guessed" behavior and ensure regression safety.

1.  **Phase 0: Doctor** — Environment verification.
2.  **Phase 1: Research** — Prompt generation for exchange discovery.
3.  **Phase 2: Spec** — Validated research output (YAML).
4.  **Phase 3: Generate** — Code generation with AST and Semantic validation.
5.  **Phase 4: Snapshot** — Creating regression baselines.
6.  **Phase 5/6: Healing & CI** — Self-healing retries and regression detection.
7.  **Smart Placeholders** — Using `{{EXCHANGE_NAME}}` and URL placeholders for cross-language consistency.

---

## 🛠 Setup & Phase 0: Environment Verification

**Important**: Always run commands from the project root.

```bash
# Verify your environment (rustc, cargo, OPENAI_API_KEY)
python3 -m builder.cli doctor

# If tools are missing, see fix instructions:
python3 -m builder.cli doctor --fix
```

---

## 🔍 Phase 1 & 2: Research & Spec

### 1. Generate Research Prompt
Generate a schema-driven research task. This automatically includes the exchange context and saves to a file.

```bash
nautilus-dinger research-auto --exchange Lighter --url https://apidocs.lighter.xyz/docs/get-started --save
```
*Creates: `Research_task_Lighter.txt`*

### 2. Gather Data
Feed the prompt to an LLM or researcher. The output must be saved as a **YAML** file.

**Location**: `builder/research/okx.yaml`

**Rules**:
- Must conform to `builder/config/schema.yaml`.
- Critical fields (endpoints, auth methods) must NOT be `UNKNOWN`.

---

## 🚀 Phase 3: Code Generation (CI-Safe)

Generate the adapter implementation. This phase is deterministic (Temp=0) and performs multiple validation gates.

### Generate Python Layer
```bash
python3 -m builder.cli generate builder/research/okx.yaml \
  --language python \
  --snapshots builder/snapshots/okx/python
```

### Generate Rust Core
```bash
python3 -m builder.cli generate builder/research/okx.yaml \
  --language rust \
  --snapshots builder/snapshots/okx/rust
```

### 🛡 Validation Gates:
1.  **Pydantic**: Validates research YAML structure.
2.  **Semantic Gate**: Enforces that critical fields are present.
3.  **AST Validation**: Checks syntax for Python/Rust.
4.  **Cargo Check**: Verifies lifetimes, traits, and module wiring for Rust.
5.  **Snapshot Diff**: Ensures no regression against known-good code.

---

## 📸 Phase 4: Snapshot Management

When you intentionally change a template or the research spec, you must update the "Golden Snapshots".

```bash
# Update snapshots (intentional mutation)
python3 -m builder.cli snapshot builder/research/okx.yaml \
  --language rust \
  --snapshots builder/snapshots/okx/rust
```

*Note: Never run `snapshot` in CI. Snapshots are your "Git Add" for generated code.*

---

## 🩹 Phase 5: Self-Healing & Entropy

The builder uses a **Per-File Entropy Retry Loop**:
- If a file fails AST or Cargo Check, the builder identifies the specific failure.
- It retries *only* the broken files, slightly increasing LLM temperature (max 0.3).
- Stable files are never regenerated, ensuring consistency.

---

## ✅ Phase 6: Human Completion Checklist

The generated code is a robust core but requires manual signing and domain mapping logic.

### 🦀 Rust Core Checklist
- [ ] **Credential Signing**: Implement `authenticate()` in `src/common/credential.rs`.
- [ ] **WS Lifecycle**: Handle specific `subscribe`/`unsubscribe` JSON in `src/websocket/client.rs`.
- [ ] **Rate Limiting**: Define buckets in `src/http/client.rs`.

### 🐍 Python Layer Checklist
- [ ] **Instrument Provider**: Implement `load_instruments` in `providers.py`.
- [ ] **Factories**: Map complex JSON objects to `nautilus_trader` models.

---

## 🏗 Smart Placeholders Reference

The builder and scaffold system use the following placeholders to ensure consistency:

- `{{EXCHANGE_NAME}}`: PascalCase (e.g., `Binance`, `Hyperliquid`)
- `{{EXCHANGE_UPPER}}`: UPPERCASE (e.g., `BINANCE`, `HYPERLIQUID`)
- `{{EXCHANGE_LOWER}}`: lowercase (e.g., `binance`, `hyperliquid`)
- `{{REST_URL_MAINNET}}`: Full Mainnet REST URL from research.
- `{{REST_URL_TESTNET}}`: Full Testnet REST URL from research.
- `{{WS_URL_PUBLIC}}`: Full Public WebSocket URL from research.

---

## 🏗 CI Workflow
A healthy adapter pipeline looks like this in CI:
```bash
builder doctor --json
builder generate ... --language rust
builder generate ... --language python
pytest
```
