// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ReputationRegistry} from "../src/ReputationRegistry.sol";

contract ReputationRegistryTest is Test {
    ReputationRegistry reg;

    address owner = makeAddr("owner");
    address agent = makeAddr("agent");
    address reviewer = makeAddr("reviewer");
    address other = makeAddr("other");

    event ReviewRecorded(
        address indexed reviewer, bytes32 indexed jobId, uint8 score, uint256 newAverageScore, uint256 totalReviews
    );
    event RecorderUpdated(address indexed recorder, bool allowed);

    function setUp() public {
        reg = new ReputationRegistry(owner);
        vm.prank(owner);
        reg.setRecorder(agent, true);
    }

    function test_EmptyReputation() public view {
        (uint256 avg, uint256 n) = reg.getReputation(reviewer);
        assertEq(avg, 0);
        assertEq(n, 0);
    }

    function test_SingleReview() public {
        vm.expectEmit(true, true, false, true);
        emit ReviewRecorded(reviewer, bytes32("j1"), 80, 80, 1);
        vm.prank(agent);
        reg.recordReview(reviewer, bytes32("j1"), 80, "ipfs://x");
        (uint256 avg, uint256 n) = reg.getReputation(reviewer);
        assertEq(avg, 80);
        assertEq(n, 1);
    }

    function test_RollingAverage() public {
        vm.startPrank(agent);
        reg.recordReview(reviewer, bytes32("j1"), 100, "");
        reg.recordReview(reviewer, bytes32("j2"), 50, "");
        reg.recordReview(reviewer, bytes32("j3"), 30, "");
        vm.stopPrank();
        (uint256 avg, uint256 n) = reg.getReputation(reviewer);
        assertEq(avg, 60); // 180 / 3
        assertEq(n, 3);
    }

    function test_AverageRoundsDown() public {
        vm.startPrank(agent);
        reg.recordReview(reviewer, bytes32("j1"), 1, "");
        reg.recordReview(reviewer, bytes32("j2"), 2, "");
        vm.stopPrank();
        (uint256 avg,) = reg.getReputation(reviewer);
        assertEq(avg, 1); // 3 / 2
    }

    function test_ReviewersAreIndependent() public {
        vm.startPrank(agent);
        reg.recordReview(reviewer, bytes32("j1"), 90, "");
        reg.recordReview(other, bytes32("j2"), 10, "");
        vm.stopPrank();
        (uint256 a1,) = reg.getReputation(reviewer);
        (uint256 a2,) = reg.getReputation(other);
        assertEq(a1, 90);
        assertEq(a2, 10);
    }

    function test_InvalidScore() public {
        vm.startPrank(agent);
        vm.expectRevert(ReputationRegistry.InvalidScore.selector);
        reg.recordReview(reviewer, bytes32("j1"), 0, "");
        vm.expectRevert(ReputationRegistry.InvalidScore.selector);
        reg.recordReview(reviewer, bytes32("j1"), 101, "");
        vm.stopPrank();
    }

    function test_BoundaryScoresAllowed() public {
        vm.startPrank(agent);
        reg.recordReview(reviewer, bytes32("j1"), 1, "");
        reg.recordReview(reviewer, bytes32("j2"), 100, "");
        vm.stopPrank();
        (, uint256 n) = reg.getReputation(reviewer);
        assertEq(n, 2);
    }

    function test_DuplicateJobReverts() public {
        vm.startPrank(agent);
        reg.recordReview(reviewer, bytes32("j1"), 80, "");
        vm.expectRevert(ReputationRegistry.AlreadyReviewed.selector);
        reg.recordReview(reviewer, bytes32("j1"), 90, "");
        vm.stopPrank();
    }

    function test_OnlyRecorder() public {
        vm.prank(other);
        vm.expectRevert(ReputationRegistry.UnauthorizedCaller.selector);
        reg.recordReview(reviewer, bytes32("j1"), 80, "");
    }

    function test_SetRecorder_OnlyOwner() public {
        vm.prank(other);
        vm.expectRevert(abi.encodeWithSelector(Ownable.OwnableUnauthorizedAccount.selector, other));
        reg.setRecorder(other, true);
    }

    function test_SetRecorder_RevokeAndEvent() public {
        vm.expectEmit(true, false, false, true);
        emit RecorderUpdated(agent, false);
        vm.prank(owner);
        reg.setRecorder(agent, false);
        vm.prank(agent);
        vm.expectRevert(ReputationRegistry.UnauthorizedCaller.selector);
        reg.recordReview(reviewer, bytes32("j1"), 80, "");
    }

    function testFuzz_AverageStaysInRange(uint8[] calldata scores) public {
        uint256 n = scores.length > 30 ? 30 : scores.length;
        uint256 sum;
        uint256 count;
        vm.startPrank(agent);
        for (uint256 i = 0; i < n; i++) {
            uint8 s = uint8(bound(scores[i], 1, 100));
            reg.recordReview(reviewer, keccak256(abi.encode(i)), s, "");
            sum += s;
            count++;
        }
        vm.stopPrank();
        (uint256 avg, uint256 total) = reg.getReputation(reviewer);
        assertEq(total, count);
        if (count > 0) {
            assertEq(avg, sum / count);
            assertGe(avg, 1);
            assertLe(avg, 100);
        } else {
            assertEq(avg, 0);
        }
    }
}
