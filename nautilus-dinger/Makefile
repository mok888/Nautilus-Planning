.PHONY: install test run-example

install:
	pip install -e .

test:
	PYTHONPATH=../ pytest ../builder/tests/
	cargo test

run-example:
	python scripts/run_generate.py gen Hyperliquid

build-rust:
	cargo build
