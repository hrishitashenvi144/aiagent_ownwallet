// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console2} from "forge-std/Script.sol";
import {AgentWallet} from "../src/AgentWallet.sol";
import {ReputationRegistry} from "../src/ReputationRegistry.sol";
import {MockUSDC} from "../src/mocks/MockUSDC.sol";

/**
 * Post-deploy setup so the agent (Person 3) can actually use the wallet. Run as the OWNER.
 *
 * Env: PRIVATE_KEY (owner), AGENT_WALLET_ADDRESS, ESCROW_CONTRACT_ADDRESS, USDC_TOKEN_ADDRESS,
 *      REPUTATION_REGISTRY_ADDRESS, SESSION_KEY_ADDRESS (public address of the agent's session key),
 *      SESSION_DAYS (optional, default 7), MINT_USDC (optional, whole USDC to mint to the wallet - MockUSDC only)
 *
 * What it does:
 *   1. allowlists USDC + Escrow as vendors (session key can only touch these)
 *   2. authorises the session key for SESSION_DAYS days
 *   3. lets the session key write reviews to the ReputationRegistry
 *   4. (optional) mints MockUSDC into the wallet
 */
contract ConfigureScript is Script {
    function run() external {
        uint256 ownerKey = vm.envUint("PRIVATE_KEY");
        AgentWallet wallet = AgentWallet(payable(vm.envAddress("AGENT_WALLET_ADDRESS")));
        address escrow = vm.envAddress("ESCROW_CONTRACT_ADDRESS");
        address usdc = vm.envAddress("USDC_TOKEN_ADDRESS");
        ReputationRegistry registry = ReputationRegistry(vm.envAddress("REPUTATION_REGISTRY_ADDRESS"));
        address sessionKey = vm.envAddress("SESSION_KEY_ADDRESS");
        uint256 sessionDays = vm.envOr("SESSION_DAYS", uint256(7));
        uint256 mintUsdc = vm.envOr("MINT_USDC", uint256(0));

        vm.startBroadcast(ownerKey);
        wallet.setVendorAllowlist(usdc, true);
        wallet.setVendorAllowlist(escrow, true);
        wallet.setSessionKey(sessionKey, uint48(block.timestamp + sessionDays * 1 days), uint48(block.timestamp));
        registry.setRecorder(sessionKey, true);
        if (mintUsdc > 0) MockUSDC(usdc).mint(address(wallet), mintUsdc * 1e6);
        vm.stopBroadcast();

        console2.log("Configured wallet:", address(wallet));
        console2.log("Session key:", sessionKey);
        console2.log("Valid for days:", sessionDays);
    }
}
