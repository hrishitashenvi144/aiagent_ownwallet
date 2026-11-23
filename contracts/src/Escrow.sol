// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Escrow
 * @notice Holds reviewer bounties for multi-agent second-opinion verification.
 */
contract Escrow {
    enum Status { None, Active, Released, Refunded }

    struct EscrowItem {
        address client;
        address reviewer;
        uint256 amount;
        uint256 deadline;
        Status status;
    }

    mapping(bytes32 => EscrowItem) public escrows;

    event EscrowCreated(bytes32 indexed jobId, address indexed client, address indexed reviewer, uint256 amount, uint256 deadline);
    event EscrowReleased(bytes32 indexed jobId, address indexed reviewer, uint256 amount);
    event EscrowRefunded(bytes32 indexed jobId, address indexed client, uint256 amount);

    error EscrowAlreadyExists();
    error EscrowNotFound();
    error EscrowNotActive();
    error DeadlineNotPassed();
    error Unauthorized();
    error TransferFailed();

    function createEscrow(
        bytes32 jobId,
        address reviewer,
        uint256 amount,
        uint256 deadline
    ) external payable {
        if (escrows[jobId].status != Status.None) revert EscrowAlreadyExists();
        if (msg.value != amount) revert TransferFailed();

        escrows[jobId] = EscrowItem({
            client: msg.sender,
            reviewer: reviewer,
            amount: amount,
            deadline: deadline,
            status: Status.Active
        });

        emit EscrowCreated(jobId, msg.sender, reviewer, amount, deadline);
    }

    function releaseEscrow(bytes32 jobId) external {
        EscrowItem storage item = escrows[jobId];
        if (item.status != Status.Active) revert EscrowNotActive();
        if (msg.sender != item.client) revert Unauthorized();

        item.status = Status.Released;
        (bool ok, ) = item.reviewer.call{value: item.amount}("");
        if (!ok) revert TransferFailed();

        emit EscrowReleased(jobId, item.reviewer, item.amount);
    }

    function refundEscrow(bytes32 jobId) external {
        EscrowItem storage item = escrows[jobId];
        if (item.status != Status.Active) revert EscrowNotActive();
        if (block.timestamp <= item.deadline) revert DeadlineNotPassed();
        if (msg.sender != item.client) revert Unauthorized();

        item.status = Status.Refunded;
        (bool ok, ) = item.client.call{value: item.amount}("");
        if (!ok) revert TransferFailed();

        emit EscrowRefunded(jobId, item.client, item.amount);
    }

    function getEscrow(bytes32 jobId) external view returns (
        address client,
        address reviewer,
        uint256 amount,
        uint256 deadline,
        uint8 status
    ) {
        EscrowItem memory item = escrows[jobId];
        return (item.client, item.reviewer, item.amount, item.deadline, uint8(item.status));
    }
}