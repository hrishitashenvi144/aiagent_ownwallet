// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console2} from "forge-std/Script.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {AgentWallet} from "../src/AgentWallet.sol";
import {Escrow} from "../src/Escrow.sol";
import {ReputationRegistry} from "../src/ReputationRegistry.sol";
import {MockUSDC} from "../src/mocks/MockUSDC.sol";

/**
 * Deploys MockUSDC (unless USDC_ADDRESS is set), AgentWallet, Escrow, ReputationRegistry.
 *
 * Env vars (read from your shell / .env - NEVER commit keys):
 *   PRIVATE_KEY   deployer key (testnet only!)
 *   OWNER         owner of wallet + registry (defaults to deployer)
 *   USDC_ADDRESS  optional existing token; otherwise MockUSDC is deployed
 *
 * Local:  forge script script/Deploy.s.sol:DeployScript --rpc-url http://127.0.0.1:8545 --broadcast
 * Sepolia: forge script script/Deploy.s.sol:DeployScript --rpc-url base_sepolia --broadcast --verify
 */
contract DeployScript is Script {
    // USDC has 6 decimals: 5 USDC per tx, 25 USDC per day, 50 USDC reserve.
    uint256 internal constant PER_TX_CAP = 5e6;
    uint256 internal constant DAILY_CAP = 25e6;
    uint256 internal constant RESERVE = 50e6;

    function run() external returns (address usdc, address wallet, address escrow, address reputation) {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerKey);
        address owner = vm.envOr("OWNER", deployer);
        address existingUsdc = vm.envOr("USDC_ADDRESS", address(0));

        vm.startBroadcast(deployerKey);

        usdc = existingUsdc == address(0) ? address(new MockUSDC()) : existingUsdc;
        AgentWallet w = new AgentWallet(IERC20(usdc), owner, PER_TX_CAP, DAILY_CAP, RESERVE);
        Escrow e = new Escrow(IERC20(usdc));
        ReputationRegistry r = new ReputationRegistry(owner);

        vm.stopBroadcast();

        wallet = address(w);
        escrow = address(e);
        reputation = address(r);

        console2.log("USDC:", usdc);
        console2.log("AgentWallet:", wallet);
        console2.log("Escrow:", escrow);
        console2.log("ReputationRegistry:", reputation);
    }
}
