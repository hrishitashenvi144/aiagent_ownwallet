# AuditAgent Analysis Engine (Person 2)

This package implements the containerized static analysis sandbox, multi-analyzer normalizer (Slither, Aderyn), LLM triage filter, Foundry PoC fuzz test generator, and secondary reviewer agent microservice.

## Directory Structure
- `analysis/`: Core Python package:
  - `runner.py`: Orchestrates sandboxed static execution and report generation.
  - `mock_runner.py`: Deterministic mock returning schema-compliant test reports for Day 1 development.
  - `normalizer.py`: Transforms raw Slither and Aderyn JSON outputs to `Finding` schema.
- `tests/`: Pytest unit and integration test suite.
- `Dockerfile`: Isolated execution container configured with no network access and strict resource boundaries.

## Sandbox Execution & Commands
```bash
# Build sandbox Docker image
docker build -t auditagent-analysis-sandbox:latest .

# Run tests
pytest tests/ -v

# Run mock analysis
python -c "from analysis.mock_runner import get_mock_report; print(get_mock_report('job-123'))"
```
