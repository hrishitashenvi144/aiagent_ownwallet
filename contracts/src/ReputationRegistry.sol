// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ReputationRegistry
 * @notice On-chain reputation registry tracking peer reviewer accuracy and scores.
 */
contract ReputationRegistry {
    struct Reputation {
        uint256 cumulativeScore;
        uint256 totalReviews;
    }

    mapping(address => Reputation) public reviewerReputation;
    mapping(bytes32 => bool) public jobRecorded;

    event ReviewRecorded(
        address indexed reviewer,
        bytes32 indexed jobId,
        uint8 score,
        uint256 newAverageScore,
        uint256 totalReviews
    );

    error InvalidScore();
    error AlreadyReviewed();
    error UnauthorizedCaller();

    function recordReview(
        address reviewer,
        bytes32 jobId,
        uint8 score,
        string calldata metadataUri
    ) external {
        if (score < 1 || score > 100) revert InvalidScore();
        if (jobRecorded[jobId]) revert AlreadyReviewed();

        jobRecorded[jobId] = true;
        Reputation storage rep = reviewerReputation[reviewer];
        rep.cumulativeScore += score;
        rep.totalReviews += 1;

        uint256 avg = rep.cumulativeScore / rep.totalReviews;
        emit ReviewRecorded(reviewer, jobId, score, avg, rep.totalReviews);
    }

    function getReputation(address reviewer) external view returns (uint256 averageScore, uint256 totalReviews) {
        Reputation memory rep = reviewerReputation[reviewer];
        if (rep.totalReviews == 0) {
            return (0, 0);
        }
        return (rep.cumulativeScore / rep.totalReviews, rep.totalReviews);
    }
}