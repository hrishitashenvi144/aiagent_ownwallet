import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
from fastapi import FastAPI, Header, HTTPException, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from agent.models import (
    QuoteRequest, QuoteResponse,
    JobCreateRequest, JobResponse,
    AgentStatusResponse, PauseRequest
)

app = FastAPI(
    title="AuditAgent Service API",
    description="Autonomous AI blockchain security triage API with x402 payment integration.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for jobs and quotes (backed by SQLite in full implementation)
JOBS_DB: Dict[str, dict] = {}
AGENT_STATE = {
    "wallet_address": os.getenv("AGENT_WALLET_ADDRESS", "0x1234567890123456789012345678901234567890"),
    "usdc_token": os.getenv("USDC_TOKEN_ADDRESS", "0x036CbD53842c5426634e7929541eC2318f3dCF7e"),
    "usdc_balance": "150000000", # 150 USDC
    "daily_spent": "0",
    "daily_limit": "25000000",   # 25 USDC
    "is_paused": False,
    "start_time": datetime.now(timezone.utc)
}

PRICING_TABLE = {
    "quick": {"usdc": 10.0, "raw": "10000000", "time": 45},
    "standard": {"usdc": 15.0, "raw": "15000000", "time": 120},
    "deep": {"usdc": 30.0, "raw": "30000000", "time": 300}
}

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

    # In mock/test mode: valid tx_hash marks job as paid and starts analysis
    job_record = {
        "job_id": job_id,
        "status": "delivered", # Delivered for immediate demo availability
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
    return job_record

@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str):
    if job_id not in JOBS_DB:
        raise HTTPException(status_code=404, detail="Job not found")
    return JOBS_DB[job_id]

@app.get("/jobs/{job_id}/report")
def get_job_report(job_id: str):
    # Try importing real analysis mock runner
    from analysis.mock_runner import get_mock_report
    depth = JOBS_DB.get(job_id, {}).get("scan_depth", "standard")
    return get_mock_report(job_id=job_id, scan_depth=depth)

@app.get("/agent/status", response_model=AgentStatusResponse)
def get_agent_status():
    uptime = (datetime.now(timezone.utc) - AGENT_STATE["start_time"]).total_seconds()
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
    # In production, verify EIP-712 signature against OWNER_ADDRESS
    if not payload.signature:
        raise HTTPException(status_code=403, detail="Signature required")
    AGENT_STATE["is_paused"] = payload.paused
    return {
        "status": "paused" if payload.paused else "active",
        "is_paused": payload.paused
    }
