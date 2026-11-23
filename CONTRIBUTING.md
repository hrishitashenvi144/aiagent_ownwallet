# Contributing Guidelines for AuditAgent

Welcome to the **AuditAgent** team! We use a strict Git Flow model to ensure seamless parallel execution among all 4 student engineers while maintaining clean integration.

---

## 1. Branch Strategy

The repository maintains two primary branches and four long-lived feature branches:

- **`main`**: Production-ready branch. Protected. Pushes and direct merges are strictly forbidden. Only tagged releases are merged here by the Lead Engineer.
- **`develop`**: Central integration branch. All feature branches merge into `develop` via Pull Requests. Protected against direct pushes.
- **`feat/contracts`**: Owned by Person 1 (Smart Contracts & On-chain Security).
- **`feat/analysis`**: Owned by Person 2 (Analysis Sandbox, LLM Triage & Reviewer Agent).
- **`feat/agent-core`**: Owned by Person 3 (Agent Core, x402 Paywall & Economic Brain).
- **`feat/dashboard`**: Owned by Person 4 (Next.js Dashboard & Security Attack Suite).

### Golden Rules:
1. **Never push directly to `main` or `develop`.**
2. Work only on your designated `feat/*` branch (or short-lived sub-branches off your feature branch).
3. **Rebase daily** from `develop` into your feature branch to keep your code up to date:
   ```bash
   git fetch origin
   git rebase origin/develop
   ```
4. Only the **Lead Engineer** has authority to approve and merge PRs into `develop` and `main`.

---

## 2. Shared Interfaces Protocol

Files in `shared/` (`shared/schemas/`, `shared/abis/`, `shared/openapi.yaml`) and `docs/INTERFACES.md` define the communication contracts between teammates.

- **Zero Silent Changes**: Never unilaterally modify a shared schema or ABI.
- **RFC Protocol**: If your feature requires modifying a shared schema, post the proposed diff in the team chat, open a dedicated interface PR with label `interface-change`, and request review from the Lead Engineer and affected team members.

---

## 3. Commit Message Standards

We enforce [Conventional Commits](https://www.conventionalcommits.org/):

Format:
```
<type>(<scope>): <short description>
```

Types:
- `feat`: New feature or capability
- `fix`: Bug fix
- `test`: Adding or updating tests
- `docs`: Documentation updates
- `refactor`: Code reorganization without behavior change
- `chore`: Tooling, dependency, or configuration updates

Examples:
- `feat(contracts): implement session key expiration check in AgentWallet`
- `fix(analysis): handle Slither AST parsing edge case for libraries`
- `test(agent): add test for 402 payment required header parsing`
- `docs(tasks): update milestone checklist for week 4`

---

## 4. Pull Request Requirements

Before opening a Pull Request into `develop`:
1. Ensure your branch is rebased on the latest `origin/develop`.
2. All unit tests and lint checks for your module must pass locally.
3. Fill out the PR template completely:
   - Summary of changes
   - Associated task checkbox references in `docs/tasks/`
   - Test confirmation
   - Secret check confirmation (no private keys or API tokens committed)
4. Every PR requires at least **1 approving review** before merging.
