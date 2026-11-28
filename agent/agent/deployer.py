"""
AuditAgent Contract Deployer Utility
Automates local Anvil or testnet contract deployment and configuration:
- Deploys MockUSDC, AgentWallet, Escrow, and ReputationRegistry
- Configures vendor allowlists on AgentWallet (USDC and Escrow)
- Authorizes session keys with expiry windows
- Authorizes reputation recorders
- Mints testnet/local MockUSDC to wallet and customer accounts
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from eth_account import Account
from web3 import Web3
from web3.contract import Contract

class ContractDeployer:
    """
    Deploys and configures the AuditAgent smart contracts on local Anvil or Base Sepolia.
    """

    def __init__(
        self,
        w3: Web3,
        deployer_private_key: str,
        artifacts_dir: Optional[str] = None
    ):
        self.w3 = w3
        self.deployer_key = deployer_private_key
        self.account = Account.from_key(deployer_private_key)
        self.address = self.account.address

        if artifacts_dir:
            self.artifacts_dir = Path(artifacts_dir)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.artifacts_dir = base_dir / "contracts" / "out"

    def _load_artifact(self, contract_name: str) -> Dict[str, Any]:
        """Load artifact JSON from contracts/out/<ContractName>.sol/<ContractName>.json."""
        artifact_path = self.artifacts_dir / f"{contract_name}.sol" / f"{contract_name}.json"
        if not artifact_path.exists():
            raise FileNotFoundError(f"Contract artifact not found at: {artifact_path}")

        with open(artifact_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def deploy_contract(self, contract_name: str, *constructor_args) -> Tuple[Contract, str]:
        """Deploy a contract and wait for receipt."""
        artifact = self._load_artifact(contract_name)
        abi = artifact["abi"]
        bytecode = artifact["bytecode"]["object"]
        if not bytecode.startswith("0x"):
            bytecode = "0x" + bytecode

        contract_factory = self.w3.eth.contract(abi=abi, bytecode=bytecode)

        nonce = self.w3.eth.get_transaction_count(self.address)
        tx_data = contract_factory.constructor(*constructor_args).build_transaction({
            "from": self.address,
            "nonce": nonce,
            "gas": 4000000,
            "gasPrice": self.w3.eth.gas_price
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx_data, private_key=self.deployer_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.get("status") != 1:
            raise RuntimeError(f"Deployment of {contract_name} failed. Tx: 0x{tx_hash.hex()}")

        contract_address = receipt.get("contractAddress")
        deployed_instance = self.w3.eth.contract(address=contract_address, abi=abi)
        return deployed_instance, contract_address

    def send_tx(self, contract_func, gas_limit: int = 500000) -> Dict[str, Any]:
        """Sign and submit a transaction from deployer account."""
        nonce = self.w3.eth.get_transaction_count(self.address)
        tx_data = contract_func.build_transaction({
            "from": self.address,
            "nonce": nonce,
            "gas": gas_limit,
            "gasPrice": self.w3.eth.gas_price
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx_data, private_key=self.deployer_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.get("status") != 1:
            raise RuntimeError(f"Transaction failed. Tx: 0x{tx_hash.hex()}")
        return receipt

    def deploy_all(
        self,
        owner_address: Optional[str] = None,
        session_key_address: Optional[str] = None,
        customer_address: Optional[str] = None,
        mint_wallet_usdc: int = 100,
        mint_customer_usdc: int = 200,
        per_tx_cap: int = 5 * 10**6,    # 5 USDC
        daily_cap: int = 25 * 10**6,    # 25 USDC
        reserve_balance: int = 50 * 10**6  # 50 USDC
    ) -> Dict[str, Any]:
        """
        Deploy and initialize the entire AuditAgent contract suite:
        1. Deploy MockUSDC
        2. Deploy AgentWallet
        3. Deploy Escrow
        4. Deploy ReputationRegistry
        5. Set Vendor Allowlists (USDC + Escrow)
        6. Set Session Key (valid for 7 days)
        7. Set Reputation Recorder
        8. Mint initial USDC balances
        """
        owner = owner_address or self.address

        # 1. Deploy MockUSDC
        usdc_contract, usdc_addr = self.deploy_contract("MockUSDC")

        # 2. Deploy AgentWallet
        wallet_contract, wallet_addr = self.deploy_contract(
            "AgentWallet",
            usdc_addr,
            owner,
            per_tx_cap,
            daily_cap,
            reserve_balance
        )

        # 3. Deploy Escrow
        escrow_contract, escrow_addr = self.deploy_contract("Escrow", usdc_addr)

        # 4. Deploy ReputationRegistry
        reputation_contract, reputation_addr = self.deploy_contract("ReputationRegistry", owner)

        # 5. Allowlist vendors in AgentWallet (must be done by owner)
        self.send_tx(wallet_contract.functions.setVendorAllowlist(usdc_addr, True))
        self.send_tx(wallet_contract.functions.setVendorAllowlist(escrow_addr, True))

        # 6. Configure Session Key if provided
        now = int(time.time())
        if session_key_address:
            valid_after = now - 60  # active now
            valid_until = now + (7 * 86400)  # 7 days
            checksum_session = Web3.to_checksum_address(session_key_address)
            self.send_tx(wallet_contract.functions.setSessionKey(
                checksum_session,
                valid_until,
                valid_after
            ))
            # Authorize session key as recorder on ReputationRegistry
            self.send_tx(reputation_contract.functions.setRecorder(checksum_session, True))

        # 7. Mint initial MockUSDC balances
        if mint_wallet_usdc > 0:
            self.send_tx(usdc_contract.functions.mint(wallet_addr, mint_wallet_usdc * 10**6))

        if customer_address and mint_customer_usdc > 0:
            checksum_cust = Web3.to_checksum_address(customer_address)
            self.send_tx(usdc_contract.functions.mint(checksum_cust, mint_customer_usdc * 10**6))

        return {
            "usdc": usdc_contract,
            "usdc_address": usdc_addr,
            "wallet": wallet_contract,
            "wallet_address": wallet_addr,
            "escrow": escrow_contract,
            "escrow_address": escrow_addr,
            "reputation": reputation_contract,
            "reputation_address": reputation_addr,
            "owner_address": owner,
            "session_key_address": session_key_address
        }
