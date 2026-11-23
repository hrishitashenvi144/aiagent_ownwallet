# AuditAgent System Interfaces & Specifications

> **Notice to All Team Members**: This document defines the canonical contracts, data formats, state machines, and communication protocols between all modules. Any changes to files in `shared/` or this document require an explicit Pull Request reviewed and approved by the Lead Engineer.

---

## 1. Schema Specifications

All JSON payloads conform to draft 2020-12 JSON Schema specifications located in `shared/schemas/`.

### 1.1 Finding Schema (`shared/schemas/finding.json`)
A finding represents a single security vulnerability, bug, or informational issue discovered by any static analyzer, LLM auditor, or fuzz engine.

- **`id`** (`string`): Unique identifier (e.g. `VULN-REENTRANCY-001`, `SWC-107-1`).
- **`title`** (`string`): Summary of the vulnerability.
- **`severity`** (`string`): `"Critical"` | `"High"` | `"Medium"` | `"Low"` | `"Informational"`.
- **`confidence`** (`string`): `"High"` | `"Medium"` | `"Low"`.
- **`location`** (`object`):
  - `file`: Path relative to the analyzed repository.
  - `contract_name`: Target contract name.
  - `function_name`: Enclosing function or hook.
  - `start_line` / `end_line`: Code line numbers.
- **`evidence`** (`string`): Code snippet, AST trace, or raw tool snippet.
- **`explanation`** (`string`): Root cause analysis, threat scenario, impact.
- **`suggested_fix`** (`string`): Recommended remediation or code diff.
- **`tool_source`** (`string`): `"slither"` | `"aderyn"` | `"llm"` | `"foundry_fuzz"`.
- **`poc_test_path`** (`string`, optional): Filepath to Foundry test verifying exploitability.

### 1.2 Report Schema (`shared/schemas/report.json`)
Consolidated final deliverable for a customer's audit job.

- **`job_id`** (`string`): Unique UUID of the job.
- **`timestamp`** (`string` ISO 8601): Delivery time.
- **`scan_depth`** (`string`): `"quick"` | `"standard"` | `"deep"`.
- **`target_contract`** (`string`): Primary contract analyzed.
- **`summary`** (`object`):
  - `risk_score`: Float between `0.0` (clean) and `100.0` (catastrophic).
  - Counts: `total_critical`, `total_high`, `total_medium`, `total_low`, `total_informational`.
- **`findings`** (`array`): Array of validated Finding items.
- **`triage_notes`** (`string`): LLM executive summary synthesizing multi-tool findings.
- **`second_opinion`** (`object`, optional): Reviewer agent address, escrow ID, consensus score, and notes.
- **`gas_report`** (`object`, optional): Gas bottlenecks detected during invariant or symbolic runs.

### 1.3 Job & Quote Schemas
- **`JobRecord`** (`shared/schemas/job.json`): Tracks DB entity lifecycle (`created`, `quoted`, `paid`, `analyzing`, `delivered`, `failed`, `refunded`).
- **`Quote`** (`shared/schemas/quote.json`): Pricing model output containing human-readable USDC, raw token units (6 decimals), and expiration.

---

## 2. Agent REST API & x402 Payment Flow

Complete OpenAPI 3.1 specification is maintained at `shared/openapi.yaml`.

### 2.1 Endpoints Overview
| Method | Path | Description | Auth / Headers |
|---|---|---|---|
| `POST` | `/quote` | Get dynamic quote based on lines of code and depth | Public |
| `POST` | `/jobs` | Submit audit job (returns 402 if unpaid, 201 when paid) | `X-Payment-Proof` (optional on submit) |
| `GET` | `/jobs/{id}` | Query current job status & progress | Public |
| `GET` | `/jobs/{id}/report` | Retrieve completed audit report | Public |
| `GET` | `/agent/status` | Read wallet balance, daily spent, pause flag | Public |
| `POST` | `/owner/pause` | Emergency kill/pause switch | Owner Signature (EIP-712 / ECDSA) |

### 2.2 The x402 "Payment Required" Protocol
1. **Client Submits Job**: Client issues `POST /jobs` without payment proof.
2. **Agent Returns 402**:
   ```http
   HTTP/1.1 402 Payment Required
   Content-Type: application/json
   X-Accept-Token: 0x036CbD53842c5426634e7929541eC2318f3dCF7e
   X-Payment-Address: 0xAgentWalletAddressHere
   X-Required-Amount: 15000000

   {
     "error": "Payment Required",
     "job_id": "7b042d76-159e-43f1-b92c-eecdfdb0470d",
     "required_amount_usdc": 15.00,
     "required_amount_raw": "15000000",
     "payment_address": "0xAgentWalletAddressHere",
     "payment_token": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
     "instructions": "Transfer 15 USDC on Base Sepolia to payment_address with job_id in calldata, or submit tx hash in X-Payment-Proof."
   }
   ```
3. **Client Pays On-Chain**: Customer wallet initiates ERC-20 `transfer(agentWallet, 15000000)` or calls a deposit function.
4. **Client Submits Proof**: Client re-submits `POST /jobs` with header:
   ```http
   X-Payment-Proof: 0x3b64c1...txHash...
   ```
5. **On-Chain Verification**:
   - `web3.py` fetches transaction receipt from Base Sepolia RPC.
   - Verifies target is `AgentWallet`, token contract is mock/testnet USDC, value matches `quote_amount`, and transaction succeeded.
   - Status transitions to `paid` and job is enqueued into background analyzer.

---

## 3. Smart Contract Interface Specifications

Contract ABIs are committed in `shared/abis/`. All contracts are compiled with Solidity `^0.8.20` and inherit OpenZeppelin 5.x contracts.

### 3.1 `AgentWallet.sol`
ERC-4337-ready smart account with strict on-chain safeguards:
- **Session Keys**: Temporary delegate key with strict expiration (`validUntil`, `validAfter`).
- **Caps**: `perTxCap` (e.g. 5 USDC), `dailyCap` (e.g. 25 USDC), `reserveBalance` (e.g. minimum 50 USDC untouchable by agent).
- **Vendor Allowlist**: Only pre-approved escrow contracts or analysis oracle addresses can receive transfers.
- **Pause & Emergency**: Owner can call `pause()`, `unpause()`, or drain funds via `withdrawReserve()`.

```solidity
interface IAgentWallet {
    event TransactionExecuted(address indexed target, uint256 value, bytes data);
    event SessionKeyUpdated(address indexed key, uint48 validUntil);
    event VendorStatusChanged(address indexed vendor, bool allowed);

    error DailyCapExceeded();
    error PerTxCapExceeded();
    error ReserveBreached();
    error VendorNotAllowed();
    error SessionKeyExpired();
    error Unauthorized();

    function execute(address dest, uint256 value, bytes calldata func) external returns (bytes memory);
    function setSessionKey(address key, uint48 validUntil, uint48 validAfter) external;
    function setLimits(uint256 perTxCap, uint256 dailyCap, uint256 reserveBalance) external;
    function setVendorAllowlist(address vendor, bool allowed) external;
    function pause() external;
    function unpause() external;
    function withdrawReserve(address to, uint256 amount) external;
    function getDailySpent() external view returns (uint256);
}
```

### 3.2 `Escrow.sol`
Manages trust-minimized payments to autonomous second-opinion reviewer agents.
- **Deposit**: Agent locks second-opinion bounty.
- **Release**: Released when reviewer submits valid report before deadline.
- **Refund**: Agent reclaims bounty if deadline expires without delivery.

```solidity
interface IEscrow {
    event EscrowCreated(bytes32 indexed jobId, address indexed client, address indexed reviewer, uint256 amount, uint256 deadline);
    event EscrowReleased(bytes32 indexed jobId, address indexed reviewer, uint256 amount);
    event EscrowRefunded(bytes32 indexed jobId, address indexed client, uint256 amount);

    function createEscrow(bytes32 jobId, address reviewer, uint256 amount, uint256 deadline) external;
    function releaseEscrow(bytes32 jobId) external;
    function refundEscrow(bytes32 jobId) external;
    function getEscrow(bytes32 jobId) external view returns (address client, address reviewer, uint256 amount, uint256 deadline, uint8 status);
}
```

### 3.3 `ReputationRegistry.sol`
On-chain rating oracle storing historical audit consensus scores:
- Score: `1` to `100` rating for reviewer accuracy.
- Cumulative moving average updated on-chain.

```solidity
interface IReputationRegistry {
    event ReviewRecorded(address indexed reviewer, bytes32 indexed jobId, uint8 score, uint256 newAverageScore, uint256 totalReviews);

    function recordReview(address reviewer, bytes32 jobId, uint8 score, string calldata metadataUri) external;
    function getReputation(address reviewer) external view returns (uint256 averageScore, uint256 totalReviews);
}
```

---

## 4. Job Lifecycle State Machine

```
              [ Client requests quote ]
                          │
                          ▼
                     ┌─────────┐
                     │ created │
                     └────┬────┘
                          │ (Agent calculates price)
                          ▼
                     ┌─────────┐
       ┌─────────────┤ quoted  ├─────────────┐
       │             └────┬────┘             │
       │ (Timeout)        │ (Valid payment)  │ (Payment fails)
       ▼                  ▼                  ▼
  ┌─────────┐        ┌─────────┐        ┌─────────┐
  │ failed  │        │  paid   │        │ failed  │
  └─────────┘        └────┬────┘        └─────────┘
                          │ (Trigger analysis pipeline)
                          ▼
                     ┌───────────┐
                     │ analyzing │
                     └─────┬─────┘
          ┌────────────────┴────────────────┐
          │ (Analysis success)              │ (Crash / Unrecoverable)
          ▼                                 ▼
    ┌───────────┐                     ┌───────────┐
    │ delivered │                     │ refunded  │
    └───────────┘                     └───────────┘
```

### State Transition Rules:
1. **`created` -> `quoted`**: Job parameters validated; quote amount computed.
2. **`quoted` -> `paid`**: On-chain verification succeeds. `tx_hash` persisted.
3. **`paid` -> `analyzing`**: Background worker process picks up job from queue.
4. **`analyzing` -> `delivered`**: Report assembled, validated against `report.json` schema, stored in DB.
5. **`analyzing` -> `refunded`**: If analysis fails unrecoverably and customer already paid, `AgentWallet` triggers on-chain refund and status becomes `refunded`.
6. **`*` -> `failed`**: Unrecoverable validation errors or customer payment timeout.

---

## 5. Development Mocks & Stubs

To enable seamless parallel development across all 4 roles from Day 1:

1. **Dashboard Developers (Person 4)**:
   - Use `agent/agent/mock_server.py` or FastAPI mock router providing pre-baked responses matching `shared/openapi.yaml`.
   - Toggle mock mode via `NEXT_PUBLIC_USE_MOCK=true` in `dashboard/.env.local`.

2. **Agent Core Developers (Person 3)**:
   - Use `analysis/analysis/mock_runner.py` which returns synthetic findings matching `shared/schemas/report.json` without launching Docker.
   - Use local Anvil stub contracts or mock web3 provider (`agent/tests/mock_web3.py`).

3. **Analysis Developers (Person 2)**:
   - Consume synthetic contract snippets from `benchmarks/datasets/sample_contracts/`.
   - Run tests against mock LLM responses returning valid `Finding` JSON.

4. **Contract Developers (Person 1)**:
   - Deploy stub contracts to local Foundry Anvil node (`scripts/dev.sh` starts Anvil on `8545`).
   - Export freshly compiled ABIs to `shared/abis/` when interfaces are updated.
