# Person 4: Dashboard, Observability Trace View, Security Suite & CI

## 1. Role Summary & Folder Ownership
- **Role Summary**: You build the user-facing web interface (Customer Portal & Owner Observability Dashboard in Next.js), author the adversarial attack security suite, build the live **Agent Execution Trace View**, implement the **Human-in-the-Loop Approval UI**, integrate CI benchmark regression gates, and lead final demo preparation and documentation.
- **Branch**: `feat/dashboard`
- **Owned Folders & Files**:
  - `dashboard/` (Next.js 14 App Router, Tailwind CSS, wagmi/viem web3 integration, trace viewer, approval banners)
  - `security-tests/` (adversarial attack suites, prompt injection probes, exploit tests, penetration vectors)
  - `.github/workflows/ci.yml` (CI maintenance and benchmark regression gates)
  - `docs/DEMO_SCRIPT.md`
- **MUST NOT EDIT**:
  - `contracts/` (Person 1)
  - `analysis/` (Person 2)
  - `agent/` (Person 3)
  - `shared/schemas/` (Requires Lead RFC)

---

## 2. Interfaces You Implement & Consume
- **Implement**:
  - **Customer UI**: Solidity submission editor, dynamic quote card, x402 USDC payment modal, interactive report viewer with **Verified Exploit PoC tab** (rendering `verified: bool` badge and `poc_path`).
  - **Owner Observability View (`/owner`)**: Live treasury balance, net P&L metrics, and the **Agent Trace View** visualizing step-by-step state machine iterations (`PLAN` -> `ACT` -> `OBSERVE` -> `REPLAN`), tool parameters, latency, model routed, and decision rationale.
  - **Human-in-the-Loop Approval Banner**: UI component enabling operators to approve or reject pending high-risk actions (`POST /jobs/{id}/approve-action`).
  - **CI Benchmark Regression Gate**: Adding threshold validation into `.github/workflows/ci.yml`.
  - **Security Attack Suite (`security-tests/`)**: Automated penetration tests probing prompt injections, sandbox network escapes, fake payment proofs, and wallet drain ceilings.
- **Consume**:
  - Agent REST API specified in `shared/openapi.yaml` (`POST /quote`, `POST /jobs`, `GET /jobs/{id}`, `GET /jobs/{id}/report`, `GET /jobs/{id}/traces`, `POST /jobs/{id}/approve-action`, `GET /agent/status`, `POST /owner/pause`).
  - Base Sepolia testnet contracts via wagmi/viem: `AgentWallet`, `Escrow`, testnet USDC.
- **Reference**: Detailed specs are in [INTERFACES.md](../INTERFACES.md).

---

## 3. Dependencies & Mocks
- **Before Person 3 completes Agent Core**: Run the frontend against `agent/agent/mock_server.py` which provides mock `/traces` and mock reports with `verified: bool`.
- **Before Person 1 deploys contracts on Base Sepolia**: Connect browser wallet to local Foundry Anvil (`http://127.0.0.1:8545`).

---

## 4. Week-by-Week Task Checklist (10 Weeks)

### Week 1: Next.js App Router Scaffold & Web3 Providers
- [ ] Initialize Next.js 14 App Router with TypeScript and Tailwind CSS in `dashboard/`. *(Est: 4h)*
  - *Done When*: `npm run build` succeeds and landing page renders cleanly.
- [ ] Configure wagmi and viem providers for Base Sepolia and local Anvil in `dashboard/app/providers.tsx`. *(Est: 4h)*
  - *Done When*: User can connect MetaMask or Coinbase Wallet on Base Sepolia.

### Week 2: Customer Submission Portal & Mock API Integration
- [ ] Build contract submission page (`/submit`) with code input, file upload, and scan tier selector (`quick`/`standard`/`deep`). *(Est: 6h)*
  - *Done When*: User can enter Solidity code and select scan depth.
- [ ] Integrate mock agent quoting API to render pricing cards and estimated completion time. *(Est: 4h)*
  - *Done When*: Quoting details display dynamically based on input length.

### Week 3: x402 Web3 Payment Modal & Flow
- [ ] Implement x402 payment modal handling HTTP 402 responses. *(Est: 6h)*
  - *Done When*: Submitting unpaid job opens modal prompting for testnet USDC approval and transfer.
- [ ] Wire wagmi `useWriteContract` to execute ERC20 USDC `transfer`, capturing transaction hash for `X-Payment-Proof`. *(Est: 5h)*
  - *Done When*: Successful transaction automatically submits payment proof to agent backend.

### Week 4: Live Job Tracking & Report Viewer with Verified PoC Badge
- [ ] Build real-time job progress page (`/jobs/[id]`) polling job status. *(Est: 5h)*
  - *Done When*: Page visually reflects state transitions (`paid` -> `analyzing` -> `delivered`).
- [ ] Implement interactive report viewer rendering risk score, summary charts, and expandable finding cards displaying the **Verified Exploit PoC** code block when `verified: true`. *(Est: 5h)*
  - *Done When*: Report viewer validates and displays complete `shared/schemas/report.json` data.

### Week 5: Security Attack Suite: Prompt Injection Tests
- [ ] Scaffold `security-tests/` with pytest and HTTP client. *(Est: 4h)*
  - *Done When*: Test runner executes and reports status.
- [ ] Implement prompt injection attack test cases in `security-tests/tests/test_prompt_injection.py` (system prompt override, jailbreak attempts, key extraction). *(Est: 6h)*
  - *Done When*: Tests verify LLM triage does not execute injected instructions or leak system environment variables.

### Week 6: Observability Trace Viewer Component (Owner Console)
- [ ] Build the interactive **Agent Trace Viewer** component in `dashboard/app/owner/traces/page.tsx` or `/owner`:
  - Visualizes step-by-step execution timeline (`PLAN` -> `ACT` -> `OBSERVE` -> `REPLAN` -> `VERIFY`).
  - Displays tool name, parameter payload, execution latency (ms), token cost, model routed, and planner rationale for each step. *(Est: 7h)*
  - *Done When*: Owner dashboard fetches and renders trace records from `GET /jobs/{id}/traces`.

### Week 7: Security Attack Suite: Sandbox Escapes, Fake Payments & Caps
- [ ] Implement sandbox escape probes (network egress attempts, compiler memory bombs). *(Est: 5h)*
  - *Done When*: Tests verify Docker sandbox denies outbound networking and kills runaway compiler memory within limits.
- [ ] Implement fake payment proof tests (replayed tx hash, wrong token contract, underpaid amounts) and wallet drain ceiling tests. *(Est: 5h)*
  - *Done When*: All forgery and wallet drain attempts fail deterministically.

### Week 8: Human-in-the-Loop Operator Approval UI & Kill Switch
- [ ] Build **Human Approval Banner** in Owner View displaying pending high-risk agent actions (e.g., escrow bounty > $10) with one-click "Approve" / "Reject" buttons calling `POST /jobs/{id}/approve-action`. *(Est: 5h)*
  - *Done When*: Operator can review pending action and trigger resume.
- [ ] Implement Emergency Kill Switch button requesting owner signature to call `POST /owner/pause`. *(Est: 4h)*
  - *Done When*: Signing emergency pause halts agent submissions in both contracts and API.

### Week 9: CI Benchmark Regression Gate & Integration Polish
- [ ] Update `.github/workflows/ci.yml` to include the automated benchmark evaluation regression gate running `python benchmarks/runner.py --dataset sample --depth standard --assert-thresholds`. *(Est: 5h)*
  - *Done When*: PRs that cause precision to drop below 75% or recall below 80% fail CI automatically.
- [ ] Polish UI responsive styling, dark mode theme, and error boundary handling. *(Est: 4h)*
  - *Done When*: Dashboard handles network dropouts gracefully without console errors.

### Week 10: Presentation Slides, Demo Rehearsal & Report Finalization
- [ ] Finalize live presentation slide deck skeleton and architecture graphics. *(Est: 5h)*
  - *Done When*: Presentation deck complete with problem statement, system architecture, benchmarks, and business model.
- [ ] Execute rehearsal of `docs/DEMO_SCRIPT.md` with team members including live trace viewer demonstration. *(Est: 5h)*
  - *Done When*: 5-minute live demo executes flawlessly from start to finish.

---

## 5. Suggested LLM Prompts
- **For Week 4 (Verified PoC Card Component)**:
  > *"Write a Tailwind CSS React component FindingCard in Next.js. If finding.verified is true, display a green 'Verified Exploit PoC' badge and an expandable tab showing the synthesized Foundry exploit test code from finding.poc_path. If finding.verified is false, show a muted 'Unverified' badge with a tooltip explaining that an automated exploit could not be synthesized."*
- **For Week 6 (Agent Trace Viewer Component)**:
  > *"Write a React component AgentTraceViewer in Next.js using Tailwind CSS. Given an array of StepTrace objects from GET /jobs/{id}/traces, render an interactive vertical timeline showing step_number, state badge (PLAN, ACT, OBSERVE, REPLAN, VERIFY), tool invoked, latency in ms, cost in USD, model used, and an expandable accordian showing the planner rationale."*
- **For Week 8 (Human Approval UI)**:
  > *"Write a React component PendingActionBanner in Next.js. If a job status is 'pending_approval', display the proposed action (e.g., 'Agent requested to hire peer reviewer for $12 USDC'), along with 'Approve' and 'Reject' buttons that post to /jobs/{id}/approve-action."*

---

## 6. Common Pitfalls & Security Notes
1. **Wallet Connection State**: Always handle edge cases where user is connected to the wrong chain (e.g. Ethereum Mainnet instead of Base Sepolia) and prompt network switch.
2. **Untrusted Code Rendering**: When displaying customer-submitted code, sanitized PoC tests, or LLM explanations in the browser, sanitize output to prevent Cross-Site Scripting (XSS).
3. **Trace Polling Efficiency**: When polling `GET /jobs/{id}/traces` in the dashboard, use exponential backoff or WebSocket/SSE to avoid hammering the agent API.
