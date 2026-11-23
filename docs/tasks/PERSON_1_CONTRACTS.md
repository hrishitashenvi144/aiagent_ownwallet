# Person 1: Smart Contracts & On-Chain Security Guardrails

## 1. Role Summary & Folder Ownership
- **Role Summary**: You are the blockchain engineer responsible for the on-chain infrastructure of AuditAgent. You develop, test, optimize, and deploy the smart contracts that give the agent an autonomous yet secure financial identity.
- **Branch**: `feat/contracts`
- **Owned Folders & Files**:
  - `contracts/` (all Foundry code, tests, scripts, configurations)
  - `shared/abis/` (exporting updated JSON ABIs)
- **MUST NOT EDIT**:
  - `analysis/` (Person 2)
  - `agent/` (Person 3)
  - `dashboard/` (Person 4)
  - `shared/schemas/` (Requires Lead RFC)

---

## 2. Interfaces You Implement & Consume
- **Implement**:
  - `contracts/src/AgentWallet.sol`: Smart account implementing daily limit, per-tx cap, session keys, vendor allowlist, emergency pause.
  - `contracts/src/Escrow.sol`: Milestone-based reviewer payment escrow.
  - `contracts/src/ReputationRegistry.sol`: On-chain oracle of reviewer consensus scores.
  - Export canonical ABIs to `shared/abis/AgentWallet.json`, `shared/abis/Escrow.json`, `shared/abis/ReputationRegistry.json`.
- **Consume**:
  - OpenZeppelin Contracts v5 (ERC20, Ownable, Pausable, ReentrancyGuard).
  - OpenZeppelin ERC-4337 reference structures.
- **Reference**: Detailed signatures and events are defined in [INTERFACES.md](../INTERFACES.md).

---

## 3. Dependencies & Mocks
- **Your work does not depend on other modules to get started.** You can develop contracts in isolation using Foundry Anvil.
- **Person 3 & 4 depend on you**: They will use your stub ABIs in `shared/abis/` and local Anvil deployments until testnet deployment at the end of Week 4.

---

## 4. Week-by-Week Task Checklist (10 Weeks)

### Week 1: Foundry Environment & Stub Setup
- [ ] Initialize Foundry structure (`forge init --no-commit`). Configure `foundry.toml` with EVM version `shanghai` and optimizer enabled (runs: 200). *(Est: 4h)*
  - *Done When*: `forge build` compiles without warnings.
- [ ] Write stub contracts (`AgentWallet.sol`, `Escrow.sol`, `ReputationRegistry.sol`) with empty function signatures matching `docs/INTERFACES.md`. *(Est: 4h)*
  - *Done When*: Exported ABIs in `shared/abis/` match interface specification.

### Week 2: AgentWallet Spending Caps & Session Keys
- [ ] Implement `AgentWallet.sol` core logic: `perTxCap`, `dailyCap` (24h rolling window reset), and `reserveBalance` safety floor. *(Est: 6h)*
  - *Done When*: Transactions exceeding caps revert with `PerTxCapExceeded()` or `DailyCapExceeded()`.
- [ ] Implement session key authorization: `setSessionKey(address key, uint48 validUntil, uint48 validAfter)`. *(Est: 5h)*
  - *Done When*: Calls by session keys outside valid timestamp revert with `SessionKeyExpired()`.

### Week 3: AgentWallet Allowlist, Pause & Comprehensive Tests
- [ ] Implement vendor allowlisting (`setVendorAllowlist`) and owner pause/unpause switches. *(Est: 4h)*
  - *Done When*: Unlisted destination calls revert with `VendorNotAllowed()`.
- [ ] Write exhaustive Foundry unit and fuzz tests in `contracts/test/AgentWallet.t.sol`. *(Est: 8h)*
  - *Done When*: Code coverage for `AgentWallet.sol` exceeds 90%.

### Week 4: Base Sepolia Deployment & Milestone 1
- [ ] Write Foundry deployment script in `contracts/script/Deploy.s.sol`. *(Est: 5h)*
  - *Done When*: Script deploys mock USDC and `AgentWallet` deterministically.
- [ ] Deploy contracts to Base Sepolia testnet and verify source code on BaseScan. Commit deployed addresses to `.env.example`. *(Est: 5h)*
  - *Done When*: Deployed addresses are verified on BaseScan and shared with Person 3 and 4.

### Week 5: Escrow Contract Implementation
- [ ] Implement `Escrow.sol` for peer reviewer bounties (`createEscrow`, `releaseEscrow`, `refundEscrow`). *(Est: 7h)*
  - *Done When*: Primary agent locks USDC; funds released only upon authorization or refunded after timeout.

### Week 6: Escrow Security & Invariant Tests
- [ ] Write unit tests and fuzz invariant tests in `contracts/test/Escrow.t.sol`. *(Est: 7h)*
  - *Done When*: Invariant test proves no funds can be drained without proper client signature or expired deadline.

### Week 7: ReputationRegistry Implementation
- [ ] Implement `ReputationRegistry.sol` to track peer reviewer performance scores. *(Est: 5h)*
  - *Done When*: New reviews update historical rolling average score.
- [ ] Write unit tests for `ReputationRegistry.t.sol`. *(Est: 4h)*
  - *Done When*: Tests achieve 100% coverage on `ReputationRegistry.sol`.

### Week 8: Gas Optimization & Gas Benchmark Report
- [ ] Run `forge snapshot` and optimize storage layouts, custom errors, and calldata slicing. *(Est: 6h)*
  - *Done When*: Gas consumption decreases across core functions; `contracts/gas-report.txt` committed.

### Week 9: Slither Scan on Our Own Contracts
- [ ] Run Slither static analyzer on all repository contracts: `slither contracts/`. *(Est: 5h)*
  - *Done When*: All high and medium warnings resolved with zero unresolved security findings.

### Week 10: Final Audit Verification, Viva & Code Freeze
- [ ] Assist with contract verification documentation, architecture diagrams, and testnet address proof for final viva. *(Est: 6h)*
  - *Done When*: Contracts confirmed active on Base Sepolia with verified clean records.

---

## 5. Suggested LLM Prompts
- **For Week 2 (Spending Limits)**:
  > *"Write a Solidity 0.8.20 contract AgentWallet inheriting OpenZeppelin Ownable and Pausable. Implement a daily rolling spend limit tracking dailySpent and lastResetDay, plus a perTxCap and a reserveBalance check that prevents any balance under 50 USDC from being spent by session keys. Use custom errors."*
- **For Week 3 (Foundry Fuzzing)**:
  > *"Write a comprehensive Foundry test AgentWallet.t.sol. Include a fuzz test testFuzz_DailySpendCap(uint256[] calldata amounts) to assert that cumulative spends exceeding dailyCap always revert."*
- **For Week 5 (Escrow)**:
  > *"Write an Escrow contract in Solidity 0.8.20 where a client deposits ERC20 tokens for a specific jobId. The client can release funds to reviewer, or call refund after deadline block.timestamp. Guard against reentrancy."*

---

## 6. Common Pitfalls & Security Notes
1. **Timestamp Manipulation**: Use block timestamps for session keys and escrow deadlines with sufficient tolerance (e.g. 15-minute buffers).
2. **Reentrancy**: Always apply `ReentrancyGuard` and follow Checks-Effects-Interactions pattern when calling `execute` or releasing escrow funds.
3. **Decimals Precision**: Remember testnet USDC has 6 decimals, whereas ETH has 18. Never mix units.
