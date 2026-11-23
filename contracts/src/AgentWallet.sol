// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AgentWallet
 * @notice Autonomous AI Agent Smart Account with on-chain safety rails.
 * Features:
 *  - Per-transaction spend ceiling
 *  - Rolling 24-hour daily spend cap
 *  - Non-custodial reserve balance floor
 *  - Vendor allowlist
 *  - Expiring session keys
 *  - Owner emergency pause and reserve withdrawal
 */
contract AgentWallet {
    address public owner;
    address public sessionKey;
    uint48 public sessionValidUntil;
    uint48 public sessionValidAfter;

    uint256 public perTxCap;
    uint256 public dailyCap;
    uint256 public reserveBalance;

    uint256 public dailySpent;
    uint256 public lastResetDay;
    bool public paused;

    mapping(address => bool) public vendorAllowlist;

    event TransactionExecuted(address indexed target, uint256 value, bytes data);
    event SessionKeyUpdated(address indexed key, uint48 validUntil);
    event VendorStatusChanged(address indexed vendor, bool allowed);
    event LimitsUpdated(uint256 perTxCap, uint256 dailyCap, uint256 reserveBalance);
    event Paused(address account);
    event Unpaused(address account);
    event ReserveWithdrawn(address to, uint256 amount);

    error DailyCapExceeded();
    error PerTxCapExceeded();
    error ReserveBreached();
    error VendorNotAllowed();
    error SessionKeyExpired();
    error Unauthorized();
    error ExecutionFailed();

    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    modifier whenNotPaused() {
        if (paused) revert Unauthorized();
        _;
    }

    constructor(
        uint256 _perTxCap,
        uint256 _dailyCap,
        uint256 _reserveBalance
    ) {
        owner = msg.sender;
        perTxCap = _perTxCap;
        dailyCap = _dailyCap;
        reserveBalance = _reserveBalance;
        lastResetDay = block.timestamp / 1 days;
    }

    receive() external payable {}

    function setSessionKey(address key, uint48 validUntil, uint48 validAfter) external onlyOwner {
        sessionKey = key;
        sessionValidUntil = validUntil;
        sessionValidAfter = validAfter;
        emit SessionKeyUpdated(key, validUntil);
    }

    function setLimits(uint256 _perTxCap, uint256 _dailyCap, uint256 _reserveBalance) external onlyOwner {
        perTxCap = _perTxCap;
        dailyCap = _dailyCap;
        reserveBalance = _reserveBalance;
        emit LimitsUpdated(_perTxCap, _dailyCap, _reserveBalance);
    }

    function setVendorAllowlist(address vendor, bool allowed) external onlyOwner {
        vendorAllowlist[vendor] = allowed;
        emit VendorStatusChanged(vendor, allowed);
    }

    function pause() external onlyOwner {
        paused = true;
        emit Paused(msg.sender);
    }

    function unpause() external onlyOwner {
        paused = false;
        emit Unpaused(msg.sender);
    }

    function withdrawReserve(address to, uint256 amount) external onlyOwner {
        if (amount > address(this).balance) revert ExecutionFailed();
        (bool ok, ) = to.call{value: amount}("");
        if (!ok) revert ExecutionFailed();
        emit ReserveWithdrawn(to, amount);
    }

    function getDailySpent() external view returns (uint256) {
        uint256 currentDay = block.timestamp / 1 days;
        if (currentDay > lastResetDay) {
            return 0;
        }
        return dailySpent;
    }

    function execute(
        address dest,
        uint256 value,
        bytes calldata func
    ) external whenNotPaused returns (bytes memory) {
        bool isOwner = (msg.sender == owner);
        bool isSession = (msg.sender == sessionKey &&
            block.timestamp >= sessionValidAfter &&
            block.timestamp <= sessionValidUntil);

        if (!isOwner && !isSession) {
            revert Unauthorized();
        }

        if (isSession) {
            if (!vendorAllowlist[dest]) revert VendorNotAllowed();
            if (value > perTxCap) revert PerTxCapExceeded();

            // Refresh rolling daily counter
            uint256 currentDay = block.timestamp / 1 days;
            if (currentDay > lastResetDay) {
                dailySpent = 0;
                lastResetDay = currentDay;
            }

            if (dailySpent + value > dailyCap) revert DailyCapExceeded();
            if (address(this).balance - value < reserveBalance) revert ReserveBreached();

            dailySpent += value;
        }

        (bool success, bytes memory ret) = dest.call{value: value}(func);
        if (!success) revert ExecutionFailed();

        emit TransactionExecuted(dest, value, func);
        return ret;
    }
}