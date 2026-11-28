// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";
import {AgentWallet} from "../src/AgentWallet.sol";
import {Escrow} from "../src/Escrow.sol";
import {MockUSDC} from "../src/mocks/MockUSDC.sol";

/// @dev A vendor that always reverts, to test ExecutionFailed.
contract RevertingVendor {
    fallback() external payable {
        revert("nope");
    }
}

contract AgentWalletTest is Test {
    MockUSDC usdc;
    AgentWallet wallet;
    Escrow vendor; // an allowlisted vendor contract

    address owner = makeAddr("owner");
    address agent = makeAddr("agent"); // session key
    address attacker = makeAddr("attacker");
    address payee = makeAddr("payee");

    event TransactionExecuted(address indexed target, uint256 value, bytes data);
    event SessionKeyUpdated(address indexed key, uint48 validUntil);
    event VendorStatusChanged(address indexed vendor, bool allowed);

    uint256 constant PER_TX = 5e6;
    uint256 constant DAILY = 25e6;
    uint256 constant RESERVE = 50e6;
    uint256 constant FUNDED = 200e6;

    function setUp() public {
        vm.warp(1_700_000_000);
        usdc = new MockUSDC();
        wallet = new AgentWallet(IERC20(address(usdc)), owner, PER_TX, DAILY, RESERVE);
        vendor = new Escrow(IERC20(address(usdc)));
        usdc.mint(address(wallet), FUNDED);

        vm.startPrank(owner);
        wallet.setVendorAllowlist(address(usdc), true); // lets the agent call transfer()
        wallet.setVendorAllowlist(address(vendor), true);
        wallet.setSessionKey(agent, uint48(block.timestamp + 1 days), uint48(block.timestamp));
        vm.stopPrank();
    }

    // helper: agent pays `amount` USDC to `to` through the wallet
    function _pay(address to, uint256 amount) internal {
        vm.prank(agent);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (to, amount)));
    }

    // ------------------------------------------------------------ config

    function test_Constructor() public view {
        assertEq(wallet.owner(), owner);
        assertEq(address(wallet.usdc()), address(usdc));
        assertEq(wallet.perTxCap(), PER_TX);
        assertEq(wallet.dailyCap(), DAILY);
        assertEq(wallet.reserveBalance(), RESERVE);
    }

    function test_Constructor_RevertsOnBadLimits() public {
        vm.expectRevert(AgentWallet.InvalidLimits.selector);
        new AgentWallet(IERC20(address(usdc)), owner, 10e6, 5e6, 0);
    }

    function test_OnlyOwnerCanConfigure() public {
        vm.startPrank(attacker);
        vm.expectRevert(AgentWallet.Unauthorized.selector);
        wallet.setLimits(1, 2, 3);
        vm.expectRevert(AgentWallet.Unauthorized.selector);
        wallet.setVendorAllowlist(attacker, true);
        vm.expectRevert(AgentWallet.Unauthorized.selector);
        wallet.setSessionKey(attacker, uint48(block.timestamp + 1), 0);
        vm.expectRevert(AgentWallet.Unauthorized.selector);
        wallet.pause();
        vm.expectRevert(AgentWallet.Unauthorized.selector);
        wallet.unpause();
        vm.expectRevert(AgentWallet.Unauthorized.selector);
        wallet.withdrawReserve(attacker, 1);
        vm.stopPrank();
    }

    function test_SetLimits() public {
        vm.prank(owner);
        wallet.setLimits(1e6, 2e6, 3e6);
        assertEq(wallet.perTxCap(), 1e6);
        assertEq(wallet.dailyCap(), 2e6);
        assertEq(wallet.reserveBalance(), 3e6);
    }

    function test_SetLimits_RevertsWhenPerTxAboveDaily() public {
        vm.prank(owner);
        vm.expectRevert(AgentWallet.InvalidLimits.selector);
        wallet.setLimits(10e6, 5e6, 0);
    }

    function test_VendorAllowlistEmitsEvent() public {
        vm.expectEmit(true, false, false, true);
        emit VendorStatusChanged(payee, true);
        vm.prank(owner);
        wallet.setVendorAllowlist(payee, true);
        assertTrue(wallet.vendorAllowlist(payee));
    }

    // ------------------------------------------------------------ caps

    function test_SessionKeyCanSpendWithinCaps() public {
        _pay(payee, 3e6);
        assertEq(usdc.balanceOf(payee), 3e6);
        assertEq(wallet.getDailySpent(), 3e6);
    }

    function test_PerTxCapExceeded() public {
        vm.prank(agent);
        vm.expectRevert(AgentWallet.PerTxCapExceeded.selector);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (payee, PER_TX + 1)));
    }

    function test_PerTxCapExactlyAllowed() public {
        _pay(payee, PER_TX);
        assertEq(usdc.balanceOf(payee), PER_TX);
    }

    function test_DailyCapExceeded() public {
        for (uint256 i = 0; i < 5; i++) {
            _pay(payee, PER_TX); // 5 x 5 = 25 = dailyCap
        }
        assertEq(wallet.getDailySpent(), DAILY);
        vm.prank(agent);
        vm.expectRevert(AgentWallet.DailyCapExceeded.selector);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (payee, 1)));
    }

    function test_DailyWindowResetsAfter24h() public {
        for (uint256 i = 0; i < 5; i++) {
            _pay(payee, PER_TX);
        }
        vm.warp(block.timestamp + 1 days);
        assertEq(wallet.getDailySpent(), 0);
        // session key from setUp lasts exactly 1 day -> refresh it
        vm.prank(owner);
        wallet.setSessionKey(agent, uint48(block.timestamp + 1 days), uint48(block.timestamp));
        _pay(payee, PER_TX);
        assertEq(wallet.getDailySpent(), PER_TX);
    }

    function test_WindowIsRollingNotCalendar() public {
        _pay(payee, PER_TX);
        uint256 start = wallet.windowStart();
        vm.warp(start + 1 days - 1);
        assertEq(wallet.getDailySpent(), PER_TX); // still same window
        vm.warp(start + 1 days);
        assertEq(wallet.getDailySpent(), 0);
    }

    function test_ReserveBreached() public {
        vm.prank(owner);
        wallet.setLimits(PER_TX, DAILY, FUNDED - 2e6); // only 2 USDC spendable
        vm.prank(agent);
        vm.expectRevert(AgentWallet.ReserveBreached.selector);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (payee, 3e6)));
        _pay(payee, 2e6); // exactly down to the reserve is fine
        assertEq(usdc.balanceOf(address(wallet)), FUNDED - 2e6);
    }

    function test_FailedSpendDoesNotConsumeDailyAllowance() public {
        vm.prank(agent);
        vm.expectRevert(AgentWallet.PerTxCapExceeded.selector);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (payee, PER_TX + 1)));
        assertEq(wallet.getDailySpent(), 0);
    }

    function test_ZeroSpendCallDoesNotCount() public {
        // balanceOf is a harmless view-style call on an allowlisted vendor
        vm.prank(agent);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.balanceOf, (payee)));
        assertEq(wallet.getDailySpent(), 0);
    }

    function test_IncomingFundsDoNotCountAsSpend() public {
        usdc.mint(address(wallet), 10e6);
        assertEq(wallet.getDailySpent(), 0);
    }

    function testFuzz_PerTxCapAlwaysEnforced(uint256 amount) public {
        amount = bound(amount, PER_TX + 1, FUNDED - RESERVE);
        vm.prank(agent);
        vm.expectRevert(AgentWallet.PerTxCapExceeded.selector);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (payee, amount)));
    }

    function testFuzz_DailySpendCap(uint256[] calldata amounts) public {
        uint256 spent;
        uint256 n = amounts.length > 20 ? 20 : amounts.length;
        for (uint256 i = 0; i < n; i++) {
            uint256 amt = bound(amounts[i], 1, PER_TX);
            vm.prank(agent);
            if (spent + amt > DAILY) {
                vm.expectRevert(AgentWallet.DailyCapExceeded.selector);
                wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (payee, amt)));
            } else {
                wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (payee, amt)));
                spent += amt;
            }
        }
        assertLe(wallet.getDailySpent(), DAILY);
        assertEq(wallet.getDailySpent(), spent);
        assertLe(usdc.balanceOf(payee), DAILY);
    }

    // ------------------------------------------------------------ session keys

    function test_SessionKeyNotYetValid() public {
        address k = makeAddr("future");
        vm.prank(owner);
        wallet.setSessionKey(k, uint48(block.timestamp + 2 hours), uint48(block.timestamp + 1 hours));
        vm.prank(k);
        vm.expectRevert(AgentWallet.SessionKeyExpired.selector);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (payee, 1)));
    }

    function test_SessionKeyExpired() public {
        vm.warp(block.timestamp + 1 days + 1);
        vm.prank(agent);
        vm.expectRevert(AgentWallet.SessionKeyExpired.selector);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (payee, 1)));
    }

    function test_SessionKeyValidAtBoundaries() public {
        (uint48 until,) = _window(agent);
        vm.warp(until); // exactly validUntil is still valid
        _pay(payee, 1);
    }

    function _window(address k) internal view returns (uint48 until, uint48 after_) {
        (until, after_) = wallet.sessionKeys(k);
    }

    function test_UnknownCallerUnauthorized() public {
        vm.prank(attacker);
        vm.expectRevert(AgentWallet.Unauthorized.selector);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (attacker, 1)));
    }

    function test_RevokeSessionKey() public {
        vm.prank(owner);
        wallet.setSessionKey(agent, 0, 0);
        vm.prank(agent);
        vm.expectRevert(AgentWallet.Unauthorized.selector);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (payee, 1)));
    }

    function test_SetSessionKey_InvalidWindow() public {
        vm.prank(owner);
        vm.expectRevert(AgentWallet.InvalidSessionWindow.selector);
        wallet.setSessionKey(agent, 100, 200);
    }

    function test_SessionKeyEmitsEvent() public {
        vm.expectEmit(true, false, false, true);
        emit SessionKeyUpdated(agent, 1_800_000_000);
        vm.prank(owner);
        wallet.setSessionKey(agent, 1_800_000_000, 1_700_000_000);
    }

    // ------------------------------------------------------------ allowlist

    function test_VendorNotAllowed() public {
        vm.prank(agent);
        vm.expectRevert(AgentWallet.VendorNotAllowed.selector);
        wallet.execute(attacker, 0, "");
    }

    function test_RemovedVendorBlocked() public {
        vm.prank(owner);
        wallet.setVendorAllowlist(address(usdc), false);
        vm.prank(agent);
        vm.expectRevert(AgentWallet.VendorNotAllowed.selector);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (payee, 1)));
    }

    function test_SessionKeyCannotSendEth() public {
        vm.deal(address(wallet), 1 ether);
        vm.prank(owner);
        wallet.setVendorAllowlist(payee, true);
        vm.prank(agent);
        vm.expectRevert(AgentWallet.ForbiddenCall.selector);
        wallet.execute(payee, 1 wei, "");
    }

    // ------------------------------------------------------------ approve guard

    function test_ApproveToNonVendorBlocked() public {
        vm.prank(agent);
        vm.expectRevert(AgentWallet.ForbiddenCall.selector);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.approve, (attacker, 1e6)));
    }

    function test_ApproveToVendorAllowedUpToPerTx() public {
        vm.prank(agent);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.approve, (address(vendor), PER_TX)));
        assertEq(usdc.allowance(address(wallet), address(vendor)), PER_TX);
    }

    function test_ApproveTooLargeBlocked() public {
        vm.prank(agent);
        vm.expectRevert(AgentWallet.ForbiddenCall.selector);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.approve, (address(vendor), PER_TX + 1)));
    }

    function test_MalformedApproveBlocked() public {
        vm.prank(agent);
        vm.expectRevert(AgentWallet.ForbiddenCall.selector);
        wallet.execute(address(usdc), 0, hex"095ea7b3");
    }

    function test_ShortCalldataIsNotTreatedAsApprove() public {
        vm.prank(agent);
        // 2 bytes of calldata hits the token's fallback -> reverts -> ExecutionFailed
        vm.expectRevert(AgentWallet.ExecutionFailed.selector);
        wallet.execute(address(usdc), 0, hex"aabb");
    }

    // ------------------------------------------------------------ pause

    function test_PauseBlocksExecute() public {
        vm.prank(owner);
        wallet.pause();
        vm.prank(agent);
        vm.expectRevert(Pausable.EnforcedPause.selector);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (payee, 1)));
        vm.prank(owner);
        vm.expectRevert(Pausable.EnforcedPause.selector);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (payee, 1)));
    }

    function test_UnpauseRestores() public {
        vm.startPrank(owner);
        wallet.pause();
        assertTrue(wallet.paused());
        wallet.unpause();
        vm.stopPrank();
        assertFalse(wallet.paused());
        _pay(payee, 1);
    }

    function test_OwnerCanWithdrawEvenWhenPaused() public {
        vm.startPrank(owner);
        wallet.pause();
        wallet.withdrawReserve(owner, 60e6);
        vm.stopPrank();
        assertEq(usdc.balanceOf(owner), 60e6);
    }

    // ------------------------------------------------------------ owner paths

    function test_OwnerExecuteIsNotCapped() public {
        vm.prank(owner);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.transfer, (payee, 100e6)));
        assertEq(usdc.balanceOf(payee), 100e6);
        assertEq(wallet.getDailySpent(), 0);
    }

    function test_OwnerCanSendEth() public {
        vm.deal(address(wallet), 1 ether);
        vm.prank(owner);
        wallet.execute(payee, 0.5 ether, "");
        assertEq(payee.balance, 0.5 ether);
    }

    function test_ExecutionFailedBubbles() public {
        RevertingVendor bad = new RevertingVendor();
        vm.startPrank(owner);
        wallet.setVendorAllowlist(address(bad), true);
        vm.expectRevert(AgentWallet.ExecutionFailed.selector);
        wallet.execute(address(bad), 0, hex"1234");
        vm.stopPrank();
    }

    function test_ExecuteEmitsEvent() public {
        bytes memory data = abi.encodeCall(IERC20.transfer, (payee, 1e6));
        vm.expectEmit(true, false, false, true);
        emit TransactionExecuted(address(usdc), 0, data);
        vm.prank(agent);
        wallet.execute(address(usdc), 0, data);
    }

    function test_ReceivesEth() public {
        vm.deal(address(this), 1 ether);
        (bool ok,) = address(wallet).call{value: 1 ether}("");
        assertTrue(ok);
        assertEq(address(wallet).balance, 1 ether);
    }

    // ------------------------------------------------------------ with Escrow

    function test_AgentCanFundEscrowWithinCaps() public {
        bytes32 jobId = keccak256("job-1");
        vm.startPrank(agent);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.approve, (address(vendor), 4e6)));
        wallet.execute(
            address(vendor), 0, abi.encodeCall(Escrow.createEscrow, (jobId, payee, 4e6, block.timestamp + 1 hours))
        );
        vm.stopPrank();
        assertEq(usdc.balanceOf(address(vendor)), 4e6);
        assertEq(wallet.getDailySpent(), 4e6); // pulled via transferFrom, still metered
    }

    function test_EscrowPullAboveCapReverts() public {
        // Owner pre-approves a huge allowance; the agent still cannot pull more than perTxCap via the vendor.
        vm.prank(owner);
        wallet.execute(address(usdc), 0, abi.encodeCall(IERC20.approve, (address(vendor), 100e6)));
        vm.prank(agent);
        vm.expectRevert(AgentWallet.PerTxCapExceeded.selector);
        wallet.execute(
            address(vendor),
            0,
            abi.encodeCall(Escrow.createEscrow, (keccak256("big"), payee, 10e6, block.timestamp + 1 hours))
        );
    }
}
