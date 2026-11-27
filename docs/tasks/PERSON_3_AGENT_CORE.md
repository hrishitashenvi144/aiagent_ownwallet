# Person 3: Agent Core, Cognitive State Machine, Memory & x402 Paywall

## 1. Role Summary & Folder Ownership
- **Role Summary**: You architect the autonomous cognitive brain of AuditAgent. You are responsible for the FastAPI REST gateway, the **LangGraph Plan -> Act -> Observe -> Replan state machine**, per-job step/token/budget limits, the Tool Registry dispatcher, structured output validation with retry loops, persistent **Agent Memory**, execution **Observability Tracing**, human-in-the-loop approval endpoints, on-chain `web3.py` payment verification, and dynamic model routing.
- **Branch**: `feat/agent-core`
- **Owned Folders & Files**:
  - `agent/` (all FastAPI application code, LangGraph state engine, database models, worker queues, web3 connectors, trace loggers)
- **MUST NOT EDIT**:
  - `contracts/` (Person 1)
  - `analysis/` (Person 2)
  - `dashboard/` (Person 4)
  - `shared/schemas/` (Requires Lead RFC)

---

## 2. Interfaces You Implement & Consume
- **Implement**:
  - All endpoints specified in `shared/openapi.yaml`:
    - `POST /quote`: Calculate price based on code size, depth tier, and historical memory.
    - `POST /jobs`: Accept job submissions; enforce HTTP 402 when unpaid; verify payment when proof is supplied; trigger agent loop.
    - `GET /jobs/{id}`: Return job lifecycle state.
    - `GET /jobs/{id}/report`: Return finished report.
    - `GET /jobs/{id}/traces`: Return full execution trace list (`StepTrace`).
    - `POST /jobs/{id}/approve-action`: Human-in-the-loop approval for risky/high-cost actions.
    - `GET /agent/status`: Return treasury balance, daily spent, and pause flag.
    - `POST /owner/pause`: Process owner signature to toggle agent pause state.
  - **Cognitive State Machine**: LangGraph state machine enforcing max 10 steps, 100k tokens, and budget limit.
  - **Persistent Agent Memory**: Tables for `job_outcomes`, `tool_precision_matrix`, and `tier_cost_history`.
- **Consume**:
  - `analysis.runner.run_analysis` and Tool Registry handlers from Person 2.
  - Contract ABIs in `shared/abis/` (`AgentWallet.json`, `Escrow.json`) via `web3.py` on Base Sepolia.
- **Reference**: Detailed specs are in [INTERFACES.md](../INTERFACES.md) and `shared/openapi.yaml`.

---

## 3. Dependencies & Mocks
- **Before Person 1 deploys contracts**: Use local Anvil stub contracts or `agent/tests/mock_web3.py` for transaction receipt verification.
- **Before Person 2 finishes Docker tools**: Use `analysis/analysis/mock_runner.py` for agent loop verification.
- **Person 4 depends on you**: Person 4 needs your API endpoints and `/traces` to build the dashboard. Keep `agent/agent/mock_server.py` functioning from Day 1.

---

## 4. Week-by-Week Task Checklist (10 Weeks)

### Week 1: FastAPI Scaffold, SQLite Models & Memory Tables
- [ ] Initialize FastAPI project with SQLAlchemy models in `agent/agent/models.py`:
  - `Job`, `Quote`, `TransactionRecord`
  - Agent Memory tables: `job_outcomes`, `tool_precision_matrix`, `tier_cost_history`
  - Trace table: `step_traces` *(Est: 5h)*
  - *Done When*: SQLite DB initializes all operational and memory tables on startup.
- [ ] Implement `agent/agent/mock_server.py` returning static responses according to `shared/openapi.yaml` (including `/traces`) for Person 4. *(Est: 3h)*
  - *Done When*: Dashboard can fetch mock quotes, reports, and execution traces.

### Week 2: x402 Paywall & Memory-Calibrated Quoting
- [x] Implement `POST /quote` querying `tier_cost_history` in Agent Memory to dynamically calculate USDC prices targeting a $\ge 40\%$ gross margin. *(Est: 5h)*
  - *Done When*: Endpoint returns valid `Quote` object adhering to `shared/schemas/quote.json`.
- [x] Implement x402 response on `POST /jobs` returning HTTP 402 with `X-Accept-Token`, `X-Payment-Address`, and `X-Required-Amount` headers when payment proof is missing. *(Est: 5h)*
  - *Done When*: Unpaid submissions return status code 402 and payment instructions.

### Week 3: On-Chain Payment Verification with web3.py
- [x] Implement `agent/agent/payment_verifier.py` using `web3.py` to inspect Base Sepolia transactions. *(Est: 6h)*
  - *Done When*: Verifier confirms recipient matches `AGENT_WALLET_ADDRESS`, token matches USDC, amount matches quote, and logs contain `job_id`.
- [x] Prevent replay attacks by asserting transaction hashes are strictly unique in SQLite. *(Est: 4h)*
  - *Done When*: Reused transaction hash returns HTTP 409 Conflict.

### Week 4: LangGraph Agent Loop State Machine (Milestone 1)
- [ ] Implement the cognitive state machine (`PLAN` -> `ACT` -> `OBSERVE` -> `REPLAN`) using LangGraph or deterministic state graph. *(Est: 8h)*
  - *Done When*: State machine iterates across states, records transitions, and halts at `COMPLETE`.
- [ ] Implement hard per-job safety limits:
  - Step counter ceiling: $\le 10$ steps.
  - Token ceiling: $\le 100,000$ tokens.
  - Budget ceiling: $\le 70\%$ of payment received. *(Est: 4h)*
  - *Done When*: Exceeding any limit immediately transitions to `TERMINATE_LIMIT_EXCEEDED`.

### Week 5: Tool Registry Dispatcher & Structured Output Retry Loop
- [ ] Implement the `ToolDispatcher` verifying registered tool schemas and timeouts prior to execution. *(Est: 6h)*
  - *Done When*: Unregistered tools or invalid parameters are rejected before execution.
- [ ] Implement structured output validator with a 3-attempt repair loop feeding validation errors back to the model. *(Est: 5h)*
  - *Done When*: Schema non-compliance triggers automatic repair; fallback parses partial output safely.

### Week 6: End-to-End Paid Agentic Pipeline (Milestone 2)
- [ ] Connect agent loop to Person 2's containerized static tools and `exploit_poc_runner`. *(Est: 6h)*
  - *Done When*: High/Critical findings trigger `VERIFY` state and invoke exploit synthesis.
- [ ] Implement dynamic Model Router: Route cheap model (Claude 3.5 Haiku) for triage/formatting and strong model (Claude 3.5 Sonnet) for exploit synthesis. *(Est: 4h)*
  - *Done When*: Traces reflect model routing by task complexity.

### Week 7: Persistent Memory Updates & Multi-Agent Escrow
- [ ] Update `tool_precision_matrix` and `job_outcomes` at the end of every completed job to refine historical accuracy per archetype. *(Est: 5h)*
  - *Done When*: Memory tables reflect verified vs. unverified findings and realized profit.
- [x] Wire multi-agent escrow subcontracting tool (`subagent_escrow_hire`) using session keys on `Escrow.sol` for `deep` tier jobs. *(Est: 5h)*
  - *Done When*: Bounty is deposited on Base Sepolia and released upon consensus delivery.

### Week 8: Observability Traces & Human-in-the-Loop Approvals
- [ ] Implement `StepTrace` logger recording every step (tool call, latency, cost, rationale) and expose via `GET /jobs/{id}/traces`. *(Est: 5h)*
  - *Done When*: API returns ordered execution traces matching `shared/openapi.yaml`.
- [ ] Implement `POST /jobs/{id}/approve-action` to pause execution for high-risk actions (e.g. escrow bounty > $10) and await human signature. *(Est: 5h)*
  - *Done When*: Agent pauses at approval gate and resumes only after approved request.

### Week 9: System Hardening & RPC Resilience
- [ ] Implement exponential backoff for Base Sepolia RPC calls and LLM API requests. *(Est: 5h)*
  - *Done When*: Temporary RPC disconnects do not drop or corrupt active jobs.
- [ ] Implement crash recovery: unhandled exceptions during tool execution transition job to `failed` and record error trace. *(Est: 4h)*
  - *Done When*: Zero hanging jobs in `analyzing` state.

### Week 10: Performance Profiling, Viva & Code Freeze
- [ ] Profile memory usage, SQLite query indexing, and trace logging latency. *(Est: 5h)*
  - *Done When*: End-to-end execution completes smoothly with clean telemetry logs for presentation.

---

## 5. Suggested LLM Prompts
- **For Week 4 (LangGraph State Machine)**:
  > *"Write a Python LangGraph state graph for an autonomous security agent. The state object holds contract_source, plan, step_count (max 10), tokens_used (max 100k), budget_remaining, findings list, and traces list. Define nodes for plan_step, act_step, observe_step, replan_step, and verify_step, with conditional edges routing to TERMINATE_LIMIT_EXCEEDED when limits are reached."*
- **For Week 5 (Structured Output Retry Loop)**:
  > *"Write a Python function call_structured_llm(prompt, schema, max_retries=3). Call Anthropic API with JSON mode. If jsonschema.validate fails, re-prompt the LLM with the validation error message and request a schema-compliant fix. Return parsed dict or trigger fallback parser."*
- **For Week 8 (Trace Logger)**:
  > *"Write an async execution trace recorder in FastAPI using SQLAlchemy. For every state machine step, log step_number, state, tool_call, tool_input, tool_output, latency_ms, cost_usd, model_routed, and planner rationale into a step_traces table. Create GET /jobs/{id}/traces endpoint."*

---

## 6. Common Pitfalls & Security Notes
1. **Infinite Agent Loops**: Always enforce the hard step limit of 10 cycles. Never allow unbounded replanning.
2. **Replay Attacks**: Ensure payment transaction hashes are uniquely constrained in SQLite.
3. **Budget Runaways**: In `REPLAN`, immediately terminate the loop if cumulative LLM/tool cost reaches 70% of the customer's payment quote.
