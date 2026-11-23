import pytest
from fastapi.testclient import TestClient
from agent.main import app

client = TestClient(app)

def test_quote_endpoint():
    response = client.post("/quote", json={
        "contract_source": "pragma solidity ^0.8.20; contract Test {}",
        "scan_depth": "standard"
    })
    assert response.status_code == 200
    data = response.json()
    assert "quote_id" in data
    assert data["price_usdc"] == 15.0
    assert data["scan_depth"] == "standard"
    assert "expires_at" in data

def test_job_x402_payment_required():
    # Attempting to submit job without payment proof must return HTTP 402
    response = client.post("/jobs", json={
        "customer_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "contract_source": "pragma solidity ^0.8.20; contract Vulnerable {}",
        "scan_depth": "standard"
    })
    assert response.status_code == 402
    assert response.headers["X-Accept-Token"].startswith("0x")
    assert response.headers["X-Payment-Address"].startswith("0x")
    assert response.headers["X-Required-Amount"] == "15000000"
    
    data = response.json()
    assert data["error"] == "Payment Required"
    assert data["required_amount_usdc"] == 15.0

def test_job_submission_with_payment_proof_and_traces():
    # Submitting with payment proof proceeds to HTTP 201
    fake_tx = "0x" + "a" * 64
    response = client.post(
        "/jobs",
        json={
            "customer_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            "contract_source": "pragma solidity ^0.8.20; contract Vulnerable {}",
            "scan_depth": "quick"
        },
        headers={"X-Payment-Proof": fake_tx}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tx_hash"] == fake_tx
    job_id = data["job_id"]

    # Verify report endpoint
    report_res = client.get(f"/jobs/{job_id}/report")
    assert report_res.status_code == 200
    assert "findings" in report_res.json()
    assert report_res.json()["summary"]["total_verified"] >= 1

    # Verify execution traces endpoint
    traces_res = client.get(f"/jobs/{job_id}/traces")
    assert traces_res.status_code == 200
    traces = traces_res.json()
    assert len(traces) >= 3
    states = [t["state"] for t in traces]
    assert "PLAN" in states
    assert "ACT" in states
    assert "VERIFY" in states

    # Verify human approval endpoint
    approval_res = client.post(f"/jobs/{job_id}/approve-action", json={
        "action_id": "act-subagent-01",
        "approved": True,
        "operator_notes": "Approved for testing"
    })
    assert approval_res.status_code == 200
    assert approval_res.json()["status"] == "approved"

def test_agent_status_and_pause():
    status_res = client.get("/agent/status")
    assert status_res.status_code == 200
    assert "wallet_address" in status_res.json()

    # Toggle pause
    pause_res = client.post("/owner/pause", json={"paused": True, "signature": "0xownerSig"})
    assert pause_res.status_code == 200
    assert pause_res.json()["is_paused"] is True

    # Re-enable
    unpause_res = client.post("/owner/pause", json={"paused": False, "signature": "0xownerSig"})
    assert unpause_res.status_code == 200
    assert unpause_res.json()["is_paused"] is False
