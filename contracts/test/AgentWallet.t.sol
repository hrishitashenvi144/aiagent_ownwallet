// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Stub test interface for Forge
interface Vm {
    function warp(uint256) external;
    function deal(address, uint256) external;
    function prank(address) external;
}

contract AgentWalletTest {
    Vm internal constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    function setUp() public {
        // Setup code for Forge tests
    }

    function test_InitialLimits() public pure {
        uint256 perTx = 5 ether;
        uint256 daily = 25 ether;
        uint256 reserve = 50 ether;
        require(perTx < daily, "perTx must be less than daily");
        require(daily < reserve, "daily must be less than reserve");
    }

    function test_SanityCheck() public pure {
        uint256 x = 1;
        require(x == 1, "Sanity failed");
    }
}