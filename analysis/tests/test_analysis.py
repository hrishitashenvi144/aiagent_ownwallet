import json
import os
import pytest
from analysis.mock_runner import get_mock_report, get_mock_findings
from analysis.normalizer import FindingsNormalizer
from analysis.runner import run_analysis

def test_mock_report_structure():
    report = get_mock_report(job_id="test-job-42", scan_depth="deep")
    assert report["job_id"] == "test-job-42"
    assert report["scan_depth"] == "deep"
    assert "summary" in report
    assert report["summary"]["risk_score"] > 0
    assert len(report["findings"]) > 0

def test_findings_normalizer():
    dummy_slither = {
        "check": "reentrancy-eth",
        "impact": "High",
        "confidence": "High",
        "description": "Reentrancy detected in Vulnerable.withdraw()",
        "elements": [
            {
                "name": "withdraw",
                "source_mapping": {"lines": [20, 25]}
            }
        ]
    }
    normalized = FindingsNormalizer.normalize_slither_issue(dummy_slither)
    assert normalized["tool_source"] == "slither"
    assert normalized["severity"] == "Critical"
    assert normalized["location"]["start_line"] == 20
    assert normalized["location"]["end_line"] == 25

def test_runner_returns_valid_payload():
    result = run_analysis("pragma solidity ^0.8.20; contract Test {}", scan_depth="quick", job_id="quick-job")
    assert result["job_id"] == "quick-job"
    assert result["scan_depth"] == "quick"
    assert isinstance(result["findings"], list)
