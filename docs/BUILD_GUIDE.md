# AuditAgent Master Build Guide

This master guide provides the holistic step-by-step roadmap for all 4 team members across the entire 10-week development cycle, establishing an industry-standard autonomous agentic system on Base Sepolia.

---

## 1. System Architecture & Cognitive Agent Flow

```
                                      [ Customers & Web3 Users ]
                                                  │
                                                  ▼
                                       ┌─────────────────────┐
                                       │ dashboard/ (Nextjs) │ (Person 4: Customer UI & Owner Trace View)
                                       └──────────┬──────────┘
                                                  │ (HTTP / JSON / OpenAPI)
                                                  ▼
                                       ┌─────────────────────┐
                                       │ agent/ (FastAPI)    │ (Person 3: LangGraph Agent Loop & Memory)
                                       │ - Plan->Act->Obs    │
                                       │ - Model Router      │
                                       │ - Tool Dispatcher   │
                                       └─────┬─────────┬─────┘
                                             │         │
                 ┌───────────────────────────┘         └───────────────────────────┐
                 │ (Dispatches Registered Tools in Sandboxes)                      │ (Verifies payment / calls Session Key)
                 ▼                                                                 ▼
      ┌───────────────────────┐                                         ┌─────────────────────┐
      │ analysis/ (Docker)    │ (Person 2: Tool Registry & Verification)│ contracts/ (Foundry)│ (Person 1)
      │ - Slither & Aderyn    │                                         │ - AgentWallet       │
      │ - Mythril Symbolic    │                                         │ - Escrow            │
      │ - Exploit PoC Runner  │                                         │ - Reputation        │
      │ - Eval Harness        │                                         │                     │
      └───────────────────────┘                                         └─────────────────────┘
```

---

## 2. Phase-by-Phase Master Execution Plan

### Phase 1: Environment Setup, Tool Registry & Interfaces (Weeks 1 - 2)
1. **Repository Bootstrap**:
   - Clone repository, run `scripts/setup.sh` or `scripts/setup.ps1`.
   - Copy `.env.example` to `.env` and configure Base Sepolia RPC and API keys.
2. **Interface & Schema Baseline**:
   - Lock `shared/schemas/finding.json` with required `verified: bool` and `poc_path`.
   - Lock `shared/schemas/report.json` with execution trace summary and verified counts.
   - Specify tool contracts in `docs/INTERFACES.md` and OpenAPI endpoints in `shared/openapi.yaml`.
   - Person 1 exports initial stub ABIs to `shared/abis/`.
   - Person 4 scaffolds Next.js dashboard with wagmi v2 and mock data.

### Phase 2: Core Components, Sandbox & State Engine (Weeks 3 - 4)
- **Person 1 (Contracts)**: Implement `AgentWallet.sol` with session keys, spending ceilings (`perTxCap`, `dailyCap`), reserve floor, and vendor allowlist. Deploy to Base Sepolia testnet.
- **Person 2 (Analysis)**: Build non-networked Docker sandbox (`--network none`). Implement `slither_static` and `aderyn_static` runners. Build normalizers producing canonical `Finding` objects.
- **Person 3 (Agent Core)**: Implement the **LangGraph Agent Loop State Machine** (`PLAN` -> `ACT` -> `OBSERVE` -> `REPLAN`). Enforce per-job step limits (10), token limits (100k), and budget limits (70% of quote). Implement `web3.py` payment verification.
- **Person 4 (Dashboard)**: Build customer submission page, dynamic pricing calculator, and x402 Web3 payment modal.
- **Checkpoint (End of Week 4 - Milestone 1)**: Contracts deployed on Base Sepolia; LangGraph state loop verified against mock tools.

### Phase 3: Tool Registry, Verify-Before-Report & Model Routing (Weeks 5 - 6)
- **Person 1**: Implement `Escrow.sol` for peer reviewer payouts. Write fuzz tests asserting timeout refund safety.
- **Person 2**: Implement **Verify-Before-Report** pipeline: Integrate strong reasoning model (Claude 3.5 Sonnet) to synthesize runnable Foundry exploit PoC tests (`testExploit()`) for Critical/High findings; execute via `exploit_poc_runner` tool. Unverified findings demoted to Low confidence. Add `mythril_symbolic` runner.
- **Person 3**: Implement dynamic **Model Router** (cheap Haiku/mini for AST triage; strong Sonnet/4o for exploit synthesis). Implement **Persistent Agent Memory** (`job_outcomes`, `tool_precision_matrix`, `tier_cost_history`) in SQLite. Implement structured output validation with retry loop.
- **Person 4**: Build **Observability Trace Viewer** in the Owner Dashboard rendering live execution traces, token consumption, and step rationale. Author prompt-injection attack tests.
- **Checkpoint (End of Week 6 - Milestone 2)**: End-to-end paid job runs autonomously: plan -> act -> observe -> verify -> report. Verified findings have executable Foundry PoCs!

### Phase 4: Multi-Agent Escrow, Observability & Guardrails (Weeks 7 - 8)
- **Person 1**: Implement `ReputationRegistry.sol`. Optimize gas usage on all contracts and commit gas report.
- **Person 2**: Implement peer reviewer agent microservice. Wire multi-agent escrow subcontracting tool (`subagent_escrow_hire`).
- **Person 3**: Implement Human-in-the-Loop approval endpoint (`POST /jobs/{id}/approve-action`) for high-risk actions. Record and expose execution traces via `GET /jobs/{id}/traces`.
- **Person 4**: Connect Owner Console to live trace API. Implement Human Approval banner in UI for pending high-risk actions. Add sandbox escape and wallet drain attack test cases.
- **Checkpoint (End of Week 8 - Milestone 3)**: Full multi-agent escrow and live observability trace view completely integrated.

### Phase 5: Comprehensive Benchmark Evaluation, CI & Release (Weeks 9 - 10)
- **Person 1**: Run Slither on our own contracts, resolve all warnings, and verify testnet contract status.
- **Person 2**: Run full evaluation harness on SWC Registry and Damn Vulnerable DeFi datasets. Compare AuditAgent against 3 baselines (Slither alone, Raw LLM alone, Pipeline without verification). Report precision, recall, FPR reduction, token cost, and net profit.
- **Person 3**: Performance profiling, RPC error recovery, transaction retries, and database query optimization.
- **Person 4**: Integrate benchmark regression test in `.github/workflows/ci.yml`. Execute adversarial test suite. Finalize live demonstration script (`docs/DEMO_SCRIPT.md`), presentation slides, and technical report.
- **Checkpoint (End of Week 10 - Milestone 4 & 5)**: Security verification, benchmark freeze, live demo rehearsal, and v1.0.0 code freeze.

---

## 3. Communication & Code Review Protocol

1. Feature branches (`feat/contracts`, `feat/analysis`, `feat/agent-core`, `feat/dashboard`) merge into `develop` only via Pull Requests.
2. PRs must pass GitHub Actions CI checks (including shared schema validation and benchmark regression tests) before being reviewed.
3. Every merge into `develop` must follow the sequential order in `docs/MERGE_PLAN.md`.
