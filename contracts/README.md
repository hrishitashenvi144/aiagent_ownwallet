# AuditAgent Smart Contracts (Person 1)

Solidity 0.8.20 + Foundry. All amounts are **USDC with 6 decimals** (5 USDC = `5e6`). Testnet only.

## Contracts

| Contract | What it does |
|---|---|
| `src/AgentWallet.sol` | The agent's account. Owner has full control; the AI's *session key* can only call **allowlisted vendors**, within `perTxCap`, a rolling-24h `dailyCap`, and above a `reserveBalance` floor. Owner can `pause()` everything and `withdrawReserve()` at any time. |
| `src/Escrow.sol` | Locks a USDC bounty for a reviewer agent. Only the client can `releaseEscrow` (pay reviewer) or, after the deadline, `refundEscrow`. |
| `src/ReputationRegistry.sol` | Reviewer scores 1-100 as a running average. Only owner-approved recorders (`setRecorder`) can write. |
| `src/mocks/MockUSDC.sol` | Testnet token with open `mint()`. Never for mainnet. |

### How spending limits work (viva-worthy)
`execute()` measures the wallet's USDC balance **before and after** the call. What actually left the wallet is
what counts against the caps, so a vendor call can't hide a transfer. Session keys also cannot send ETH, and
`approve()` is only allowed towards an allowlisted vendor for <= `perTxCap` (otherwise an allowance could be
pulled later, outside `execute()`, dodging every cap).

### Additions beyond `docs/INTERFACES.md` (flag to Lead)
- Constructors: `AgentWallet(usdc, owner, perTxCap, dailyCap, reserve)`, `Escrow(usdc)`, `ReputationRegistry(owner)`.
- `ReputationRegistry.setRecorder(address,bool)`: without it anyone could spam scores.
- Extra errors: `InvalidLimits`, `InvalidSessionWindow`, `ForbiddenCall`, `ExecutionFailed`; Escrow: `InvalidAmount/Reviewer/Deadline`.
- `createEscrow` is no longer `payable` (it pulls USDC via `transferFrom`; the caller must `approve` the escrow first).
- A session key is a mapping (several keys can be valid); `setSessionKey(key, 0, 0)` revokes.
- Paused state reverts with OpenZeppelin's `EnforcedPause()`.

## Commands
```bash
forge build
forge test                         # 72 tests incl. fuzz + escrow invariants
forge test --no-match-contract Invariant   # fast loop
forge coverage --no-match-coverage "(test|script|lib|mocks)"   # 100% on all 3 contracts
forge test --gas-report --no-match-contract Invariant          # -> gas-report.txt
FOUNDRY_OFFLINE=true SOLC_VERSION=0.8.20 slither . --filter-paths "lib|test|script|mocks"   # -> slither-report.txt
```
Dependencies (OpenZeppelin 5.0.2, forge-std 1.9.7) are vendored in `lib/`, mapped in `remappings.txt`.

## Deploy
```bash
# local
anvil &
export PRIVATE_KEY=<anvil key #0>     # printed by anvil; local only
forge script script/Deploy.s.sol:DeployScript --rpc-url http://127.0.0.1:8545 --broadcast

# Base Sepolia (testnet funds only!). Set USDC_ADDRESS to reuse the real testnet USDC, otherwise MockUSDC is deployed.
export PRIVATE_KEY=<testnet-only key>  USDC_ADDRESS=0x036CbD53842c5426634e7929541eC2318f3dCF7e
forge script script/Deploy.s.sol:DeployScript --rpc-url base_sepolia --broadcast --verify
```
Defaults: perTx 5 USDC, daily 25 USDC, reserve 50 USDC. Never commit keys or `.env`.

### Configure (run once after deploy, as the owner)
Allowlists USDC + Escrow, authorises the agent's session key, lets it record reviews, optionally mints MockUSDC:
```bash
export PRIVATE_KEY=<owner key>  SESSION_KEY_ADDRESS=<agent session key PUBLIC address>
export AGENT_WALLET_ADDRESS=0x...  ESCROW_CONTRACT_ADDRESS=0x...  USDC_TOKEN_ADDRESS=0x...  REPUTATION_REGISTRY_ADDRESS=0x...
MINT_USDC=150 forge script script/Configure.s.sol:ConfigureScript --rpc-url base_sepolia --broadcast   # MINT_USDC only with MockUSDC
```
Note: bounties above `perTxCap` (5 USDC) revert for the session key; raise it with `setLimits` if the agent should pay up to 10.

## ABIs
`shared/abis/*.json` are generated: `forge inspect <Contract> abi --json > ../shared/abis/<Contract>.json`.

## Node fallback check
`npm test` verifies the source files and ABIs exist (no Foundry needed).
