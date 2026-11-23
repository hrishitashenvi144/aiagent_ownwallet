"use client";

import React, { useState } from "react";
import QuoteCard from "@/components/QuoteCard";

export default function Home() {
  const [sourceCode, setSourceCode] = useState(`// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VulnerableVault {
    mapping(address => uint256) public balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() external {
        uint256 balance = balances[msg.sender];
        require(balance > 0, "No balance");
        
        (bool ok, ) = msg.sender.call{value: balance}("");
        require(ok, "Transfer failed");
        
        balances[msg.sender] = 0;
    }
}`);
  const [selectedDepth, setSelectedDepth] = useState("standard");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [report, setReport] = useState<any>(null);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      // In full implementation, handles HTTP 402 and web3 payment modal
      const res = await fetch("http://localhost:8000/quote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contract_source: sourceCode, scan_depth: selectedDepth })
      });
      if (res.ok) {
        // Mock preview for UI check
        setReport({
          status: "quoted",
          depth: selectedDepth
        });
      }
    } catch (e) {
      console.log("Using offline mock mode");
      setReport({ status: "ready_for_payment" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">
          Autonomous Solidity Security Triage
        </h1>
        <p className="text-slate-400 max-w-2xl text-sm">
          Submit contract source code and pay in testnet USDC. The agent executes containerized static analysis, LLM triage, and generates executable Foundry fuzz tests.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Solidity Source Code
            </label>
            <span className="text-xs text-slate-500">Target: Solidity ^0.8.20</span>
          </div>
          <textarea
            value={sourceCode}
            onChange={(e) => setSourceCode(e.target.value)}
            rows={16}
            className="w-full font-mono text-xs bg-slate-900 border border-slate-800 rounded-xl p-4 focus:outline-none focus:border-emerald-500 text-slate-200"
          />
        </div>

        <div className="space-y-4">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Select Triage Tier
          </label>
          <div className="space-y-3">
            <QuoteCard
              depth="quick"
              price={10}
              timeEstimate="< 60 seconds"
              description="Fast scan using Slither AST detectors and basic sanity checks."
              selected={selectedDepth === "quick"}
              onSelect={() => setSelectedDepth("quick")}
            />
            <QuoteCard
              depth="standard"
              price={15}
              timeEstimate="< 3 minutes"
              description="Slither + Aderyn + LLM false positive filtering and ranked risk summary."
              selected={selectedDepth === "standard"}
              onSelect={() => setSelectedDepth("standard")}
            />
            <QuoteCard
              depth="deep"
              price={30}
              timeEstimate="< 6 minutes"
              description="Full multi-engine pipeline + LLM-synthesized Foundry PoC fuzz tests + secondary reviewer consensus check."
              selected={selectedDepth === "deep"}
              onSelect={() => setSelectedDepth("deep")}
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="w-full mt-4 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 rounded-xl transition-all shadow-lg shadow-emerald-600/20 text-sm"
          >
            {isSubmitting ? "Generating Quote..." : "Get Quote & Submit (x402)"}
          </button>
        </div>
      </div>
    </div>
  );
}