.PHONY: run test benchmark
run:
	uvicorn evidencecheck.server:app --reload --host 127.0.0.1 --port 8000

test:
	pytest

benchmark:
	PYTHONPATH=. python scripts/benchmark.py
