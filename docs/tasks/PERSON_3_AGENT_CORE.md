# Person 3: Agent Core, Economic Brain & x402 Paywall

## 1. Role Summary & Folder Ownership
- **Role Summary**: You build the core autonomous orchestrator of AuditAgent. You are responsible for the FastAPI REST gateway, the HTTP 402 "Payment Required" paywall, on-chain payment verification via `web3.py`, the SQLite job database, the background worker, and the economic brain that optimizes pricing, scan depths, and agent profit margins.
- **Branch**: `feat/agent-core`
- **Owned Folders & Files**:
  - `agent/` (all FastAPI application code, database models, worker queues, web3 connectors)
- **MUST NOT EDIT**:
  - `contracts/` (Person 1)
  - `analysis/` (Person 2)
  - `dashboard/` (Person 4)
  - `shared/schemas/` (Requires Lead RFC)

---

## 2. Interfaces You Implement & Consume
- **Implement**:
  - All endpoints specified in `shared/openapi.yaml`:
    - `POST /quote`: Calculate price based on code size and depth tier.
    - `POST /jobs`: Accept job submissions; enforce HTTP 402 when unpaid; verify payment when proof is supplied.
    - `GET /jobs/{id}`: Return job lifecycle state.
    - `GET /jobs/{id}/report`: Return finished report.
    - `GET /agent/status`: Return treasury balance, daily spent, and pause flag.
    - `POST /owner/pause`: Process owner signature to toggle agent pause state.
- **Consume**:
  - `analysis.runner.run_analysis` (from Person 2; mock first, real in Week 4).
  - Contract ABIs in `shared/abis/` (`AgentWallet.json`, `Escrow.json`) via `web3.py` on Base Sepolia.
- **Reference**: Detailed specs are in [INTERFACES.md](../INTERFACES.md).

---

## 3. Dependencies & Mocks
- **Before Person 1 deploys contracts**: Use local Anvil stub contracts or `agent/tests/mock_web3.py` for transaction receipt verification.
- **Before Person 2 finishes Docker analysis**: Use `analysis/analysis/mock_runner.py` for job worker testing.
- **Person 4 depends on you**: Person 4 needs your API endpoints to build the dashboard. Keep `agent/agent/mock_server.py` functioning from Day 1.

---

## 4. Week-by-Week Task Checklist (10 Weeks)

### Week 1: FastAPI Scaffold & SQLite Job Database
- [ ] Initialize FastAPI project with SQLAlchemy models in `agent/agent/models.py` (`Job`, `Quote`, `TransactionRecord`). *(Est: 5h)*
  - *Done When*: SQLite DB initializes tables successfully upon service startup.
- [ ] Create `agent/agent/mock_server.py` returning static responses according to `shared/openapi.yaml` for Person 4. *(Est: 3h)*
  - *Done When*: Dashboard can fetch mock quotes and job reports.

### Week 2: x402 Paywall & Quoting Engine
- [ ] Implement `POST /quote` calculating dynamic USDC price based on source line count, scan tier (`quick`/`standard`/`deep`), and gas price. *(Est: 5h)*
  - *Done When*: Endpoint returns valid `Quote` object adhering to `shared/schemas/quote.json`.
- [ ] Implement x402 response on `POST /jobs` returning HTTP 402 with `X-Accept-Token`, `X-Payment-Address`, and `X-Required-Amount` headers when payment is missing. *(Est: 5h)*
  - *Done When*: Unpaid submissions return status code 402 and payment instructions.

### Week 3: On-Chain Payment Verification with web3.py
- [ ] Implement `agent/agent/payment_verifier.py` using `web3.py` to query Base Sepolia RPC. *(Est: 6h)*
  - *Done When*: Verifier confirms recipient matches `AGENT_WALLET_ADDRESS`, token matches USDC, amount matches quote, and logs contain `job_id`.
- [ ] Prevent replay attacks by asserting transaction hashes are unique in the database. *(Est: 4h)*
  - *Done When*: Submitting an already used transaction hash rejects with HTTP 409.

### Week 4: Background Job Worker & Milestone 1 Integration
- [ ] Implement async background job queue in `agent/agent/worker.py` polling SQLite for `paid` jobs and launching analysis. *(Est: 6h)*
  - *Done When*: Job status automatically transitions from `paid` -> `analyzing` -> `delivered`.
- [ ] Swap `mock_runner` with Person 2's containerized `run_analysis` engine. *(Est: 4h)*
  - *Done When*: Real analysis execution succeeds end-to-end on test contract.

### Week 5: Economic Brain (Cost vs. Payment Optimization)
- [ ] Implement `agent/agent/economic_brain.py` modeling token cost vs. payment received to maximize profit margin. *(Est: 6h)*
  - *Done When*: Brain computes net gross profit per job and records telemetry in DB.
- [ ] Implement spend-or-skip logic: If estimated analysis costs exceed customer payment, adjust scan depth safely or trigger refund. *(Est: 4h)*
  - *Done When*: Unprofitable jobs are gracefully handled.

### Week 6: End-to-End Paid Job Integration (Milestone 2)
- [ ] Integrate full pipeline from `POST /quote` -> `POST /jobs` (with payment) -> worker analysis -> report persistence. *(Est: 7h)*
  - *Done When*: End-to-end integration test passes in `agent/tests/test_e2e.py`.

### Week 7: Multi-Agent Escrow Coordination
- [ ] Add escrow interaction module using `web3.py` and session key to invoke `createEscrow` on `Escrow.sol` for `deep` tier jobs. *(Est: 6h)*
  - *Done When*: Agent wallet deposits bounty to escrow contract when hiring peer reviewer.
- [ ] Verify secondary reviewer report hash and trigger `releaseEscrow`. *(Est: 4h)*
  - *Done When*: Bounty is released upon consensus delivery.

### Week 8: Owner Telemetry & Emergency Pause Implementation
- [ ] Implement `GET /agent/status` returning live treasury balance, daily spent, active job count, and uptime. *(Est: 4h)*
  - *Done When*: Owner dashboard visualizes live financial and operational metrics.
- [ ] Implement `POST /owner/pause` with ECDSA signature verification to pause/unpause agent operations. *(Est: 5h)*
  - *Done When*: Invalid signatures return 403; valid owner signature pauses agent execution.

### Week 9: System Hardening & Resilience
- [ ] Implement exponential backoff for Base Sepolia RPC calls and LLM API requests. *(Est: 5h)*
  - *Done When*: System recovers smoothly from temporary RPC drops without dropping jobs.
- [ ] Write integration recovery tests: verify crashed analysis jobs restart or issue customer refunds. *(Est: 4h)*
  - *Done When*: Zero stuck jobs in `analyzing` state.

### Week 10: Performance Profiling, Viva & Code Freeze
- [ ] Measure API latency, DB query performance, and ensure clean logs for presentation. *(Est: 5h)*
  - *Done When*: Agent service runs stably with zero memory leaks during extended demo run.

---

## 5. Suggested LLM Prompts
- **For Week 2 (HTTP 402 Paywall)**:
  > *"Write a FastAPI route for POST /jobs. If the request does not include the X-Payment-Proof header with a valid transaction hash, return an HTTP 402 Payment Required response containing custom headers X-Payment-Address, X-Required-Amount, and X-Accept-Token, plus a JSON body with payment instructions."*
- **For Week 3 (web3.py Payment Verification)**:
  > *"Write a Python class PaymentVerifier using web3.py. Given a tx_hash, RPC URL, agent_wallet_address, usdc_contract_address, expected_amount, and expected_job_id, verify that the transaction succeeded on-chain, transferred at least expected_amount USDC to agent_wallet_address, and contained expected_job_id in calldata. Return boolean."*
- **For Week 5 (Economic Brain)**:
  > *"Write an EconomicBrain class that estimates the cost of an audit job based on Solidity source line count, estimated LLM token usage, and static analysis compute time. Compute dynamic quote price in USDC targeting a 40% profit margin."*

---

## 6. Common Pitfalls & Security Notes
1. **Replay Attacks**: Always enforce that every payment transaction hash can only be redeemed once in the SQLite database.
2. **Chain Reorgs & Unconfirmed Txs**: Wait for at least 1-2 block confirmations on Base Sepolia before marking a job as `paid`.
3. **Session Key Safety**: Store session private keys in memory or secure environment variables; never log them or expose them via API endpoints.
