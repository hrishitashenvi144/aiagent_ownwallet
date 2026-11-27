// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ReputationRegistry
 * @notice On-chain reputation registry for peer reviewer agents.
 *         Scores are 1..100; the average is cumulative / totalReviews
 *         (integer division, rounds down).
 *         Only addresses approved by the owner (e.g. the primary agent) may
 *         record reviews, so strangers cannot spam or smear a reviewer.
 */
contract ReputationRegistry is Ownable {
    struct Reputation {
        uint256 cumulativeScore;
        uint256 totalReviews;
    }

    mapping(address => Reputation) public reviewerReputation;
    mapping(bytes32 => bool) public jobRecorded;
    mapping(address => bool) public recorders;

    event ReviewRecorded(
        address indexed reviewer, bytes32 indexed jobId, uint8 score, uint256 newAverageScore, uint256 totalReviews
    );
    event RecorderUpdated(address indexed recorder, bool allowed);

    error InvalidScore();
    error AlreadyReviewed();
    error UnauthorizedCaller();

    constructor(address _owner) Ownable(_owner) {}

    function setRecorder(address recorder, bool allowed) external onlyOwner {
        recorders[recorder] = allowed;
        emit RecorderUpdated(recorder, allowed);
    }

    function recordReview(address reviewer, bytes32 jobId, uint8 score, string calldata /* metadataUri */ )
        external
    {
        if (!recorders[msg.sender]) revert UnauthorizedCaller();
        if (score < 1 || score > 100) revert InvalidScore();
        if (jobRecorded[jobId]) revert AlreadyReviewed();

        jobRecorded[jobId] = true;
        Reputation storage rep = reviewerReputation[reviewer];
        rep.cumulativeScore += score;
        rep.totalReviews += 1;

        emit ReviewRecorded(reviewer, jobId, score, rep.cumulativeScore / rep.totalReviews, rep.totalReviews);
    }

    function getReputation(address reviewer) external view returns (uint256 averageScore, uint256 totalReviews) {
        Reputation memory rep = reviewerReputation[reviewer];
        if (rep.totalReviews == 0) return (0, 0);
        return (rep.cumulativeScore / rep.totalReviews, rep.totalReviews);
    }
}
