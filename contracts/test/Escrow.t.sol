// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {StdInvariant} from "forge-std/StdInvariant.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Escrow} from "../src/Escrow.sol";
import {MockUSDC} from "../src/mocks/MockUSDC.sol";

contract EscrowTest is Test {
    MockUSDC usdc;
    Escrow escrow;

    address client = makeAddr("client");
    address reviewer = makeAddr("reviewer");
    address attacker = makeAddr("attacker");

    bytes32 constant JOB = keccak256("job-1");
    uint256 constant AMOUNT = 10e6;

    event EscrowCreated(
        bytes32 indexed jobId, address indexed client, address indexed reviewer, uint256 amount, uint256 deadline
    );
    event EscrowReleased(bytes32 indexed jobId, address indexed reviewer, uint256 amount);
    event EscrowRefunded(bytes32 indexed jobId, address indexed client, uint256 amount);

    function setUp() public {
        vm.warp(1_700_000_000);
        usdc = new MockUSDC();
        escrow = new Escrow(IERC20(address(usdc)));
        usdc.mint(client, 1000e6);
        vm.prank(client);
        usdc.approve(address(escrow), type(uint256).max);
    }

    function _create() internal returns (uint256 deadline) {
        deadline = block.timestamp + 1 hours;
        vm.prank(client);
        escrow.createEscrow(JOB, reviewer, AMOUNT, deadline);
    }

    function test_Create() public {
        uint256 deadline = block.timestamp + 1 hours;
        vm.expectEmit(true, true, true, true);
        emit EscrowCreated(JOB, client, reviewer, AMOUNT, deadline);
        vm.prank(client);
        escrow.createEscrow(JOB, reviewer, AMOUNT, deadline);

        (address c, address r, uint256 a, uint256 d, uint8 s) = escrow.getEscrow(JOB);
        assertEq(c, client);
        assertEq(r, reviewer);
        assertEq(a, AMOUNT);
        assertEq(d, deadline);
        assertEq(s, 1); // Active
        assertEq(usdc.balanceOf(address(escrow)), AMOUNT);
        assertEq(usdc.balanceOf(client), 1000e6 - AMOUNT);
    }

    function test_Create_Duplicate() public {
        _create();
        vm.prank(client);
        vm.expectRevert(Escrow.EscrowAlreadyExists.selector);
        escrow.createEscrow(JOB, reviewer, AMOUNT, block.timestamp + 1 hours);
    }

    function test_Create_Validation() public {
        vm.startPrank(client);
        vm.expectRevert(Escrow.InvalidAmount.selector);
        escrow.createEscrow(JOB, reviewer, 0, block.timestamp + 1 hours);
        vm.expectRevert(Escrow.InvalidReviewer.selector);
        escrow.createEscrow(JOB, address(0), AMOUNT, block.timestamp + 1 hours);
        vm.expectRevert(Escrow.InvalidReviewer.selector);
        escrow.createEscrow(JOB, client, AMOUNT, block.timestamp + 1 hours);
        vm.expectRevert(Escrow.InvalidDeadline.selector);
        escrow.createEscrow(JOB, reviewer, AMOUNT, block.timestamp);
        vm.stopPrank();
    }

    function test_Create_WithoutAllowanceReverts() public {
        vm.prank(attacker);
        vm.expectRevert(); // ERC20InsufficientAllowance
        escrow.createEscrow(JOB, reviewer, AMOUNT, block.timestamp + 1 hours);
        // and nothing was stored
        (,,,, uint8 s) = escrow.getEscrow(JOB);
        assertEq(s, 0);
    }

    function test_Release() public {
        _create();
        vm.expectEmit(true, true, false, true);
        emit EscrowReleased(JOB, reviewer, AMOUNT);
        vm.prank(client);
        escrow.releaseEscrow(JOB);
        assertEq(usdc.balanceOf(reviewer), AMOUNT);
        assertEq(usdc.balanceOf(address(escrow)), 0);
        (,,,, uint8 s) = escrow.getEscrow(JOB);
        assertEq(s, 2); // Released
    }

    function test_Release_OnlyClient() public {
        _create();
        vm.prank(attacker);
        vm.expectRevert(Escrow.Unauthorized.selector);
        escrow.releaseEscrow(JOB);
        vm.prank(reviewer);
        vm.expectRevert(Escrow.Unauthorized.selector);
        escrow.releaseEscrow(JOB); // reviewer cannot self-release
    }

    function test_Release_NotFound() public {
        vm.expectRevert(Escrow.EscrowNotFound.selector);
        escrow.releaseEscrow(JOB);
    }

    function test_Release_Twice() public {
        _create();
        vm.startPrank(client);
        escrow.releaseEscrow(JOB);
        vm.expectRevert(Escrow.EscrowNotActive.selector);
        escrow.releaseEscrow(JOB);
        vm.stopPrank();
    }

    function test_Release_AfterDeadlineStillAllowedIfNotRefunded() public {
        uint256 deadline = _create();
        vm.warp(deadline + 1);
        vm.prank(client);
        escrow.releaseEscrow(JOB);
        assertEq(usdc.balanceOf(reviewer), AMOUNT);
    }

    function test_Refund_AfterDeadline() public {
        uint256 deadline = _create();
        vm.warp(deadline + 1);
        vm.expectEmit(true, true, false, true);
        emit EscrowRefunded(JOB, client, AMOUNT);
        vm.prank(client);
        escrow.refundEscrow(JOB);
        assertEq(usdc.balanceOf(client), 1000e6);
        (,,,, uint8 s) = escrow.getEscrow(JOB);
        assertEq(s, 3); // Refunded
    }

    function test_Refund_BeforeDeadlineReverts() public {
        uint256 deadline = _create();
        vm.prank(client);
        vm.expectRevert(Escrow.DeadlineNotPassed.selector);
        escrow.refundEscrow(JOB);
        vm.warp(deadline); // deadline itself is still "not passed"
        vm.prank(client);
        vm.expectRevert(Escrow.DeadlineNotPassed.selector);
        escrow.refundEscrow(JOB);
    }

    function test_Refund_OnlyClient() public {
        uint256 deadline = _create();
        vm.warp(deadline + 1);
        vm.prank(attacker);
        vm.expectRevert(Escrow.Unauthorized.selector);
        escrow.refundEscrow(JOB);
    }

    function test_Refund_NotFound() public {
        vm.expectRevert(Escrow.EscrowNotFound.selector);
        escrow.refundEscrow(JOB);
    }

    function test_Refund_AfterReleaseReverts() public {
        uint256 deadline = _create();
        vm.startPrank(client);
        escrow.releaseEscrow(JOB);
        vm.warp(deadline + 1);
        vm.expectRevert(Escrow.EscrowNotActive.selector);
        escrow.refundEscrow(JOB);
        vm.stopPrank();
    }

    function test_Release_AfterRefundReverts() public {
        uint256 deadline = _create();
        vm.warp(deadline + 1);
        vm.startPrank(client);
        escrow.refundEscrow(JOB);
        vm.expectRevert(Escrow.EscrowNotActive.selector);
        escrow.releaseEscrow(JOB);
        vm.stopPrank();
    }

    function test_JobIdCannotBeReusedAfterSettlement() public {
        _create();
        vm.startPrank(client);
        escrow.releaseEscrow(JOB);
        vm.expectRevert(Escrow.EscrowAlreadyExists.selector);
        escrow.createEscrow(JOB, reviewer, AMOUNT, block.timestamp + 1 hours);
        vm.stopPrank();
    }

    function testFuzz_ReleaseOrRefundPaysExactlyOnce(uint96 amount, bool release) public {
        amount = uint96(bound(amount, 1, 1000e6));
        bytes32 id = keccak256(abi.encode(amount, release));
        uint256 deadline = block.timestamp + 1 hours;
        vm.startPrank(client);
        escrow.createEscrow(id, reviewer, amount, deadline);
        if (release) {
            escrow.releaseEscrow(id);
            assertEq(usdc.balanceOf(reviewer), amount);
        } else {
            vm.warp(deadline + 1);
            escrow.refundEscrow(id);
            assertEq(usdc.balanceOf(client), 1000e6);
        }
        vm.stopPrank();
        assertEq(usdc.balanceOf(address(escrow)), 0);
    }
}

/// @dev Handler: the fuzzer calls these with random actors/jobs/times.
contract EscrowHandler is Test {
    MockUSDC public usdc;
    Escrow public escrow;
    address[] public actors;
    bytes32[] public jobs;

    uint256 public totalDeposited;
    uint256 public totalPaidOut; // released + refunded

    constructor(MockUSDC _usdc, Escrow _escrow) {
        usdc = _usdc;
        escrow = _escrow;
        for (uint256 i = 0; i < 4; i++) {
            address a = address(uint160(0xA000 + i));
            actors.push(a);
            usdc.mint(a, 1_000_000e6);
            vm.prank(a);
            usdc.approve(address(escrow), type(uint256).max);
        }
    }

    function jobCount() external view returns (uint256) {
        return jobs.length;
    }

    function create(uint256 actorSeed, uint256 reviewerSeed, uint96 amount, uint32 ttl) external {
        address c = actors[actorSeed % actors.length];
        address r = actors[(reviewerSeed % (actors.length - 1) + 1 + actorSeed) % actors.length];
        if (r == c) return;
        amount = uint96(bound(amount, 1, 10_000e6));
        ttl = uint32(bound(ttl, 1, 30 days));
        bytes32 id = keccak256(abi.encode(jobs.length));
        vm.prank(c);
        escrow.createEscrow(id, r, amount, block.timestamp + ttl);
        jobs.push(id);
        totalDeposited += amount;
    }

    function release(uint256 jobSeed, uint256 callerSeed) external {
        if (jobs.length == 0) return;
        bytes32 id = jobs[jobSeed % jobs.length];
        address caller = actors[callerSeed % actors.length];
        (address c,, uint256 amt,, uint8 status) = escrow.getEscrow(id);
        vm.prank(caller);
        try escrow.releaseEscrow(id) {
            require(caller == c && status == 1, "released without authorisation");
            totalPaidOut += amt;
        } catch {}
    }

    function refund(uint256 jobSeed, uint256 callerSeed) external {
        if (jobs.length == 0) return;
        bytes32 id = jobs[jobSeed % jobs.length];
        address caller = actors[callerSeed % actors.length];
        (address c,, uint256 amt, uint256 deadline, uint8 status) = escrow.getEscrow(id);
        vm.prank(caller);
        try escrow.refundEscrow(id) {
            require(caller == c && status == 1 && block.timestamp > deadline, "refunded without authorisation");
            totalPaidOut += amt;
        } catch {}
    }

    function warp(uint32 secs) external {
        vm.warp(block.timestamp + bound(secs, 1, 3 days));
    }
}

/// @notice Proves funds can only leave the escrow via an authorised release or an
///         expired-deadline refund by the client.
contract EscrowInvariantTest is StdInvariant, Test {
    MockUSDC usdc;
    Escrow escrow;
    EscrowHandler handler;

    function setUp() public {
        vm.warp(1_700_000_000);
        usdc = new MockUSDC();
        escrow = new Escrow(IERC20(address(usdc)));
        handler = new EscrowHandler(usdc, escrow);
        targetContract(address(handler));
    }

    /// Escrow's token balance == deposits - payouts (nothing leaks, nothing is stuck).
    function invariant_BalanceMatchesAccounting() public view {
        assertEq(usdc.balanceOf(address(escrow)), handler.totalDeposited() - handler.totalPaidOut());
    }

    /// Escrow balance == sum of amounts of Active escrows.
    function invariant_BalanceEqualsActiveEscrows() public view {
        uint256 active;
        for (uint256 i = 0; i < handler.jobCount(); i++) {
            (,, uint256 amt,, uint8 status) = escrow.getEscrow(handler.jobs(i));
            if (status == 1) active += amt;
        }
        assertEq(usdc.balanceOf(address(escrow)), active);
    }
}
