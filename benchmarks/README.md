# AuditAgent Benchmark Datasets & Runner (Person 2)

This directory contains curated datasets of vulnerable Solidity contracts and evaluation harnesses to assess detection recall, precision, and false-positive reduction rates.

## Datasets
- `datasets/sample_contracts/`: Canonical test contracts (Reentrancy, Unchecked Call, Integer Issues).
- Future additions: SWC Registry subset (30 contracts), Damn Vulnerable DeFi challenges.

## Running Benchmarks
```bash
python runner.py --dataset sample --depth standard
```
Results are saved to `benchmarks/results/`.
