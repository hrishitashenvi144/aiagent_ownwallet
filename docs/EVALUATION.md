# AuditAgent Evaluation & Benchmark Methodology

This document specifies the metrics, labeled datasets, baselines, and evaluation harness used to measure vulnerability detection efficacy, verification reliability, and economic sustainability of the AuditAgent agentic system.

---

## 1. Labeled Evaluation Datasets

The evaluation suite tests the complete autonomous agent loop across four canonical smart contract security datasets stored in `benchmarks/datasets/`:

1. **SWC Registry Curated Benchmark (Smart Contract Weakness Classification)**:
   - 30 standardized contracts covering vulnerability archetypes:
     - SWC-107: Reentrancy (The DAO pattern, cross-function reentrancy)
     - SWC-101: Integer Arithmetic Overflow/Underflow
     - SWC-104: Unchecked Low-Level Call Return Value
     - SWC-105: Unprotected Ether Withdrawal
     - SWC-106: Unprotected SELFDESTRUCT
     - SWC-115: Authorization through `tx.origin`
2. **SmartBugs Curated Subset**:
   - 20 historical contracts with ground-truth real-world exploits.
3. **Damn Vulnerable DeFi (v4)**:
   - Complex multi-contract DeFi architectures: Unstoppable, Naive Receiver, Truster, Free Rider.
4. **Ethernaut Security Challenges**:
   - Puzzles evaluating edge-case logic flaws: Fallback, CoinFlip, Telephone, Token, Delegation, Reentrancy.

---

## 2. Evaluation Metrics

### 2.1 Security & Verification Metrics
- **Recall (Sensitivity)**:
  $$\text{Recall} = \frac{\text{True Positives}}{\text{True Positives} + \text{False Negatives}}$$
  *Target*: $\ge 80\%$ on known Critical and High vulnerabilities.
- **Precision**:
  $$\text{Precision} = \frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}}$$
  *Target*: $\ge 85\%$ across all reported findings.
- **False Positive Rate (FPR)**:
  $$\text{FPR} = \frac{\text{False Positives}}{\text{False Positives} + \text{True Negatives}}$$
  *Target*: $\le 15\%$ after Verify-Before-Report validation.
- **Exploit Verification Rate (EVR)**:
  $$\text{EVR} = \frac{\text{True Positives with Executed Passing Foundry PoC}}{\text{Total Critical/High True Positives}}$$
  *Target*: $\ge 70\%$ of confirmed Critical/High vulnerabilities backed by passing Foundry tests.

### 2.2 Economic & Operational Performance
- **Token Efficiency & Step Convergence**: Average steps per job (target $\le 6$ steps) and token count (target $\le 45,000$ tokens for standard tier).
- **Execution Cost**: Realized API + compute cost per job in USD.
- **Gross Profit Margin**: Percentage of customer USDC payment retained in `AgentWallet`:
  $$\text{Margin} = \frac{\text{Price Paid} - \text{Incurred Cost}}{\text{Price Paid}} \times 100$$
  *Target*: $\ge 40\%$ net operating margin.

---

## 3. Comparative Baselines

AuditAgent is evaluated against three distinct baselines to isolate the contribution of each architectural layer:

| System / Pipeline | Architecture & Capabilities | Expected Precision | Expected Recall | FPR | Cost / Job | Verified PoCs? |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Baseline 1: Slither Alone** | Standalone static AST detector | 38% | 85% | 62% | $0.002 | No |
| **Baseline 2: Raw LLM Alone** | Zero-shot prompt with contract source | 45% | 60% | 55% | $0.08 | No (Hallucinations) |
| **Baseline 3: Pipeline Without Verification** | Slither + Aderyn + LLM Triage (No PoC execution) | 72% | 82% | 28% | $0.15 | No |
| **AuditAgent (Proposed)** | LangGraph loop + Tool Registry + Verify-Before-Report + Model Router | **92%** | **84%** | **8%** | **$0.22** | **Yes (100% of Verified)** |

---

## 4. Benchmark Execution Harness (`benchmarks/`)

The evaluation harness in `benchmarks/runner.py` runs the entire agent end-to-end on each dataset contract:
1. Simulates customer submission and payment quote.
2. Initializes the agent loop (`PLAN` -> `ACT` -> `OBSERVE` -> `REPLAN`).
3. Executes registered tools (`slither_static`, `aderyn_static`, `exploit_poc_runner`).
4. Generates a consolidated benchmark report saved to `benchmarks/results/benchmark_report.json` and a formatted summary table.

### CLI Usage:
```bash
# Run benchmark on sample contracts with baseline comparison
python benchmarks/runner.py --dataset sample --compare-baselines --depth standard

# Run full evaluation across SWC benchmark
python benchmarks/runner.py --dataset swc --depth deep
```

---

## 5. Continuous Integration (CI) Regression Gate

To prevent quality degradation as team members introduce changes, `.github/workflows/ci.yml` runs an automated regression check on every pull request into `develop`:

```yaml
- name: Run Agent Benchmark Regression Check
  run: |
    python benchmarks/runner.py --dataset sample --depth standard --assert-thresholds
```

### Automated Failure Conditions:
- Recall drops below **80%**.
- Precision drops below **75%**.
- Average execution cost per standard job exceeds **$0.50 USD**.
- Any unverified finding is marked with `confidence: "High"` (violates Verify-Before-Report invariant).
