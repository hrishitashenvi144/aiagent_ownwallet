from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class QuoteRequest(BaseModel):
    contract_source: str
    scan_depth: str = Field(default="standard", pattern="^(quick|standard|deep)$")

class QuoteResponse(BaseModel):
    quote_id: str
    job_id: str
    scan_depth: str
    price_usdc: float
    price_raw: str
    estimated_time_seconds: int
    expires_at: str
    payment_recipient: str

class JobCreateRequest(BaseModel):
    customer_address: str
    contract_source: str
    scan_depth: str = Field(default="standard", pattern="^(quick|standard|deep)$")
    payment_tx_hash: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    status: str
    customer_address: str
    contract_source: str
    scan_depth: str
    quote_amount: str
    tx_hash: Optional[str] = None
    created_at: str
    updated_at: str
    error_message: Optional[str] = None

class AgentStatusResponse(BaseModel):
    status: str
    wallet_address: str
    usdc_balance: str
    daily_spent: str
    daily_limit: str
    is_paused: bool
    active_jobs_count: int
    uptime_seconds: float

class PauseRequest(BaseModel):
    paused: bool
    signature: str

class StepTrace(BaseModel):
    step_number: int
    state: str = Field(pattern="^(PLAN|ACT|OBSERVE|REPLAN|VERIFY|COMPLETE|TERMINATE_LIMIT_EXCEEDED)$")
    tool_call: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Dict[str, Any]] = None
    latency_ms: int
    cost_usd: float
    tokens_used: Optional[int] = None
    model_routed: Optional[str] = None
    rationale: str
    timestamp: str

class ActionApprovalRequest(BaseModel):
    action_id: str
    approved: bool
    operator_notes: Optional[str] = None

class ActionApprovalResponse(BaseModel):
    action_id: str
    status: str
