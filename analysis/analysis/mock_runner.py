from datetime import datetime, timezone
from typing import Dict, Any, List

def get_mock_findings() -> List[Dict[str, Any]]:
    return [
        {
            "id": "SWC-107-001",
            "title": "Reentrancy in withdrawBalance()",
            "severity": "Critical",
            "confidence": "High",
            "location": {
                "file": "contracts/Vulnerable.sol",
                "contract_name": "VulnerableVault",
                "function_name": "withdrawBalance()",
                "start_line": 24,
                "end_line": 31
            },
            "evidence": "msg.sender.call{value: balance}(\"\"); userBalances[msg.sender] = 0;",
            "explanation": "State variable userBalances is modified after external call to msg.sender, permitting recursive reentrancy exploit.",
            "suggested_fix": "Apply Checks-Effects-Interactions pattern or inherit OpenZeppelin ReentrancyGuard.",
            "tool_source": "slither",
            "poc_test_path": "test/PoCReentrancy.t.sol"
        },
        {
            "id": "SWC-104-002",
            "title": "Unchecked Return Value of External Transfer",
            "severity": "Low",
            "confidence": "Medium",
            "location": {
                "file": "contracts/Vulnerable.sol",
                "contract_name": "VulnerableVault",
                "function_name": "transferFee()",
                "start_line": 45,
                "end_line": 47
            },
            "evidence": "token.transfer(feeCollector, amount);",
            "explanation": "Return value of ERC20 transfer is ignored. Some tokens (e.g. USDT) do not revert on failure.",
            "suggested_fix": "Use OpenZeppelin SafeERC20.safeTransfer instead.",
            "tool_source": "aderyn"
        }
    ]

def get_mock_report(job_id: str = "mock-job-123", scan_depth: str = "standard") -> Dict[str, Any]:
    findings = get_mock_findings()
    return {
        "job_id": job_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scan_depth": scan_depth,
        "target_contract": "VulnerableVault",
        "summary": {
            "risk_score": 88.5,
            "total_critical": 1,
            "total_high": 0,
            "total_medium": 0,
            "total_low": 1,
            "total_informational": 0
        },
        "findings": findings,
        "triage_notes": "Automated triage detected 1 confirmed Critical reentrancy vulnerability. State update occurs post-call without protection.",
        "second_opinion": {
            "reviewer_address": "0xReviewerAgentStubAddress7777777777777777",
            "escrow_id": "0xescrow1234567890",
            "consensus_score": 95.0,
            "notes": "Secondary peer reviewer concurs with critical classification on reentrancy."
        },
        "gas_report": {
            "hotspots": [
                {
                    "function": "withdrawBalance()",
                    "estimated_gas": 45000,
                    "suggestion": "Cache storage read in local stack memory."
                }
            ]
        }
    }
