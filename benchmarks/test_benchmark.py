import os
from benchmarks.runner import run_benchmark

def test_benchmark_runner_evaluates_samples():
    sample_dir = os.path.join(os.path.dirname(__file__), "datasets/sample_contracts")
    results = run_benchmark(sample_dir, compare_baselines=True, assert_thresholds=True)
    
    agentic = results["auditagent_agentic"]
    assert agentic["contracts_evaluated"] >= 2
    assert agentic["precision"] >= 0.85
    assert agentic["recall"] >= 0.80
    assert agentic["false_positive_rate"] <= 0.15
    assert agentic["exploit_verification_rate"] >= 0.70
    assert "SimpleReentrancy.sol" in agentic["contracts"]

    # Verify baseline comparisons are present
    baselines = results["baselines"]
    assert "slither_alone" in baselines
    assert "raw_llm_alone" in baselines
    assert "pipeline_unverified" in baselines
    assert baselines["slither_alone"]["false_positive_rate"] > agentic["false_positive_rate"]
