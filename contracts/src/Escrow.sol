// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title Escrow
 * @notice Holds USDC bounties for second-opinion reviewer agents.
 *
 * Flow: the client (our AgentWallet) locks `amount` for a job. Only the client
 * can release the money to the reviewer (client authorisation). If the reviewer
 * never delivers, the client can take the money back once the deadline passed.
 * Nobody else - not even the reviewer - can move the funds in any other way.
 */
contract Escrow is ReentrancyGuard {
    using SafeERC20 for IERC20;

    enum Status {
        None,
        Active,
        Released,
        Refunded
    }

    struct EscrowItem {
        address client;
        address reviewer;
        uint256 amount;
        uint256 deadline;
        Status status;
    }

    IERC20 public immutable usdc;
    mapping(bytes32 => EscrowItem) public escrows;

    event EscrowCreated(
        bytes32 indexed jobId, address indexed client, address indexed reviewer, uint256 amount, uint256 deadline
    );
    event EscrowReleased(bytes32 indexed jobId, address indexed reviewer, uint256 amount);
    event EscrowRefunded(bytes32 indexed jobId, address indexed client, uint256 amount);

    error EscrowAlreadyExists();
    error EscrowNotFound();
    error EscrowNotActive();
    error DeadlineNotPassed();
    error Unauthorized();
    error InvalidAmount();
    error InvalidReviewer();
    error InvalidDeadline();

    constructor(IERC20 _usdc) {
        usdc = _usdc;
    }

    /// @notice Lock `amount` USDC (caller must have approved this contract).
    function createEscrow(bytes32 jobId, address reviewer, uint256 amount, uint256 deadline) external nonReentrant {
        if (escrows[jobId].status != Status.None) revert EscrowAlreadyExists();
        if (amount == 0) revert InvalidAmount();
        if (reviewer == address(0) || reviewer == msg.sender) revert InvalidReviewer();
        if (deadline <= block.timestamp) revert InvalidDeadline();

        // Effects before interaction (checks-effects-interactions).
        escrows[jobId] = EscrowItem({
            client: msg.sender,
            reviewer: reviewer,
            amount: amount,
            deadline: deadline,
            status: Status.Active
        });

        usdc.safeTransferFrom(msg.sender, address(this), amount);

        emit EscrowCreated(jobId, msg.sender, reviewer, amount, deadline);
    }

    /// @notice Client pays the reviewer.
    function releaseEscrow(bytes32 jobId) external nonReentrant {
        EscrowItem storage item = escrows[jobId];
        if (item.status == Status.None) revert EscrowNotFound();
        if (item.status != Status.Active) revert EscrowNotActive();
        if (msg.sender != item.client) revert Unauthorized();

        item.status = Status.Released;
        usdc.safeTransfer(item.reviewer, item.amount);

        emit EscrowReleased(jobId, item.reviewer, item.amount);
    }

    /// @notice Client reclaims funds after the deadline.
    function refundEscrow(bytes32 jobId) external nonReentrant {
        EscrowItem storage item = escrows[jobId];
        if (item.status == Status.None) revert EscrowNotFound();
        if (item.status != Status.Active) revert EscrowNotActive();
        if (msg.sender != item.client) revert Unauthorized();
        if (block.timestamp <= item.deadline) revert DeadlineNotPassed();

        item.status = Status.Refunded;
        usdc.safeTransfer(item.client, item.amount);

        emit EscrowRefunded(jobId, item.client, item.amount);
    }

    function getEscrow(bytes32 jobId)
        external
        view
        returns (address client, address reviewer, uint256 amount, uint256 deadline, uint8 status)
    {
        EscrowItem memory item = escrows[jobId];
        return (item.client, item.reviewer, item.amount, item.deadline, uint8(item.status));
    }
}
