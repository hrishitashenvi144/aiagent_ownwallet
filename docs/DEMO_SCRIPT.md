# AuditAgent Live Demonstration Script

This script provides a 5-minute step-by-step live demonstration plan for academic reviews, university presentations, and technical showcases.

---

## Preparation Checklist (T-Minus 15 Minutes)
- [ ] Local Anvil node running on `http://127.0.0.1:8545` (or live Base Sepolia testnet connection).
- [ ] Agent Core FastAPI service running on `http://localhost:8000`.
- [ ] Next.js dashboard running on `http://localhost:3000`.
- [ ] Browser wallet (MetaMask / Coinbase Wallet) loaded with Base Sepolia testnet ETH and testnet USDC.
- [ ] Sample vulnerable contract file ready (`benchmarks/datasets/sample_contracts/SimpleReentrancy.sol`).

---

## 5-Minute Live Demo Flow

### Act 1: Introduction & Micro-Business Concept (0:00 - 0:45)
- **Presenter**: *"Welcome to AuditAgent. We built an autonomous AI agent that operates as a self-sustaining on-chain security business on Base Sepolia. It triages smart contract vulnerabilities for developers before they pay for expensive manual audits, accepts testnet USDC through an HTTP 402 protocol, manages its own profit margins, and enforces strict financial safety limits on its smart wallet."*
- **Visual**: Show the Next.js landing page with live agent status, wallet address, and gas/pricing metrics.

### Act 2: Dynamic Quoting & The x402 Flow (0:45 - 2:00)
1. **Submit Code**:
   - Navigate to Customer Portal (`/submit`).
   - Paste `SimpleReentrancy.sol` containing a vulnerable `withdrawBalance()` function.
   - Select scan tier: **"Standard"** (Slither + Aderyn + LLM Triage).
2. **Observe 402 Flow**:
   - Click **"Generate Quote & Submit"**.
   - Show network inspector tab: Observe HTTP `402 Payment Required` returned by FastAPI with headers `X-Accept-Token`, `X-Payment-Address`, and `X-Required-Amount`.
   - UI seamlessly captures the 402 response and triggers the Web3 payment modal.
3. **Pay On-Chain**:
   - Click **"Approve & Pay 15 USDC"** in the modal.
   - Confirm the transaction in MetaMask.
   - Transaction hash is forwarded to the agent API in the `X-Payment-Proof` header.
   - Show status transition on screen: `created` -> `quoted` -> `paid` -> `analyzing`.

### Act 3: Sandboxed Execution & Multi-Engine Triage (2:00 - 3:15)
1. **Containerized Analysis**:
   - Explain to the audience: *"Behind the scenes, the agent spawned a Docker container with zero network access and strict CPU/memory caps."*
   - Show terminal logs of Slither and Aderyn detecting raw AST issues.
   - Show LLM triage reducing false positives and synthesizing an exploit Foundry test (`ReentrancyPoC.t.sol`).
2. **Review Completed Report**:
   - Status updates in real-time to `delivered`.
   - Show generated report:
     - Composite Risk Score: `92 / 100` (Critical).
     - Clean finding card highlighting vulnerable line numbers, evidence snippet, root cause explanation, and proposed fix using OpenZeppelin `ReentrancyGuard`.
     - Synthesized Foundry exploit test passing locally to prove exploitability.

### Act 4: Multi-Agent Escrow Subcontracting (3:15 - 4:15)
1. **Deep Scan Mode**:
   - Demonstrate submitting under **"Deep"** tier.
   - Show agent console logs: The primary agent determines that high-complexity contracts require a second opinion.
   - Show on-chain transaction: `AgentWallet` calls `Escrow.sol` depositing a 5 USDC bounty for the peer reviewer agent.
   - Show secondary reviewer agent submitting findings and claiming bounty upon consensus agreement.
   - View updated reputation score in `ReputationRegistry.sol`.

### Act 5: Owner Console, P&L Telemetry & Emergency Kill Switch (4:15 - 5:00)
1. **Switch to Owner View** (`/owner`):
   - Show live agent treasury: Total USDC earned, gross revenue, net margin, and reserve deposits.
   - Show agent reasoning log: Why specific scan depths and tool combinations were selected.
2. **Emergency Kill-Switch Trigger**:
   - Demonstrate on-chain safety: Click **"Emergency Pause"**.
   - Sign owner transaction.
   - Attempt a new submission: Show that `AgentWallet` and API reject new transactions with `AgentPausedError`.
- **Conclusion**: *"AuditAgent demonstrates how AI agents can operate transparent, safe, and autonomous micro-economies on Ethereum L2s."*
