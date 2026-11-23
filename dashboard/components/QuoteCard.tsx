import React from "react";

interface QuoteCardProps {
  depth: string;
  price: number;
  timeEstimate: string;
  description: string;
  selected: boolean;
  onSelect: () => void;
}

export default function QuoteCard({
  depth,
  price,
  timeEstimate,
  description,
  selected,
  onSelect
}: QuoteCardProps) {
  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer rounded-xl border p-4 transition-all ${
        selected
          ? "border-emerald-500 bg-emerald-500/10 shadow-lg shadow-emerald-500/5"
          : "border-slate-800 bg-slate-900/50 hover:border-slate-700"
      }`}
    >
      <div className="flex justify-between items-start mb-2">
        <h4 className="font-semibold capitalize text-slate-100">{depth} Tier</h4>
        <span className="text-emerald-400 font-bold text-lg">${price} USDC</span>
      </div>
      <p className="text-xs text-slate-400 mb-3">{description}</p>
      <div className="text-[11px] text-slate-500">
        Estimated Time: <span className="text-slate-300 font-medium">{timeEstimate}</span>
      </div>
    </div>
  );
}