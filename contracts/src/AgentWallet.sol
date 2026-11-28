// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title AgentWallet
 * @notice Smart account for the AuditAgent. The owner (a human) keeps full
 *         control; a temporary "session key" held by the AI agent can only
 *         spend within strict on-chain limits.
 *
 * Safety rails (all measured in USDC, 6 decimals):
 *  - perTxCap        : max USDC leaving the wallet in ONE execute() call
 *  - dailyCap        : max USDC leaving per rolling 24h window
 *  - reserveBalance  : USDC floor session keys can never spend below
 *  - vendor allowlist: session keys may only call approved contracts
 *  - session keys    : expire, and are only valid inside [validAfter, validUntil]
 *  - pause           : owner kill-switch freezing all execute() calls
 *
 * How spending is metered: instead of trusting the calldata, execute() compares
 * the wallet's USDC balance before and after the call. Whatever actually left
 * the wallet is what counts against the caps, so a vendor call cannot hide a
 * transfer from the limits.
 */
contract AgentWallet is Ownable, Pausable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    struct SessionKey {
        uint48 validUntil;
        uint48 validAfter;
    }

    /// @dev selector of ERC20.approve(address,uint256)
    bytes4 private constant APPROVE_SELECTOR = 0x095ea7b3;
    uint256 private constant WINDOW = 1 days;

    IERC20 public immutable usdc;

    uint256 public perTxCap;
    uint256 public dailyCap;
    uint256 public reserveBalance;

    /// @notice USDC spent by session keys in the current window.
    uint256 public dailySpent;
    /// @notice Timestamp at which the current 24h window started.
    uint256 public windowStart;

    mapping(address => SessionKey) public sessionKeys;
    mapping(address => bool) public vendorAllowlist;

    event TransactionExecuted(address indexed target, uint256 value, bytes data);
    event SessionKeyUpdated(address indexed key, uint48 validUntil);
    event VendorStatusChanged(address indexed vendor, bool allowed);
    event LimitsUpdated(uint256 perTxCap, uint256 dailyCap, uint256 reserveBalance);
    event ReserveWithdrawn(address indexed to, uint256 amount);

    error DailyCapExceeded();
    error PerTxCapExceeded();
    error ReserveBreached();
    error VendorNotAllowed();
    error SessionKeyExpired();
    error Unauthorized();
    error ExecutionFailed();
    error InvalidLimits();
    error InvalidSessionWindow();
    /// @dev session keys may not send ETH or move allowances to non-vendors
    error ForbiddenCall();

    constructor(IERC20 _usdc, address _owner, uint256 _perTxCap, uint256 _dailyCap, uint256 _reserveBalance)
        Ownable(_owner)
    {
        if (_perTxCap > _dailyCap) revert InvalidLimits();
        usdc = _usdc;
        perTxCap = _perTxCap;
        dailyCap = _dailyCap;
        reserveBalance = _reserveBalance;
        windowStart = block.timestamp;
        emit LimitsUpdated(_perTxCap, _dailyCap, _reserveBalance);
    }

    receive() external payable {}

    // ---------------------------------------------------------------------
    // Owner configuration
    // ---------------------------------------------------------------------

    /// @dev Use the interface's `Unauthorized()` error instead of OZ's default.
    function _checkOwner() internal view override {
        if (owner() != _msgSender()) revert Unauthorized();
    }

    /// @notice Authorise (or, with validUntil = 0, revoke) a session key.
    function setSessionKey(address key, uint48 validUntil, uint48 validAfter) external onlyOwner {
        if (validUntil != 0 && validUntil <= validAfter) revert InvalidSessionWindow();
        sessionKeys[key] = SessionKey({validUntil: validUntil, validAfter: validAfter});
        emit SessionKeyUpdated(key, validUntil);
    }

    function setLimits(uint256 _perTxCap, uint256 _dailyCap, uint256 _reserveBalance) external onlyOwner {
        if (_perTxCap > _dailyCap) revert InvalidLimits();
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
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    /// @notice Owner can always pull USDC out (including the reserve), even when paused.
    function withdrawReserve(address to, uint256 amount) external onlyOwner nonReentrant {
        usdc.safeTransfer(to, amount);
        emit ReserveWithdrawn(to, amount);
    }

    // ---------------------------------------------------------------------
    // Execution
    // ---------------------------------------------------------------------

    /**
     * @notice Call `dest` from this wallet.
     * @dev Owner: unrestricted (but blocked while paused).
     *      Session key: must be inside its time window, `dest` must be an
     *      allowlisted vendor, no ETH, and the USDC that leaves the wallet is
     *      checked against perTxCap / dailyCap / reserveBalance.
     */
    function execute(address dest, uint256 value, bytes calldata func)
        external
        whenNotPaused
        nonReentrant
        returns (bytes memory)
    {
        bool isOwner = msg.sender == owner();

        if (!isOwner) {
            SessionKey memory sk = sessionKeys[msg.sender];
            if (sk.validUntil == 0) revert Unauthorized();
            if (block.timestamp < sk.validAfter || block.timestamp > sk.validUntil) revert SessionKeyExpired();
            if (!vendorAllowlist[dest]) revert VendorNotAllowed();
            if (value != 0) revert ForbiddenCall();
            _checkApprove(func);
        }

        uint256 balanceBefore = usdc.balanceOf(address(this));

        // The balance check below must run AFTER the call; re-entry is blocked by nonReentrant.
        // slither-disable-next-line reentrancy-benign,reentrancy-events
        (bool success, bytes memory ret) = dest.call{value: value}(func);
        if (!success) revert ExecutionFailed();

        if (!isOwner) {
            uint256 balanceAfter = usdc.balanceOf(address(this));
            uint256 spent = balanceBefore > balanceAfter ? balanceBefore - balanceAfter : 0;
            _enforceLimits(spent, balanceAfter);
        }

        emit TransactionExecuted(dest, value, func);
        return ret;
    }

    /// @notice USDC spent in the current rolling window (0 once the window has lapsed).
    function getDailySpent() external view returns (uint256) {
        if (block.timestamp >= windowStart + WINDOW) return 0;
        return dailySpent;
    }

    // ---------------------------------------------------------------------
    // Internals
    // ---------------------------------------------------------------------

    function _enforceLimits(uint256 spent, uint256 balanceAfter) private {
        // Calls that moved no USDC (e.g. balanceOf, or a 0-value approve) don't touch the caps.
        if (spent > 0) {
            if (spent > perTxCap) revert PerTxCapExceeded();

            // Roll the 24h window forward.
            // slither-disable-next-line timestamp
            if (block.timestamp >= windowStart + WINDOW) {
                windowStart = block.timestamp;
                dailySpent = 0;
            }

            uint256 newDaily = dailySpent + spent;
            if (newDaily > dailyCap) revert DailyCapExceeded();
            if (balanceAfter < reserveBalance) revert ReserveBreached();

            dailySpent = newDaily;
        }
    }

    /**
     * @dev A session key must not be able to hand out token allowances: a spender
     *      could pull the money later, outside execute(), dodging every cap.
     *      approve() is only allowed towards an allowlisted vendor, for <= perTxCap.
     */
    function _checkApprove(bytes calldata func) private view {
        if (func.length < 4 || bytes4(func[0:4]) != APPROVE_SELECTOR) return;
        if (func.length < 68) revert ForbiddenCall();
        (address spender, uint256 amount) = abi.decode(func[4:68], (address, uint256));
        if (!vendorAllowlist[spender] || amount > perTxCap) revert ForbiddenCall();
    }
}
