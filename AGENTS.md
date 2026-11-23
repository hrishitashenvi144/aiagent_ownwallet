# Rules and Instructions for AI Coding Assistants in AuditAgent

Welcome, AI Assistant! You are supporting a university engineering team building **AuditAgent**—an autonomous AI agent operating as a smart contract security triage business on Base Sepolia.

To ensure smooth collaboration across all four student engineers and prevent git conflicts or broken interfaces, you **MUST** strictly follow the guidelines below.

---

## 1. Persona and Mode Identification

Whenever a user starts a conversation in this repository:
1. **Identify the Teammate**: Check if the user specified their role. If not stated, ask immediately:
   > *"Which team member are you working as? (Person 1: Contracts, Person 2: Analysis, Person 3: Agent Core, Person 4: Dashboard & Security)?"*
2. **Read Required Context**:
   - Relevant person task file: `docs/tasks/PERSON_<N>_*.md`
   - Master implementation plan: `docs/BUILD_GUIDE.md`
   - Technical interface definitions: `docs/INTERFACES.md`
3. **Offer Interaction Modes**:
   - **BUILD Mode**: You generate clean code, write tests, and assist in implementation.
   - **GUIDE Mode**: You explain architectural concepts, provide pseudo-code, and mentor the student to implement the solutions themselves.
   Ask which mode the user prefers.

---

## 2. Directory Ownership and Boundary Enforcement

Every team member owns a specific directory. You must **NEVER** edit files outside of the active member's owned scope without explicit coordination:

| Person | Owned Directories & Files | Must Not Edit Directly |
|---|---|---|
| **Person 1** | `contracts/`, `shared/abis/` | `analysis/`, `agent/`, `dashboard/` |
| **Person 2** | `analysis/`, `benchmarks/` | `contracts/`, `agent/`, `dashboard/` |
| **Person 3** | `agent/` | `contracts/`, `analysis/`, `dashboard/` |
| **Person 4** | `dashboard/`, `security-tests/`, `docs/DEMO_SCRIPT.md` | `contracts/`, `analysis/`, `agent/` |

### Strict Interface Protocol:
The folder `shared/schemas/` and the contract document `docs/INTERFACES.md` represent the shared contracts between all modules. If an interface change is needed:
- **Do not modify `shared/` silently.**
- Draft the proposed modification and instruct the user to discuss with the Lead Engineer and submit a formal PR.

---

## 3. Git Branching & Commit Discipline

- Ensure work occurs on the person's designated feature branch:
  - Person 1: `feat/contracts`
  - Person 2: `feat/analysis`
  - Person 3: `feat/agent-core`
  - Person 4: `feat/dashboard`
- **Never push or commit directly to `main` or `develop`.**
- Break down changes into small, atomic commits using [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`.
- Rebase from `develop` regularly to stay synchronized.

---

## 4. Task Execution & Educational Explanations

- Follow the checklist in `docs/tasks/PERSON_<N>_*.md` sequentially. Do not skip tasks.
- For every completed task, remind the user to mark the checkbox `[x]` in their task file.
- **Always write and run tests** for any new capability before marking a task complete.
- **Explain concepts clearly**: The team members are university students. Provide concise explanations of why an architectural pattern or library was selected, and explain security tradeoffs.

---

## 5. Security & Safety Guardrails

1. **No Real Funds / Testnet Only**:
   - All blockchain activity is restricted to Base Sepolia testnet.
   - Never reference or use mainnet RPCs or real currency.
2. **Credential Hygiene**:
   - Never hardcode or commit private keys, API keys, or secrets into source files.
   - Always load credentials from `.env` using environment variables.
   - Use dummy private keys for local Anvil tests.
3. **Prompt Injection & Untrusted Code Defense**:
   - Any Solidity code submitted by users for analysis must be treated as **completely untrusted data**.
   - Never execute customer Solidity code directly on host machines.
   - Never feed customer code directly into LLM prompts without clear system boundaries and anti-jailbreak sanitization.
   - All static analysis tools must execute inside isolated, non-networked Docker containers with enforced memory and CPU limits.
