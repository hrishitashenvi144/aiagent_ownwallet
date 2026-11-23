from typing import Dict, Any, List

class FindingsNormalizer:
    """Normalizes raw Slither and Aderyn findings into canonical Finding objects."""

    @staticmethod
    def normalize_slither_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
        check = issue.get("check", "unknown-vuln")
        impact = issue.get("impact", "Informational")
        confidence = issue.get("confidence", "Medium")
        description = issue.get("description", "Potential vulnerability detected by Slither.")
        
        # Map severity to schema enum
        severity_map = {
            "High": "High",
            "Medium": "Medium",
            "Low": "Low",
            "Informational": "Informational",
            "Optimization": "Informational"
        }
        mapped_severity = severity_map.get(impact, "Medium")
        if mapped_severity == "High" and ("reentrancy" in check.lower() or "suicide" in check.lower()):
            mapped_severity = "Critical"

        location = {
            "file": issue.get("first_markdown_element", "contract.sol"),
            "contract_name": "UnknownContract",
            "function_name": "unknown()",
            "start_line": 1,
            "end_line": 10
        }

        elements = issue.get("elements", [])
        if elements:
            first_elem = elements[0]
            source_mapping = first_elem.get("source_mapping", {})
            lines = source_mapping.get("lines", [1])
            location["start_line"] = lines[0] if lines else 1
            location["end_line"] = lines[-1] if lines else 1
            if "name" in first_elem:
                location["function_name"] = first_elem["name"]

        return {
            "id": f"SLITHER-{check.upper()}",
            "title": f"Slither: {check}",
            "severity": mapped_severity,
            "confidence": confidence if confidence in ["High", "Medium", "Low"] else "Medium",
            "location": location,
            "evidence": description[:200],
            "explanation": description,
            "suggested_fix": "Review Slither detector recommendations and verify access controls / state ordering.",
            "tool_source": "slither"
        }
