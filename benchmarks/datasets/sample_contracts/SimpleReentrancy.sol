// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title SimpleReentrancy
 * @notice Canonical SWC-107 Reentrancy vulnerability.
 */
contract SimpleReentrancy {
    mapping(address => uint256) public balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() external {
        uint256 bal = balances[msg.sender];
        require(bal > 0, "Zero balance");

        // Vulnerability: State change occurs after external call
        (bool success, ) = msg.sender.call{value: bal}("");
        require(success, "Failed");

        balances[msg.sender] = 0;
    }
}