# AuditAgent Smart Contracts (Person 1)

This module contains the Solidity smart contracts, Foundry test harness, deployment scripts, and gas benchmarking setup for **AuditAgent**.

## Contracts Overview
- **`src/AgentWallet.sol`**: Autonomous agent smart wallet with on-chain safety rails:
  - Per-transaction spend ceiling (`perTxCap`).
  - Rolling 24-hour daily spend cap (`dailyCap`).
  - Non-custodial reserve balance untouchable by session keys (`reserveBalance`).
  - Vendor allowlist limiting target call destinations.
  - Cryptographically bounded session keys (`validAfter`, `validUntil`).
  - Owner emergency kill-switch (`pause()` / `unpause()`).
- **`src/Escrow.sol`**: Decentralized escrow contract for second-opinion reviewer agent bounties.
- **`src/ReputationRegistry.sol`**: On-chain scoring oracle tracking reviewer accuracy.

## Prerequisites & Manual Install Steps
To compile and test these contracts on your machine, install Foundry:

### On Linux / macOS / WSL:
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### On Windows PowerShell:
```powershell
# In PowerShell:
irm https://raw.githubusercontent.com/foundry-rs/foundry/master/foundryup/install.ps1 | iex
foundryup
```

## Foundry Commands
```bash
# Build contracts
forge build

# Run unit and fuzz tests with verbosity
forge test -vvv

# Run test coverage analysis (target >90%)
forge coverage

# Run local gas snapshot
forge snapshot

# Deploy to local Anvil node
forge script script/Deploy.s.sol:DeployScript --rpc-url http://127.0.0.1:8545 --broadcast

# Deploy to Base Sepolia testnet
forge script script/Deploy.s.sol:DeployScript --rpc-url https://sepolia.base.org --broadcast --verify
```

## Node.js Fallback Test Runner
If Foundry is not yet installed in your current shell, you can verify contract source integrity and stub ABIs via:
```bash
npm test
```
