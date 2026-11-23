# AuditAgent 10-Week Master Timeline

This schedule coordinates the 4 team members across the 10-week semester, synchronizing integration milestones and merge checkpoints.

---

## 1. High-Level Milestone Map

```
Week 1-2   Foundations, Mocks, and Scaffolding
Week 3-4   Standalone Component Implementations & Local Verification
           ─── MILESTONE 1 (End of Week 4): Contracts on Testnet + Analysis v1 + Mock-to-Real Swap Started ───
Week 5-6   Core x402 Integration & End-to-End Pipeline
           ─── MILESTONE 2 (End of Week 6): End-to-End Paid Job Works ───
Week 7-8   Multi-Agent Escrow, Reputation & Full Dashboard Integration
           ─── MILESTONE 3 (End of Week 8): Escrow + Sub-Agent + Dashboard Integrated ───
Week 9     Adversarial Attack Suite & Dataset Benchmark Runs
           ─── MILESTONE 4 (End of Week 9): Security Verification & Performance Freezes ───
Week 10    Final Demo, Presentation Slides, Technical Report & Codebase Freeze
           ─── MILESTONE 5 (End of Week 10): Academic Submission & Presentation ───
```

---

## 2. Weekly Team Matrix

| Week | Person 1 (Contracts) | Person 2 (Analysis & Reviewer) | Person 3 (Agent Core & x402) | Person 4 (Dashboard & Security) | Milestone / Integration Point |
|:---:|---|---|---|---|---|
| **W1** | Set up Foundry repo, write stub contracts & export initial ABIs. | Docker sandbox scaffold, Slither CLI wrapper inside container. | FastAPI server scaffold, SQLite DB models, mock analysis routes. | Next.js scaffold, wagmi setup, landing page & UI layout. | **Kickoff**: Dev environment ready; all tests pass against stubs. |
| **W2** | `AgentWallet.sol`: implement daily limits, per-tx cap, session key logic. | Slither + Aderyn runners; normalize raw outputs to `finding.json`. | x402 Paywall logic: HTTP 402 generation & quote calculation engine. | Customer view: code editor component & quote display with mocks. | **Mocks locked**: Dashboard can query mock API; Agent queries mock runner. |
| **W3** | Unit tests for `AgentWallet` (>90% coverage); fuzz limit boundaries. | LLM triage wrapper; system prompts for false-positive reduction. | On-chain payment verification using `web3.py` against local Anvil node. | Owner view: UI wireframes for balance telemetry and kill-switch button. | **Local integration**: Agent verifies Anvil transactions and updates DB. |
| **W4** | Deploy contracts to Base Sepolia testnet; verify on BaseScan explorer. | End-to-end report generator conforming to `report.json` schema. | Connect FastAPI worker to real Docker analysis runner (swap mock). | Customer view: integrate wagmi wallet connection and USDC transfer flow. | **MILESTONE 1**: Contracts deployed on Base Sepolia; Mock-to-Real swap started. |
| **W5** | `Escrow.sol` implementation: deposit, release, timeout refund logic. | LLM Foundry fuzz test synthesizer for flagged vulnerabilities. | Background job worker queue: async polling and execution pipeline. | Security test harness setup: prompt injection test cases against LLM. | **E2E Progress**: Background queue processes jobs asynchronously. |
| **W6** | Unit tests for `Escrow.sol`; edge cases (early release, expired deadline). | Standalone second-opinion reviewer agent microservice prototype. | Dynamic pricing brain: lines-of-code metric and gas price feed sync. | Malicious contract attack tests (reentrancy, gas bombs, sandbox escapes). | **MILESTONE 2**: End-to-End paid job works from API to report delivery! |
| **W7** | `ReputationRegistry.sol`: scoring oracle and historical averages. | Integrate reviewer agent subcontracting flow via Escrow. | Multi-agent coordination: Agent calls Escrow to hire reviewer agent. | Connect Dashboard customer UI to live Agent Core REST endpoints. | **Multi-Agent Phase**: Primary agent locks escrow and queries reviewer. |
| **W8** | Gas optimization pass on all contracts; commit gas benchmark report. | Benchmark suite harness: SWC-registry and Damn Vulnerable DeFi tests. | Owner admin endpoints: pause signature verification, P&L calculations. | Connect Dashboard owner UI to live Agent status and emergency pause. | **MILESTONE 3**: Escrow + Sub-agent + Dashboard fully integrated! |
| **W9** | Slither analysis on our own contracts; remediate all findings. | Execute full benchmark suite; compute detection recall and FP rates. | Hardening: error recovery, transaction retries, timeout cancellations. | Run full adversarial security attack suite; document defense results. | **MILESTONE 4**: Security verification and performance benchmarks frozen. |
| **W10** | Assist with final report; verify testnet contract status. | Prepare benchmark charts and comparison tables for presentation. | System stability verification and live demo backend configuration. | Complete demo rehearsal, finalize presentation slides and report. | **MILESTONE 5**: Final demo, project presentation, and codebase freeze! |
