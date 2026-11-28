"""
AuditAgent Payment Verifier Module
Enforces x402 on-chain payment verification and defends against replay attacks.
"""

from typing import Dict, Any, Optional, Set
from agent.web3_client import Web3Client

class PaymentVerificationError(Exception):
    """Base error for payment verification failures."""
    pass

class ReplayAttackError(PaymentVerificationError):
    """Raised when an on-chain transaction hash is re-submitted for another job."""
    pass

class InvalidPaymentProofError(PaymentVerificationError):
    """Raised when the format or content of the payment proof header is invalid."""
    pass

class PaymentUnderpaidError(PaymentVerificationError):
    """Raised when the transaction value is less than the required quote."""
    pass

class PaymentVerifier:
    """
    Validates on-chain transactions and guards against replay attacks.
    """

    def __init__(self, web3_client: Optional[Web3Client] = None):
        self.web3_client = web3_client or Web3Client()
        # In-memory registry for claimed transaction hashes (backed by SQLite in full DB)
        self._processed_tx_hashes: Set[str] = set()

    def is_processed(self, tx_hash: str) -> bool:
        """Check if a transaction hash has already been used."""
        return tx_hash.lower() in self._processed_tx_hashes

    def mark_processed(self, tx_hash: str) -> None:
        """Register a transaction hash as used."""
        self._processed_tx_hashes.add(tx_hash.lower())

    def reset_processed(self) -> None:
        """Clear processed hashes (for testing)."""
        self._processed_tx_hashes.clear()

    def verify(
        self,
        tx_hash: str,
        expected_recipient: str,
        expected_amount_raw: int,
        expected_job_id: Optional[str] = None,
        allow_mock: bool = False
    ) -> Dict[str, Any]:
        """
        Verify payment proof:
        1. Reject if tx_hash has already been claimed (Replay Defense).
        2. Validate hex structure (0x + 64 hex characters).
        3. If Web3 RPC is online, verify on-chain receipt and transfer logs.
        4. If Web3 RPC is offline, permit mock hash only if allow_mock=True.
        """
        if not tx_hash:
            raise InvalidPaymentProofError("Payment proof is missing or empty.")

        clean_hash = tx_hash.strip().lower()
        if not clean_hash.startswith("0x"):
            clean_hash = "0x" + clean_hash

        # Strict hex pattern check
        if len(clean_hash) != 66:
            raise InvalidPaymentProofError(
                f"Invalid transaction hash length: {len(clean_hash)}. Must be 66 characters."
            )
        try:
            int(clean_hash[2:], 16)
        except ValueError:
            raise InvalidPaymentProofError("Transaction hash contains non-hexadecimal characters.")

        # Replay Attack Protection: reject if already claimed
        if self.is_processed(clean_hash):
            raise ReplayAttackError(
                f"Replay attack detected: transaction {clean_hash} has already been claimed."
            )

        # On-Chain Verification
        if self.web3_client and self.web3_client.is_connected:
            try:
                verification_result = self.web3_client.verify_usdc_payment(
                    tx_hash=clean_hash,
                    expected_recipient=expected_recipient,
                    expected_amount_raw=expected_amount_raw,
                    expected_job_id=expected_job_id
                )
                self.mark_processed(clean_hash)
                return verification_result
            except Exception as exc:
                raise PaymentVerificationError(f"On-chain verification failed: {str(exc)}") from exc

        # Fallback for offline mock testing
        if allow_mock:
            self.mark_processed(clean_hash)
            return {
                "verified": True,
                "mock": True,
                "tx_hash": clean_hash,
                "recipient": expected_recipient,
                "amount_raw": expected_amount_raw
            }

        raise PaymentVerificationError("Web3 RPC endpoint unreachable and mock payments disabled.")
