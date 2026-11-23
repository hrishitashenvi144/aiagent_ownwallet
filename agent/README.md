# AuditAgent Core Service (Person 3)

This package contains the core FastAPI application orchestrating job lifecycle, x402 payment requirements, on-chain Base Sepolia verification via `web3.py`, SQLite job persistence, and the autonomous economic brain.

## Endpoints Implemented
- `POST /quote`: Calculate dynamic USDC price quote.
- `POST /jobs`: Create audit job. Emits HTTP 402 ("Payment Required") when unverified; verifies `X-Payment-Proof` header.
- `GET /jobs/{id}`: Fetch job lifecycle status (`created`, `quoted`, `paid`, `analyzing`, `delivered`, `failed`).
- `GET /jobs/{id}/report`: Fetch ranked security triage report.
- `GET /agent/status`: Fetch treasury balance, daily allowance, active jobs, and pause state.
- `POST /owner/pause`: Owner signature verification to toggle emergency stop.

## Running Locally
```bash
# Run FastAPI server locally on port 8000
uvicorn agent.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
pytest tests/ -v
```
