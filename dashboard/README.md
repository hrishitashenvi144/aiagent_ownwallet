# AuditAgent Dashboard (Person 4)

Next.js 14 App Router frontend providing customer submission & report tracking and owner management consoles.

## Features
- **Customer View**:
  - Interactive Solidity source code editor & file uploader.
  - Dynamic quote display based on scan tier (`quick`, `standard`, `deep`).
  - Web3 wallet connection (wagmi / viem) on Base Sepolia.
  - x402 payment modal handling USDC approvals and transfers.
  - Interactive vulnerability report viewer with severity filtering.
- **Owner View**:
  - Treasury telemetry: Live USDC balance, 24h daily spend allowance, cumulative margin.
  - Agent reasoning log viewer.
  - On-chain Emergency Kill-Switch toggle.

## Running Locally
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Run dashboard module tests
npm test
```
Open `http://localhost:3000` in your browser.
