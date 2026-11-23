import React from "react";

export default function Header() {
  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="h-8 w-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center font-bold text-emerald-400">
          AA
        </div>
        <div>
          <span className="font-semibold text-lg text-slate-100">AuditAgent</span>
          <span className="ml-2 text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full">
            Base Sepolia
          </span>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <nav className="flex gap-4 text-sm text-slate-300">
          <a href="/" className="hover:text-emerald-400 transition-colors">Submit Code</a>
          <a href="/owner" className="hover:text-emerald-400 transition-colors">Owner Console</a>
        </nav>
        <button className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium px-3 py-1.5 rounded-md transition-colors">
          Connect Wallet
        </button>
      </div>
    </header>
  );
}