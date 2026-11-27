"""
AuditAgent Web3 Client Module
Integrates the Agent Core with Base Sepolia / Anvil smart contracts using web3.py:
- Loads canonical ABIs from shared/abis/
- Connects to local Anvil or Base Sepolia RPC
- Provides read helpers: balances, spending limits, escrow status, reviewer reputation
- Provides session-key execution helpers for AgentWallet, Escrow, and ReputationRegistry
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
from eth_account import Account
from web3 import Web3
from web3.contract import Contract

# Standard ERC-20 Transfer event signature: Transfer(address indexed from, address indexed to, uint256 value)
ERC20_TRANSFER_EVENT_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

class Web3Client:
    """
    Manages Web3 provider connections and smart contract interactions for AuditAgent.
    """

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        abi_dir: Optional[str] = None
    ):
        self.rpc_url = rpc_url or os.getenv("RPC_URL", "http://127.0.0.1:8545")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        # Locate shared/abis directory
        if abi_dir:
            self.abi_dir = Path(abi_dir)
        else:
            # Look relative to repository root
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.abi_dir = base_dir / "shared" / "abis"

        self._abi_cache: Dict[str, list] = {}

    @property
    def is_connected(self) -> bool:
        """Check if RPC endpoint is responding."""
        try:
            return self.w3.is_connected()
        except Exception:
            return False

    def load_abi(self, contract_name: str) -> list:
        """Load contract ABI JSON from shared/abis/."""
        if contract_name in self._abi_cache:
            return self._abi_cache[contract_name]

        file_name = f"{contract_name}.json" if not contract_name.endswith(".json") else contract_name
        abi_path = self.abi_dir / file_name

        if not abi_path.exists():
            raise FileNotFoundError(f"ABI file not found: {abi_path}")

        with open(abi_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Support both forge artifact (with "abi" key) and raw ABI array
            abi = data.get("abi", data) if isinstance(data, dict) else data

        self._abi_cache[contract_name] = abi
        return abi

    def get_contract(self, contract_name: str, address: str) -> Contract:
        """Instantiate a web3 Contract object with loaded ABI."""
        checksum_address = Web3.to_checksum_address(address)
        abi = self.load_abi(contract_name)
        return self.w3.eth.contract(address=checksum_address, abi=abi)

    # -------------------------------------------------------------------------
    # 1. On-Chain State Queries (Wallet, Escrow, Reputation)
    # -------------------------------------------------------------------------

    def get_wallet_status(self, wallet_address: str, usdc_address: str) -> Dict[str, Any]:
        """
        Query live on-chain status of the AgentWallet smart account:
        - USDC balance
        - Daily amount spent in current window
        - Per-tx spending cap
        - Daily spending cap
        - Reserve balance threshold
        - Paused flag & owner address
        """
        checksum_wallet = Web3.to_checksum_address(wallet_address)
        checksum_usdc = Web3.to_checksum_address(usdc_address)

        wallet = self.get_contract("AgentWallet", checksum_wallet)
        usdc = self.get_contract("MockUSDC", checksum_usdc)

        usdc_balance = usdc.functions.balanceOf(checksum_wallet).call()
        per_tx_cap = wallet.functions.perTxCap().call()
        daily_cap = wallet.functions.dailyCap().call()
        reserve_balance = wallet.functions.reserveBalance().call()
        daily_spent = wallet.functions.getDailySpent().call()
        is_paused = wallet.functions.paused().call()
        owner = wallet.functions.owner().call()

        return {
            "wallet_address": checksum_wallet,
            "usdc_address": checksum_usdc,
            "usdc_balance": str(usdc_balance),
            "usdc_balance_formatted": usdc_balance / 1e6,
            "per_tx_cap": str(per_tx_cap),
            "daily_cap": str(daily_cap),
            "daily_spent": str(daily_spent),
            "reserve_balance": str(reserve_balance),
            "is_paused": is_paused,
            "owner": owner
        }

    def get_escrow_status(self, escrow_address: str, job_id: Union[str, bytes]) -> Dict[str, Any]:
        """Query state of an Escrow record by job_id bytes32."""
        checksum_escrow = Web3.to_checksum_address(escrow_address)
        escrow = self.get_contract("Escrow", checksum_escrow)

        job_id_bytes32 = self.to_bytes32(job_id)
        item = escrow.functions.escrows(job_id_bytes32).call()
        # item: (client, reviewer, amount, deadline, status)
        status_map = {0: "None", 1: "Active", 2: "Released", 3: "Refunded"}
        return {
            "job_id_hex": "0x" + job_id_bytes32.hex(),
            "client": item[0],
            "reviewer": item[1],
            "amount_raw": item[2],
            "amount_usdc": item[2] / 1e6,
            "deadline": item[3],
            "status_code": item[4],
            "status": status_map.get(item[4], "Unknown")
        }

    def get_reviewer_reputation(self, registry_address: str, reviewer_address: str) -> Dict[str, Any]:
        """Query cumulative reputation and review count for a reviewer agent."""
        checksum_reg = Web3.to_checksum_address(registry_address)
        checksum_rev = Web3.to_checksum_address(reviewer_address)
        registry = self.get_contract("ReputationRegistry", checksum_reg)

        average_score, total_reviews = registry.functions.getReputation(checksum_rev).call()
        return {
            "reviewer": checksum_rev,
            "average_score": average_score,
            "total_reviews": total_reviews
        }

    # -------------------------------------------------------------------------
    # 2. Payment Transaction Verification (x402 Protocol)
    # -------------------------------------------------------------------------

    def verify_usdc_payment(
        self,
        tx_hash: str,
        expected_recipient: str,
        expected_amount_raw: int,
        expected_job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify that a customer transaction:
        1. Exists and succeeded on-chain (status == 1)
        2. Contains an ERC-20 Transfer log transferring at least expected_amount_raw to expected_recipient
        3. Optionally binds the expected_job_id in calldata or log
        """
        if not tx_hash.startswith("0x"):
            tx_hash = "0x" + tx_hash

        receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        if receipt is None:
            raise ValueError(f"Transaction {tx_hash} not found on chain.")

        if receipt.get("status") != 1:
            raise ValueError(f"Transaction {tx_hash} reverted or failed on chain.")

        checksum_recipient = Web3.to_checksum_address(expected_recipient).lower()

        # Inspect logs for ERC20 Transfer
        found_transfer = False
        sender_address = None
        transfer_amount = 0
        token_address = None

        for log in receipt.get("logs", []):
            topics = log.get("topics", [])
            if not topics:
                continue

            # Check if topic0 is Transfer(address,address,uint256)
            topic0 = topics[0].hex() if hasattr(topics[0], "hex") else str(topics[0])
            if not topic0.startswith("0x"):
                topic0 = "0x" + topic0

            if topic0.lower() == ERC20_TRANSFER_EVENT_TOPIC.lower():
                # topics[1] = from, topics[2] = to
                if len(topics) >= 3:
                    to_topic = topics[2].hex() if hasattr(topics[2], "hex") else str(topics[2])
                    to_addr = "0x" + to_topic[-40:]

                    if to_addr.lower() == checksum_recipient:
                        # Decode value from log data
                        from_topic = topics[1].hex() if hasattr(topics[1], "hex") else str(topics[1])
                        sender_address = Web3.to_checksum_address("0x" + from_topic[-40:])
                        data = log.get("data", b"")
                        if isinstance(data, str):
                            data_bytes = bytes.fromhex(data[2:] if data.startswith("0x") else data)
                        else:
                            data_bytes = bytes(data)

                        amount = int.from_bytes(data_bytes, byteorder="big")
                        if amount >= expected_amount_raw:
                            found_transfer = True
                            transfer_amount = amount
                            token_address = log.get("address")
                            break

        if not found_transfer:
            raise ValueError(
                f"No matching ERC20 transfer of at least {expected_amount_raw} raw USDC to {expected_recipient} found in tx logs."
            )

        # Inspect calldata for expected job ID if requested
        job_id_verified = True
        tx = self.w3.eth.get_transaction(tx_hash)
        input_data = tx.get("input", "")
        if hasattr(input_data, "hex"):
            input_data = input_data.hex()

        if expected_job_id:
            # Check if job_id utf-8 hex or plain string is inside calldata
            job_id_hex = expected_job_id.encode("utf-8").hex()
            if job_id_hex not in input_data and expected_job_id not in input_data:
                # If not strictly found in calldata, check if expected_job_id bytes32 is in input
                b32_hex = self.to_bytes32(expected_job_id).hex()
                if b32_hex not in input_data:
                    # Permissive fallback: if calldata is empty standard transfer, accept if recipient matches
                    job_id_verified = False

        return {
            "verified": True,
            "tx_hash": tx_hash,
            "sender": sender_address,
            "recipient": expected_recipient,
            "amount_raw": transfer_amount,
            "amount_usdc": transfer_amount / 1e6,
            "token_address": token_address,
            "block_number": receipt.get("blockNumber"),
            "job_id_matched": job_id_verified
        }

    # -------------------------------------------------------------------------
    # 3. Session Key Execution Helpers (Calling through AgentWallet.execute)
    # -------------------------------------------------------------------------

    def execute_via_session_key(
        self,
        wallet_address: str,
        session_private_key: str,
        dest_address: str,
        value: int,
        calldata: bytes,
        gas_limit: int = 500000
    ) -> Dict[str, Any]:
        """
        Sign and submit a call to AgentWallet.execute(dest, value, func)
        using the authorized session key.
        """
        checksum_wallet = Web3.to_checksum_address(wallet_address)
        checksum_dest = Web3.to_checksum_address(dest_address)
        session_account = Account.from_key(session_private_key)

        wallet = self.get_contract("AgentWallet", checksum_wallet)

        nonce = self.w3.eth.get_transaction_count(session_account.address)
        tx_data = wallet.functions.execute(
            checksum_dest,
            value,
            calldata
        ).build_transaction({
            "from": session_account.address,
            "nonce": nonce,
            "gas": gas_limit,
            "gasPrice": self.w3.eth.gas_price
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx_data, private_key=session_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.get("status") != 1:
            raise RuntimeError(f"AgentWallet.execute transaction reverted. Tx: 0x{tx_hash.hex()}")

        return {
            "tx_hash": "0x" + tx_hash.hex(),
            "block_number": receipt.get("blockNumber"),
            "gas_used": receipt.get("gasUsed")
        }

    def create_reviewer_escrow(
        self,
        wallet_address: str,
        escrow_address: str,
        usdc_address: str,
        session_private_key: str,
        job_id: Union[str, bytes],
        reviewer_address: str,
        amount_raw: int,
        deadline_timestamp: int
    ) -> Dict[str, Any]:
        """
        Multi-step on-chain action executing through AgentWallet session key:
        1. Approves Escrow contract to pull `amount_raw` USDC
        2. Calls Escrow.createEscrow(jobId, reviewer, amount, deadline)
        """
        checksum_escrow = Web3.to_checksum_address(escrow_address)
        checksum_usdc = Web3.to_checksum_address(usdc_address)
        checksum_reviewer = Web3.to_checksum_address(reviewer_address)
        job_id_bytes32 = self.to_bytes32(job_id)

        usdc = self.get_contract("MockUSDC", checksum_usdc)
        escrow = self.get_contract("Escrow", checksum_escrow)

        # 1. Approve USDC to Escrow contract from AgentWallet
        approve_calldata = usdc.encode_abi("approve", [checksum_escrow, amount_raw])
        approve_res = self.execute_via_session_key(
            wallet_address=wallet_address,
            session_private_key=session_private_key,
            dest_address=checksum_usdc,
            value=0,
            calldata=approve_calldata
        )

        # 2. Call Escrow.createEscrow
        create_calldata = escrow.encode_abi(
            "createEscrow",
            [job_id_bytes32, checksum_reviewer, amount_raw, deadline_timestamp]
        )
        create_res = self.execute_via_session_key(
            wallet_address=wallet_address,
            session_private_key=session_private_key,
            dest_address=checksum_escrow,
            value=0,
            calldata=create_calldata
        )

        return {
            "job_id_hex": "0x" + job_id_bytes32.hex(),
            "approve_tx": approve_res["tx_hash"],
            "create_escrow_tx": create_res["tx_hash"],
            "reviewer": checksum_reviewer,
            "amount_raw": amount_raw
        }

    def release_reviewer_escrow(
        self,
        wallet_address: str,
        escrow_address: str,
        session_private_key: str,
        job_id: Union[str, bytes]
    ) -> Dict[str, Any]:
        """Release escrow funds to the reviewer via AgentWallet session key."""
        checksum_escrow = Web3.to_checksum_address(escrow_address)
        job_id_bytes32 = self.to_bytes32(job_id)
        escrow = self.get_contract("Escrow", checksum_escrow)

        release_calldata = escrow.encode_abi("releaseEscrow", [job_id_bytes32])
        res = self.execute_via_session_key(
            wallet_address=wallet_address,
            session_private_key=session_private_key,
            dest_address=checksum_escrow,
            value=0,
            calldata=release_calldata
        )
        return {
            "job_id_hex": "0x" + job_id_bytes32.hex(),
            "release_tx": res["tx_hash"]
        }

    def refund_reviewer_escrow(
        self,
        wallet_address: str,
        escrow_address: str,
        session_private_key: str,
        job_id: Union[str, bytes]
    ) -> Dict[str, Any]:
        """Reclaim escrow funds back to AgentWallet after deadline passed."""
        checksum_escrow = Web3.to_checksum_address(escrow_address)
        job_id_bytes32 = self.to_bytes32(job_id)
        escrow = self.get_contract("Escrow", checksum_escrow)

        refund_calldata = escrow.encode_abi("refundEscrow", [job_id_bytes32])
        res = self.execute_via_session_key(
            wallet_address=wallet_address,
            session_private_key=session_private_key,
            dest_address=checksum_escrow,
            value=0,
            calldata=refund_calldata
        )
        return {
            "job_id_hex": "0x" + job_id_bytes32.hex(),
            "refund_tx": res["tx_hash"]
        }

    def record_reviewer_reputation(
        self,
        registry_address: str,
        recorder_private_key: str,
        reviewer_address: str,
        job_id: Union[str, bytes],
        score: int,
        metadata_uri: str = ""
    ) -> Dict[str, Any]:
        """Direct call from an authorized recorder account to ReputationRegistry.recordReview."""
        checksum_reg = Web3.to_checksum_address(registry_address)
        checksum_rev = Web3.to_checksum_address(reviewer_address)
        job_id_bytes32 = self.to_bytes32(job_id)
        recorder_account = Account.from_key(recorder_private_key)

        registry = self.get_contract("ReputationRegistry", checksum_reg)

        nonce = self.w3.eth.get_transaction_count(recorder_account.address)
        tx_data = registry.functions.recordReview(
            checksum_rev,
            job_id_bytes32,
            score,
            metadata_uri
        ).build_transaction({
            "from": recorder_account.address,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": self.w3.eth.gas_price
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx_data, private_key=recorder_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.get("status") != 1:
            raise RuntimeError(f"recordReview transaction reverted. Tx: 0x{tx_hash.hex()}")

        return {
            "tx_hash": "0x" + tx_hash.hex(),
            "reviewer": checksum_rev,
            "score": score
        }

    @staticmethod
    def to_bytes32(val: Union[str, bytes]) -> bytes:
        """Convert a string or byte sequence safely into bytes32 format."""
        if isinstance(val, bytes):
            if len(val) == 32:
                return val
            if len(val) < 32:
                return val.ljust(32, b"\0")
            return val[:32]

        if isinstance(val, str):
            if val.startswith("0x") and len(val) == 66:
                return bytes.fromhex(val[2:])
            # Keccak256 hash text to produce deterministic bytes32
            return Web3.keccak(text=val)

        raise TypeError(f"Cannot convert type {type(val)} to bytes32")
