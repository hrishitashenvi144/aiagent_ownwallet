# AuditAgent Adversarial Security Attack Suite (Person 4)

This suite contains automated red-team adversarial tests probing the resilience of AuditAgent across 5 attack vectors:
1. **Prompt Injection**: Submitting adversarial comments/strings to hijack LLM triage or extract system keys.
2. **Sandbox Escape**: Compiler resource bombs, unauthorized syscall attempts, and network egress probes.
3. **Fake Payment Proofs**: Forged transaction hashes, mismatched token contracts, underpaid amounts, and hash replay attacks.
4. **Malicious Sub-Agent**: Forged secondary reviews, expired escrow timeouts, and non-consensus collusion.
5. **Wallet Drain**: Exploits attempting to breach daily spend caps, per-tx ceilings, or the untouchable reserve balance.

## Running Tests
```bash
pytest tests/ -v
```
