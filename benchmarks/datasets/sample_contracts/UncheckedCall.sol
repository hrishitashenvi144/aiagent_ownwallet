// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title UncheckedCall
 * @notice Canonical SWC-104 Unchecked Low-Level Call vulnerability.
 */
contract UncheckedCall {
    function sendEther(address payable recipient, uint256 amount) external {
        // Vulnerability: Return value of low level call ignored
        recipient.call{value: amount}("");
    }
}