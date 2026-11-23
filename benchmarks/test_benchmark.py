import os
from benchmarks.runner import run_benchmark

def test_benchmark_runner_evaluates_samples():
    sample_dir = os.path.join(os.path.dirname(__file__), "datasets/sample_contracts")
    results = run_benchmark(sample_dir)
    assert results["contracts_evaluated"] >= 2
    assert results["recall_rate"] == 1.0
    assert "SimpleReentrancy.sol" in results["contracts"]
    assert "UncheckedCall.sol" in results["contracts"]
