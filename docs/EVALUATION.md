# AuditAgent Evaluation & Benchmark Methodology

This document specifies the metrics, datasets, baselines, and evaluation protocols used to measure the security efficacy, economic viability, and performance of AuditAgent.

---

## 1. Evaluation Datasets

The analysis engine and LLM triage pipeline are evaluated across four canonical smart contract security datasets stored in `benchmarks/datasets/`:

1. **SWC Registry Benchmark (Smart Contract Weakness Classification)**:
   - 30 curated test contracts covering common vulnerability archetypes:
     - SWC-107: Reentrancy
     - SWC-101: Integer Overflow and Underflow
     - SWC-104: Unchecked Call Return Value
     - SWC-105: Unprotected Ether Withdrawal
     - SWC-115: Authorization through tx.origin
2. **SmartBugs Curated Subset**:
   - 20 historical contracts with ground-truth real-world exploits (The DAO, King of the Ether, etc.).
3. **Damn Vulnerable DeFi (v4)**:
   - Challenges evaluating multi-contract interactions: Unstoppable, Naive Receiver, Truster, Free Rider.
4. **Ethernaut Challenges**:
   - Selected puzzles: Fallback, CoinFlip, Telephone, Token, Delegation, Re-entrancy.

---

## 2. Evaluation Metrics

### 2.1 Vulnerability Detection Performance
- **Recall (Sensitivity)**:
  $$\text{Recall} = \frac{\text{True Positives}}{\text{True Positives} + \text{False Negatives}}$$
  *Target*: $\ge 80\%$ on known critical and high vulnerabilities.
- **Precision**:
  $$\text{Precision} = \frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}}$$
  *Target*: $\ge 75\%$ after LLM triage and false-positive filtering.
- **False Positive Reduction Rate**:
  $$\text{FPR Reduction} = 1 - \frac{\text{FP}_{\text{post-LLM}}}{\text{FP}_{\text{raw-static}}}$$
  *Target*: $\ge 60\%$ reduction in raw static analysis noise.
- **PoC Exploit Synthesis Rate**:
  Percentage of flagged Critical vulnerabilities for which an LLM-synthesized Foundry fuzz test successfully passes/fails demonstrating exploitability. *Target*: $\ge 50\%$.

### 2.2 Economic & Operational Performance
- **Quoting Accuracy**: Margin variance between estimated compute/token costs and actual costs.
- **Profitability**: Net profit retained in `AgentWallet` after subtracting LLM API costs and reviewer bounties.
- **Scan Latency**: Total execution time from payment confirmation to report delivery:
  - Quick tier: $< 60\text{s}$
  - Standard tier: $< 180\text{s}$
  - Deep tier: $< 400\text{s}$

---

## 3. Comparative Baselines

AuditAgent is benchmarked against three distinct baselines:

| System / Pipeline | Tooling | Strengths | Weaknesses |
|---|---|---|---|
| **Baseline 1: Slither Only** | Raw static analysis | Fast, deterministic AST rules | High false positive rate, no natural language explanation |
| **Baseline 2: Aderyn Only** | Rust static analyzer | High performance, modern detectors | Misses complex cross-function logic flaws |
| **Baseline 3: Naive LLM** | Direct prompt with source code | Readable explanations | High hallucination rate, blind to deep bytecode mechanics |
| **AuditAgent (Proposed)** | Sandboxed Slither + Aderyn + LLM Triage + Foundry Fuzz + Reviewer Escrow | High recall, verified PoCs, low noise, economic sustainability | Higher latency than raw static tools |

---

## 4. Benchmark Execution Harness

The benchmark harness is located in `benchmarks/runner/`. To run the evaluation:
```bash
python benchmarks/runner/run_benchmarks.py --dataset swc --depth standard
```
The script outputs precision, recall, execution timings, and generates a formatted Markdown report in `benchmarks/results/`.
