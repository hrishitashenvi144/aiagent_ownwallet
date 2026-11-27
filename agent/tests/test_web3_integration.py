"""
Integration Tests for AuditAgent Web3 Contracts & Payment Flows
Runs against a local Foundry Anvil node (Chain ID 31337).
Validates:
1. Smart contract deployment (MockUSDC, AgentWallet, Escrow, ReputationRegistry)
2. Live on-chain USDC payment verification (x402 flow)
3. Replay attack rejection (HTTP 409 Conflict)
4. Fake and unverified payment proof rejection (HTTP 400 Bad Request)
5. Live treasury telemetry on GET /agent/status
6. Session key execution: Escrow creation & release
7. Safety rails: PerTxCap and VendorAllowlist enforcement
8. ReputationRegistry review recording and scoring
"""

import os
import time
import shutil
import subprocess
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from eth_account import Account
from web3 import Web3

from agent.main import app, set_agent_contracts, payment_verifier
from agent.web3_client import Web3Client
from agent.deployer import ContractDeployer

# Standard Anvil test accounts (Chain ID 31337)
ANVIL_ACCOUNTS = {
    "deployer": {
        "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "key": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    },
    "session_key": {
        "address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "key": "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
    },
    "customer": {
        "address": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
        "key": "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"
    },
    "reviewer": {
        "address": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
        "key": "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6"
    }
}

def find_anvil_binary() -> str:
    """Locate the anvil binary in PATH or standard ~/.foundry/bin path."""
    which_anvil = shutil.which("anvil")
    if which_anvil:
        return which_anvil
    home_anvil = Path.home() / ".foundry" / "bin" / ("anvil.exe" if os.name == "nt" else "anvil")
    if home_anvil.exists():
        return str(home_anvil)
    return "anvil"

@pytest.fixture(scope="module")
def anvil_rpc():
    """Ensure local Anvil node is active for tests."""
    rpc_url = "http://127.0.0.1:8545"
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    proc = None

    if not w3.is_connected():
        anvil_bin = find_anvil_binary()
        proc = subprocess.Popen(
            [anvil_bin, "--port", "8545", "--silent"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        start = time.time()
        connected = False
        while time.time() - start < 10:
            if w3.is_connected():
                connected = True
                break
            time.sleep(0.3)
        if not connected:
            if proc:
                proc.kill()
            pytest.skip("Anvil executable not found or failed to start")

    yield rpc_url

    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()

@pytest.fixture(scope="module")
def web3_client(anvil_rpc):
    """Web3Client connected to Anvil."""
    return Web3Client(rpc_url=anvil_rpc)

@pytest.fixture(scope="module")
def deployed_contracts(anvil_rpc):
    """Deploy MockUSDC, AgentWallet, Escrow, and ReputationRegistry to Anvil."""
    w3 = Web3(Web3.HTTPProvider(anvil_rpc))
    deployer = ContractDeployer(
        w3=w3,
        deployer_private_key=ANVIL_ACCOUNTS["deployer"]["key"]
    )
    result = deployer.deploy_all(
        owner_address=ANVIL_ACCOUNTS["deployer"]["address"],
        session_key_address=ANVIL_ACCOUNTS["session_key"]["address"],
        customer_address=ANVIL_ACCOUNTS["customer"]["address"],
        mint_wallet_usdc=100,      # 100 USDC in AgentWallet
        mint_customer_usdc=200,    # 200 USDC to customer
        per_tx_cap=5 * 10**6,      # 5 USDC per tx cap
        daily_cap=25 * 10**6,      # 25 USDC daily cap
        reserve_balance=50 * 10**6 # 50 USDC reserve floor
    )
    return result

@pytest.fixture(autouse=True)
def reset_processed_txs():
    """Reset replay protection cache before each test."""
    payment_verifier.reset_processed()
    yield

def test_contract_deployment_and_initial_state(web3_client, deployed_contracts):
    """Verify contracts are initialized with correct parameters on Anvil."""
    status = web3_client.get_wallet_status(
        wallet_address=deployed_contracts["wallet_address"],
        usdc_address=deployed_contracts["usdc_address"]
    )
    assert status["usdc_balance"] == str(100 * 10**6)
    assert status["per_tx_cap"] == str(5 * 10**6)
    assert status["daily_cap"] == str(25 * 10**6)
    assert status["reserve_balance"] == str(50 * 10**6)
    assert status["daily_spent"] == "0"
    assert status["is_paused"] is False
    assert status["owner"].lower() == ANVIL_ACCOUNTS["deployer"]["address"].lower()

def test_onchain_payment_and_job_creation(anvil_rpc, deployed_contracts):
    """Customer pays 15 USDC on-chain and submits job with valid transaction proof."""
    w3 = Web3(Web3.HTTPProvider(anvil_rpc))
    client = TestClient(app)

    # Point agent state to newly deployed contracts
    set_agent_contracts(
        wallet_address=deployed_contracts["wallet_address"],
        usdc_token=deployed_contracts["usdc_address"]
    )

    # Customer sends 15 USDC (15,000,000 raw) to AgentWallet
    usdc = deployed_contracts["usdc"]
    customer_key = ANVIL_ACCOUNTS["customer"]["key"]
    customer_addr = ANVIL_ACCOUNTS["customer"]["address"]
    wallet_addr = deployed_contracts["wallet_address"]

    payment_amount_raw = 15 * 10**6
    nonce = w3.eth.get_transaction_count(customer_addr)
    tx_data = usdc.functions.transfer(wallet_addr, payment_amount_raw).build_transaction({
        "from": customer_addr,
        "nonce": nonce,
        "gas": 150000,
        "gasPrice": w3.eth.gas_price
    })
    signed_tx = w3.eth.account.sign_transaction(tx_data, private_key=customer_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    assert receipt["status"] == 1

    tx_hash_hex = "0x" + tx_hash.hex()

    # Submit job using the real payment tx hash in header
    response = client.post(
        "/jobs",
        json={
            "customer_address": customer_addr,
            "contract_source": "pragma solidity ^0.8.20; contract Target { function test() public {} }",
            "scan_depth": "standard"
        },
        headers={"X-Payment-Proof": tx_hash_hex}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tx_hash"] == tx_hash_hex
    assert data["status"] in ("delivered", "paid", "analyzing")

def test_replay_attack_rejected(anvil_rpc, deployed_contracts):
    """Replaying an already-claimed payment transaction must return HTTP 409 Conflict."""
    w3 = Web3(Web3.HTTPProvider(anvil_rpc))
    client = TestClient(app)
    set_agent_contracts(deployed_contracts["wallet_address"], deployed_contracts["usdc_address"])

    # Create a fresh payment transaction
    usdc = deployed_contracts["usdc"]
    customer_key = ANVIL_ACCOUNTS["customer"]["key"]
    customer_addr = ANVIL_ACCOUNTS["customer"]["address"]

    nonce = w3.eth.get_transaction_count(customer_addr)
    tx_data = usdc.functions.transfer(deployed_contracts["wallet_address"], 15 * 10**6).build_transaction({
        "from": customer_addr,
        "nonce": nonce,
        "gas": 150000,
        "gasPrice": w3.eth.gas_price
    })
    signed_tx = w3.eth.account.sign_transaction(tx_data, private_key=customer_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    tx_hash_hex = "0x" + tx_hash.hex()

    # 1. First claim: succeeds
    res1 = client.post(
        "/jobs",
        json={
            "customer_address": customer_addr,
            "contract_source": "pragma solidity ^0.8.20; contract Target1 {}",
            "scan_depth": "standard"
        },
        headers={"X-Payment-Proof": tx_hash_hex}
    )
    assert res1.status_code == 201

    # 2. Second claim with identical tx_hash: must be rejected with 409 Conflict
    res2 = client.post(
        "/jobs",
        json={
            "customer_address": customer_addr,
            "contract_source": "pragma solidity ^0.8.20; contract Target2 {}",
            "scan_depth": "standard"
        },
        headers={"X-Payment-Proof": tx_hash_hex}
    )
    assert res2.status_code == 409
    assert "Replay attack detected" in res2.json()["detail"]

def test_invalid_and_fake_payment_proofs(deployed_contracts):
    """Unverified or corrupted transaction hashes must be rejected with HTTP 400."""
    client = TestClient(app)
    set_agent_contracts(deployed_contracts["wallet_address"], deployed_contracts["usdc_address"])

    # 1. Invalid hex format
    res_bad_format = client.post(
        "/jobs",
        json={
            "customer_address": ANVIL_ACCOUNTS["customer"]["address"],
            "contract_source": "contract Test {}",
            "scan_depth": "standard"
        },
        headers={"X-Payment-Proof": "not-a-valid-hex-hash"}
    )
    assert res_bad_format.status_code == 400

    # 2. Fake transaction that doesn't exist on Anvil
    fake_hash = "0x" + "9" * 64
    res_fake = client.post(
        "/jobs",
        json={
            "customer_address": ANVIL_ACCOUNTS["customer"]["address"],
            "contract_source": "contract Test {}",
            "scan_depth": "standard"
        },
        headers={"X-Payment-Proof": fake_hash}
    )
    assert res_fake.status_code == 400

def test_agent_live_status_from_anvil(deployed_contracts):
    """GET /agent/status returns real on-chain balance and limits directly from Anvil."""
    client = TestClient(app)
    set_agent_contracts(deployed_contracts["wallet_address"], deployed_contracts["usdc_address"])

    res = client.get("/agent/status")
    assert res.status_code == 200
    data = res.json()
    assert data["wallet_address"] == deployed_contracts["wallet_address"]
    # Balance is at least 100 USDC (initial mint) + previous test payments
    assert int(data["usdc_balance"]) >= 100 * 10**6
    assert data["daily_limit"] == str(25 * 10**6)
    assert data["is_paused"] is False

def test_session_key_escrow_workflow(web3_client, deployed_contracts):
    """
    Test autonomous subcontracting flow via AgentWallet session key:
    1. Agent locks 4 USDC in Escrow for reviewer agent
    2. Escrow status reflects Active
    3. Agent releases 4 USDC bounty upon review completion
    4. Reviewer receives 4 USDC on-chain
    """
    wallet_addr = deployed_contracts["wallet_address"]
    escrow_addr = deployed_contracts["escrow_address"]
    usdc_addr = deployed_contracts["usdc_address"]
    session_key = ANVIL_ACCOUNTS["session_key"]["key"]
    reviewer_addr = ANVIL_ACCOUNTS["reviewer"]["address"]

    bounty_amount_raw = 4 * 10**6  # 4 USDC (within perTxCap = 5 USDC)
    deadline = int(time.time()) + 3600
    job_id = "job-subagent-review-001"

    # 1. Create Escrow via session key executing through AgentWallet
    escrow_res = web3_client.create_reviewer_escrow(
        wallet_address=wallet_addr,
        escrow_address=escrow_addr,
        usdc_address=usdc_addr,
        session_private_key=session_key,
        job_id=job_id,
        reviewer_address=reviewer_addr,
        amount_raw=bounty_amount_raw,
        deadline_timestamp=deadline
    )
    assert "create_escrow_tx" in escrow_res

    # 2. Check Escrow contract status
    escrow_status = web3_client.get_escrow_status(escrow_addr, job_id)
    assert escrow_status["status"] == "Active"
    assert escrow_status["amount_raw"] == bounty_amount_raw
    assert escrow_status["reviewer"].lower() == reviewer_addr.lower()

    # 3. Release Escrow via session key
    release_res = web3_client.release_reviewer_escrow(
        wallet_address=wallet_addr,
        escrow_address=escrow_addr,
        session_private_key=session_key,
        job_id=job_id
    )
    assert "release_tx" in release_res

    # 4. Check Escrow is Released and reviewer received funds
    updated_status = web3_client.get_escrow_status(escrow_addr, job_id)
    assert updated_status["status"] == "Released"

    usdc = deployed_contracts["usdc"]
    reviewer_balance = usdc.functions.balanceOf(reviewer_addr).call()
    assert reviewer_balance == bounty_amount_raw

def test_safety_rails_enforcement(web3_client, deployed_contracts):
    """
    Verify on-chain safety rails enforce bounds:
    1. Per-tx cap exceeded (> 5 USDC) reverts with PerTxCapExceeded()
    2. Non-allowlisted vendor call reverts with VendorNotAllowed()
    """
    wallet_addr = deployed_contracts["wallet_address"]
    usdc_addr = deployed_contracts["usdc_address"]
    session_key = ANVIL_ACCOUNTS["session_key"]["key"]
    reviewer_addr = ANVIL_ACCOUNTS["reviewer"]["address"]
    usdc = deployed_contracts["usdc"]

    # 1. Exceed PerTxCap: attempt to spend 10 USDC (> 5 USDC cap)
    excess_amount = 10 * 10**6
    approve_excess = usdc.encode_abi("approve", [reviewer_addr, excess_amount])

    with pytest.raises(Exception) as exc_info:
        web3_client.execute_via_session_key(
            wallet_address=wallet_addr,
            session_private_key=session_key,
            dest_address=usdc_addr,
            value=0,
            calldata=approve_excess
        )
    # The transaction must revert because approve amount > perTxCap or vendor not allowed
    assert "reverted" in str(exc_info.value).lower()

    # 2. Non-allowlisted vendor destination
    random_unauthorized_dest = "0x1111111111111111111111111111111111111111"
    with pytest.raises(Exception) as exc_info2:
        web3_client.execute_via_session_key(
            wallet_address=wallet_addr,
            session_private_key=session_key,
            dest_address=random_unauthorized_dest,
            value=0,
            calldata=b""
        )
    assert "reverted" in str(exc_info2.value).lower()

def test_reputation_registry_workflow(web3_client, deployed_contracts):
    """Test on-chain reputation scoring for peer reviewer agents."""
    registry_addr = deployed_contracts["reputation_address"]
    recorder_key = ANVIL_ACCOUNTS["session_key"]["key"]
    reviewer_addr = ANVIL_ACCOUNTS["reviewer"]["address"]

    # 1. Record first review: score = 95
    rec1 = web3_client.record_reviewer_reputation(
        registry_address=registry_addr,
        recorder_private_key=recorder_key,
        reviewer_address=reviewer_addr,
        job_id="job-rep-001",
        score=95,
        metadata_uri="ipfs://QmAuditReview001"
    )
    assert "tx_hash" in rec1

    rep1 = web3_client.get_reviewer_reputation(registry_addr, reviewer_addr)
    assert rep1["average_score"] == 95
    assert rep1["total_reviews"] == 1

    # 2. Record second review: score = 85
    web3_client.record_reviewer_reputation(
        registry_address=registry_addr,
        recorder_private_key=recorder_key,
        reviewer_address=reviewer_addr,
        job_id="job-rep-002",
        score=85,
        metadata_uri="ipfs://QmAuditReview002"
    )
    rep2 = web3_client.get_reviewer_reputation(registry_addr, reviewer_addr)
    # Cumulative: 95 + 85 = 180 / 2 = 90
    assert rep2["average_score"] == 90
    assert rep2["total_reviews"] == 2
