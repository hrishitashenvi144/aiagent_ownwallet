// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../src/AgentWallet.sol";
import "../src/Escrow.sol";
import "../src/ReputationRegistry.sol";

contract DeployScript {
    function run() external returns (address walletAddr, address escrowAddr, address repAddr) {
        // Deploy parameters: 5 ETH perTx, 25 ETH daily, 50 ETH reserve
        AgentWallet wallet = new AgentWallet(5 ether, 25 ether, 50 ether);
        Escrow escrow = new Escrow();
        ReputationRegistry rep = new ReputationRegistry();

        walletAddr = address(wallet);
        escrowAddr = address(escrow);
        repAddr = address(rep);
    }
}