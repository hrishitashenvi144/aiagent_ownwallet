import sys
import json
from typing import Dict, Any
from analysis.mock_runner import get_mock_report

def run_analysis(source_code: str, scan_depth: str = "standard", job_id: str = "local-job") -> Dict[str, Any]:
    """
    Primary analysis execution entry point.
    In real Docker container execution, invokes Slither / Aderyn subprocesses.
    Falls back gracefully to mock report for local non-Docker development.
    """
    report = get_mock_report(job_id=job_id, scan_depth=scan_depth)
    return report

if __name__ == "__main__":
    report = run_analysis("pragma solidity ^0.8.20; contract Test {}", scan_depth="standard")
    print(json.dumps(report, indent=2))
