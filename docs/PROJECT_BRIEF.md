# AuditAgent Project Brief

## 1. Executive Summary
AuditAgent is an autonomous AI agent engineered as an on-chain micro-business running on Base Sepolia. The system provides pre-audit security triage for Solidity smart contracts. Customers submit contract code and pay using testnet USDC via an HTTP 402 ("Payment Required") protocol. 

The agent analyzes contract complexity, formulates quotes, verifies on-chain payment proofs, executes sandboxed multi-analyzer pipelines (Slither, Aderyn, LLM vulnerability filtering, and LLM-synthesized Foundry fuzz tests), optionally delegates consensus checks to peer reviewer agents through smart contract escrows, delivers a structured, ranked security report, and retains operating profit.

## 2. Core Value Proposition & Positioning
- **Target Audience**: Solidity developers, hackathon teams, and DeFi protocols seeking rapid automated security scans before scheduling comprehensive manual audits.
- **Positioning**: **Pre-audit automated triage and vulnerability discovery**, NOT a certified audit report or replacement for manual human security auditing.
- **Safety Boundary**: Strict testnet-only deployment (Base Sepolia). No mainnet funds or real value are ever risked.

## 3. Key Differentiators
1. **Autonomous Economic Agent**: The agent maintains its own smart wallet, calculates dynamic pricing based on computational and LLM token costs, tracks gross margins, and saves profits in an untouchable on-chain reserve.
2. **On-Chain Financial Safety Rails**:
   - `AgentWallet` implements per-transaction expenditure caps.
   - Rolling 24-hour daily spend ceilings.
   - Hardcoded untouchable reserve balance only withdrawable by the human owner.
   - Vendor allowlists restricting outbound calldata.
   - Session keys with strict cryptographic validity windows.
   - Emergency pause switch (owner override).
3. **Decentralized Multi-Agent Subcontracting**:
   - For high-complexity contracts (`deep` scan mode), the agent can autonomously subcontract an independent peer reviewer agent.
   - Funds are locked in a non-custodial `Escrow` smart contract.
   - Both agents contribute to an on-chain `ReputationRegistry`.

## 4. Key Performance Targets
- **Code Coverage**: >= 90% branch/statement coverage on Solidity contracts.
- **Triage Precision**: Benchmark vulnerability detection >= 80% recall on SWC/SmartBugs known vulnerability datasets with < 20% false positive rate after LLM triage.
- **End-to-End Latency**: Quick scan < 60s; Standard scan < 180s; Deep scan < 400s.
- **Sandbox Security**: 0% host escape rate against adversarial test suites.
