# Nautilus Dinger

Automated NautilusTrader adapter generation using LLMs.

## Setup

1. Install dependencies:
   ```bash
   pip install -e .
   ```
2. Set up environment:
   ```bash
   cp .env.example .env
   # Add your OpenAI API key to .env
   ```

## Usage

1. **Research**: Create a markdown file in `research/` with exchange details (use the template).
2. **Generate**: Run the pipeline:
   ```bash
   nautilus-dinger run research/hyperliquid.md
   ```

## Structure

- `nautilus_adapter/`: Core package
- `research/`: Exchange research documents
- `scripts/`: Helper scripts
- `tests/`: Project tests
