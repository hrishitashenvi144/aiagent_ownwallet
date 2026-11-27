import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from fastapi import FastAPI, Header, HTTPException, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from agent.models import (
    QuoteRequest, QuoteResponse,
    JobCreateRequest, JobResponse,
    AgentStatusResponse, PauseRequest,
    StepTrace, ActionApprovalRequest, ActionApprovalResponse
)
from agent.web3_client import Web3Client
from agent.payment_verifier import (
    PaymentVerifier,
    PaymentVerificationError,
    ReplayAttackError,
    InvalidPaymentProofError
)

app = FastAPI(
    title="AuditAgent Service API",
    description="Autonomous AI blockchain security triage API with x402 payment integration and agentic tracing.",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for jobs, quotes, and traces (backed by SQLite in full implementation)
JOBS_DB: Dict[str, dict] = {}
TRACES_DB: Dict[str, List[dict]] = {}
PENDING_APPROVALS: Dict[str, dict] = {}

web3_client = Web3Client()
payment_verifier = PaymentVerifier(web3_client=web3_client)

AGENT_STATE = {
    "wallet_address": os.getenv("AGENT_WALLET_ADDRESS", "0x1234567890123456789012345678901234567890"),
    "usdc_token": os.getenv("USDC_TOKEN_ADDRESS", "0x036CbD53842c5426634e7929541eC2318f3dCF7e"),
    "usdc_balance": "150000000", # 150 USDC
    "daily_spent": "0",
    "daily_limit": "25000000",   # 25 USDC
    "is_paused": False,
    "start_time": datetime.now(timezone.utc)
}

def set_agent_contracts(wallet_address: str, usdc_token: str):
    """Update active contract addresses in agent state."""
    AGENT_STATE["wallet_address"] = wallet_address
    AGENT_STATE["usdc_token"] = usdc_token


PRICING_TABLE = {
    "quick": {"usdc": 10.0, "raw": "10000000", "time": 45},
    "standard": {"usdc": 15.0, "raw": "15000000", "time": 120},
    "deep": {"usdc": 30.0, "raw": "30000000", "time": 300}
}

def generate_default_traces(job_id: str) -> List[dict]:
    now = datetime.now(timezone.utc)
    return [
        {
            "step_number": 1,
            "state": "PLAN",
            "tool_call": None,
            "tool_input": None,
            "tool_output": None,
            "latency_ms": 320,
            "cost_usd": 0.001,
            "tokens_used": 450,
            "model_routed": "claude-3-5-haiku",
            "rationale": "Initial analysis: detected Vault contract archetype. Plan to invoke slither_static detector.",
            "timestamp": now.isoformat()
        },
        {
            "step_number": 2,
            "state": "ACT",
            "tool_call": "slither_static",
            "tool_input": {"contract_path": "contracts/Vulnerable.sol"},
            "tool_output": {"status": "success", "raw_issues_count": 2},
            "latency_ms": 1420,
            "cost_usd": 0.002,
            "tokens_used": 0,
            "model_routed": None,
            "rationale": "Executing slither_static inside isolated container (--network none).",
            "timestamp": (now + timedelta(seconds=1)).isoformat()
        },
        {
            "step_number": 3,
            "state": "OBSERVE",
            "tool_call": None,
            "tool_input": None,
            "tool_output": {"findings_normalized": 2},
            "latency_ms": 480,
            "cost_usd": 0.003,
            "tokens_used": 980,
            "model_routed": "claude-3-5-haiku",
            "rationale": "Parsed 1 Critical reentrancy candidate and 1 Low unchecked call. Routing Critical finding to VERIFY state.",
            "timestamp": (now + timedelta(seconds=2)).isoformat()
        },
        {
            "step_number": 4,
            "state": "VERIFY",
            "tool_call": "exploit_poc_runner",
            "tool_input": {"poc_name": "test/PoCReentrancy.t.sol", "test_function": "testExploit()"},
            "tool_output": {"compile": "ok", "test_passed": True, "balance_drained_eth": 10},
            "latency_ms": 2850,
            "cost_usd": 0.015,
            "tokens_used": 3200,
            "model_routed": "claude-3-5-sonnet",
            "rationale": "Synthesized and executed Foundry exploit PoC. State corruption verified! Setting verified=true and confidence=High.",
            "timestamp": (now + timedelta(seconds=5)).isoformat()
        },
        {
            "step_number": 5,
            "state": "COMPLETE",
            "tool_call": None,
            "tool_input": None,
            "tool_output": {"risk_score": 88.5, "verified_findings": 1},
            "latency_ms": 310,
            "cost_usd": 0.002,
            "tokens_used": 600,
            "model_routed": "claude-3-5-haiku",
            "rationale": "All candidate High/Critical findings verified. Assembling final ranked report.",
            "timestamp": (now + timedelta(seconds=6)).isoformat()
        }
    ]

@app.post("/quote", response_model=QuoteResponse)
def get_quote(payload: QuoteRequest):
    tier = PRICING_TABLE.get(payload.scan_depth, PRICING_TABLE["standard"])
    quote_id = f"quote-{uuid.uuid4().hex[:8]}"
    job_id = str(uuid.uuid4())
    expires = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    
    return QuoteResponse(
        quote_id=quote_id,
        job_id=job_id,
        scan_depth=payload.scan_depth,
        price_usdc=tier["usdc"],
        price_raw=tier["raw"],
        estimated_time_seconds=tier["time"],
        expires_at=expires,
        payment_recipient=AGENT_STATE["wallet_address"]
    )

@app.post("/jobs", status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreateRequest,
    x_payment_proof: Optional[str] = Header(None, alias="X-Payment-Proof")
):
    if AGENT_STATE["is_paused"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent is currently paused by owner override."
        )

    tx_hash = x_payment_proof or payload.payment_tx_hash
    tier = PRICING_TABLE.get(payload.scan_depth, PRICING_TABLE["standard"])
    now_iso = datetime.now(timezone.utc).isoformat()
    job_id = str(uuid.uuid4())

    # x402 Protocol: Check for payment proof
    if not tx_hash:
        headers = {
            "X-Accept-Token": AGENT_STATE["usdc_token"],
            "X-Payment-Address": AGENT_STATE["wallet_address"],
            "X-Required-Amount": tier["raw"]
        }
        content = {
            "error": "Payment Required",
            "job_id": job_id,
            "required_amount_usdc": tier["usdc"],
            "required_amount_raw": tier["raw"],
            "payment_address": AGENT_STATE["wallet_address"],
            "payment_token": AGENT_STATE["usdc_token"],
            "instructions": f"Transfer {tier['usdc']} USDC to payment_address on Base Sepolia with job_id in calldata or include tx_hash in X-Payment-Proof header."
        }
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content=content,
            headers=headers
        )

    # Verify payment proof & defend against replay attacks
    try:
        payment_verifier.verify(
            tx_hash=tx_hash,
            expected_recipient=AGENT_STATE["wallet_address"],
            expected_amount_raw=int(tier["raw"]),
            expected_job_id=job_id,
            allow_mock=True
        )
    except ReplayAttackError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Replay attack detected: {str(exc)}"
        )
    except (InvalidPaymentProofError, PaymentVerificationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment verification failed: {str(exc)}"
        )

    job_record = {
        "job_id": job_id,
        "status": "delivered",
        "customer_address": payload.customer_address,
        "contract_source": payload.contract_source,
        "scan_depth": payload.scan_depth,
        "quote_amount": tier["raw"],
        "tx_hash": tx_hash,
        "created_at": now_iso,
        "updated_at": now_iso,
        "error_message": None
    }
    JOBS_DB[job_id] = job_record
    TRACES_DB[job_id] = generate_default_traces(job_id)
    return job_record

@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str):
    if job_id not in JOBS_DB:
        raise HTTPException(status_code=404, detail="Job not found")
    return JOBS_DB[job_id]

@app.get("/jobs/{job_id}/report")
def get_job_report(job_id: str):
    from analysis.mock_runner import get_mock_report
    depth = JOBS_DB.get(job_id, {}).get("scan_depth", "standard")
    return get_mock_report(job_id=job_id, scan_depth=depth)

@app.get("/jobs/{job_id}/traces", response_model=List[StepTrace])
def get_job_traces(job_id: str):
    if job_id not in TRACES_DB:
        if job_id in JOBS_DB:
            TRACES_DB[job_id] = generate_default_traces(job_id)
        else:
            raise HTTPException(status_code=404, detail="Job traces not found")
    return TRACES_DB[job_id]

@app.post("/jobs/{job_id}/approve-action", response_model=ActionApprovalResponse)
def approve_action(job_id: str, payload: ActionApprovalRequest):
    if job_id not in JOBS_DB:
        raise HTTPException(status_code=404, detail="Job not found")
    status_str = "approved" if payload.approved else "rejected"
    PENDING_APPROVALS[payload.action_id] = {
        "job_id": job_id,
        "status": status_str,
        "operator_notes": payload.operator_notes
    }
    return ActionApprovalResponse(
        action_id=payload.action_id,
        status=status_str
    )

@app.get("/agent/status", response_model=AgentStatusResponse)
def get_agent_status():
    uptime = (datetime.now(timezone.utc) - AGENT_STATE["start_time"]).total_seconds()

    # Query live on-chain status if Web3 RPC is connected
    if web3_client.is_connected:
        try:
            onchain = web3_client.get_wallet_status(
                wallet_address=AGENT_STATE["wallet_address"],
                usdc_address=AGENT_STATE["usdc_token"]
            )
            AGENT_STATE["usdc_balance"] = onchain["usdc_balance"]
            AGENT_STATE["daily_spent"] = onchain["daily_spent"]
            AGENT_STATE["daily_limit"] = onchain["daily_cap"]
            AGENT_STATE["is_paused"] = onchain["is_paused"]
        except Exception:
            pass

    return AgentStatusResponse(
        status="paused" if AGENT_STATE["is_paused"] else "idle",
        wallet_address=AGENT_STATE["wallet_address"],
        usdc_balance=AGENT_STATE["usdc_balance"],
        daily_spent=AGENT_STATE["daily_spent"],
        daily_limit=AGENT_STATE["daily_limit"],
        is_paused=AGENT_STATE["is_paused"],
        active_jobs_count=len(JOBS_DB),
        uptime_seconds=uptime
    )

@app.post("/owner/pause")
def toggle_pause(payload: PauseRequest):
    if not payload.signature:
        raise HTTPException(status_code=403, detail="Signature required")
    AGENT_STATE["is_paused"] = payload.paused
    return {
        "status": "paused" if payload.paused else "active",
        "is_paused": payload.paused
    }
