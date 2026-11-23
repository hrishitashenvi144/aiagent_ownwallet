# AuditAgent Master Build Guide

This master guide provides the holistic step-by-step roadmap for all 4 team members across the entire 10-week development cycle.

---

## 1. System Architecture & Component Mapping

```
                                      [ Customers & Web3 Users ]
                                                  │
                                                  ▼
                                       ┌─────────────────────┐
                                       │ dashboard/ (Nextjs) │ (Person 4)
                                       └──────────┬──────────┘
                                                  │ (HTTP / JSON / OpenAPI)
                                                  ▼
                                       ┌─────────────────────┐
                                       │ agent/ (FastAPI)    │ (Person 3)
                                       └─────┬─────────┬─────┘
                                             │         │
                 ┌───────────────────────────┘         └───────────────────────────┐
                 │ (Execute analysis jobs)                                         │ (Verify payment / execute session tx)
                 ▼                                                                 ▼
      ┌───────────────────────┐                                         ┌─────────────────────┐
      │ analysis/ (Docker)    │ (Person 2)                              │ contracts/ (Foundry)│ (Person 1)
      │ - Slither & Aderyn    │                                         │ - AgentWallet       │
      │ - LLM Triage          │                                         │ - Escrow            │
      │ - Reviewer Agent      │                                         │ - Reputation        │
      └───────────────────────┘                                         └─────────────────────┘
```

---

## 2. Phase-by-Phase Master Execution Plan

### Phase 1: Environment Setup & Shared Contracts (Week 1 - 2)
1. **Repository Bootstrap**:
   - Clone repository, run `scripts/setup.sh` or `scripts/setup.ps1`.
   - Copy `.env.example` to `.env` and configure local development variables.
2. **Interface Baseline**:
   - Person 1 exports initial stub ABIs to `shared/abis/`.
   - Person 2 and Person 3 lock schemas in `shared/schemas/` and endpoints in `shared/openapi.yaml`.
   - Person 4 sets up Next.js mock client using `NEXT_PUBLIC_USE_MOCK=true`.

### Phase 2: Core Module Implementation (Week 3 - 4)
- **Person 1 (Contracts)**: Implement `AgentWallet.sol` with session keys and expenditure caps. Write comprehensive unit tests in Foundry. Deploy to Base Sepolia testnet.
- **Person 2 (Analysis)**: Build Docker sandbox with Slither and Aderyn. Build normalizer pipeline converting raw tool findings to `Finding` objects.
- **Person 3 (Agent Core)**: Implement FastAPI routes (`POST /quote`, `POST /jobs`, `GET /jobs/{id}`). Implement x402 payment flow with `web3.py`.
- **Person 4 (Dashboard)**: Build customer portal with contract editor, pricing display, and wagmi wallet integration for Base Sepolia testnet USDC.
- **Checkpoint (End of Week 4)**: Milestone 1 reached. Contracts deployed on testnet; mock-to-real swap initiated.

### Phase 3: Integration & End-to-End Pipeline (Week 5 - 6)
- **Person 1**: Implement `Escrow.sol` for peer reviewer payouts. Write fuzz tests for boundary conditions.
- **Person 2**: Implement LLM triage and false-positive filter. Implement LLM-synthesized Foundry fuzz tests. Prototype peer reviewer microservice.
- **Person 3**: Implement async background worker queue. Connect agent to containerized analysis runner. Implement dynamic quoting brain.
- **Person 4**: Build Owner View dashboard (balance telemetry, reasoning log, emergency kill switch). Scaffold adversarial attack test suite.
- **Checkpoint (End of Week 6)**: Milestone 2 reached. A user can submit Solidity code, pay testnet USDC, have the contract analyzed in Docker, and receive a completed report.

### Phase 4: Decentralized Multi-Agent & Dashboard Polish (Week 7 - 8)
- **Person 1**: Implement `ReputationRegistry.sol`. Optimize gas usage on all contracts and commit gas report.
- **Person 2**: Connect peer reviewer agent to Escrow contract. Assemble benchmark suite from SWC and Damn Vulnerable DeFi contracts.
- **Person 3**: Wire Escrow subcontracting logic into `deep` scan mode in the economic brain. Implement owner pause signature verification.
- **Person 4**: Connect frontend to live Agent Core and Base Sepolia contracts. Wire owner emergency pause button.
- **Checkpoint (End of Week 8)**: Milestone 3 reached. Multi-agent escrow and complete dashboard fully integrated.

### Phase 5: Security Auditing, Benchmarks & Finalization (Week 9 - 10)
- **Person 1**: Run Slither on our own contracts, fix all identified issues, and finalize deployment documentation.
- **Person 2**: Execute benchmark test suite, collect accuracy/recall metrics, and generate comparison charts.
- **Person 3**: Hardening, error handling, transaction retry logic, and performance profiling.
- **Person 4**: Run full adversarial security attack suite (prompt injections, malicious code escapes, fake payment proofs). Finalize presentation slides and demo script.
- **Checkpoint (End of Week 10)**: Milestones 4 & 5 reached. Live demo execution and codebase freeze.

---

## 3. Communication & Code Review Protocol

1. Feature branches (`feat/contracts`, `feat/analysis`, `feat/agent-core`, `feat/dashboard`) merge into `develop` only via Pull Requests.
2. PRs must pass GitHub Actions CI checks before being reviewed.
3. Every merge into `develop` must be preceded by a local rebase from `origin/develop`.
4. Lead Engineer verifies each integration gate following `docs/MERGE_PLAN.md`.
