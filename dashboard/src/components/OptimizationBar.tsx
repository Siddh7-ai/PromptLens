import React from 'react';

interface OptimizationBarProps {
  baselineTokens: number;
  compressedTokens: number;
  savingsPct: number;
}

export const OptimizationBar: React.FC<OptimizationBarProps> = ({
  baselineTokens,
  compressedTokens,
  savingsPct
}) => {
  return (
    <div className="headroom-card p-6 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-white">Context Optimization Ratio</h2>
          <p className="text-xs text-[#888888]">Baseline tokens vs compressed prompt payload sent to LLM model.</p>
        </div>
        <div className="text-xs font-mono text-[#888888]">
          Baseline: <span className="text-white font-semibold">{baselineTokens.toLocaleString()}</span> tokens | Compressed: <span className="text-white font-semibold">{compressedTokens.toLocaleString()}</span> tokens
        </div>
      </div>

      <div className="w-full bg-[#141414] rounded-lg h-3 p-0.5 border border-[#222222] relative overflow-hidden flex items-center">
        <div
          className="bg-white h-full rounded transition-all duration-500"
          style={{ width: `${Math.max(0, Math.min(100, savingsPct))}%` }}
        />
      </div>
      <div className="flex items-center justify-between text-xs text-[#666666]">
        <span>0%</span>
        <span className="font-medium text-[#aaaaaa]">
          Token Reduction Efficiency: <strong className="text-white">{savingsPct.toFixed(1)}%</strong>
        </span>
        <span>100%</span>
      </div>
    </div>
  );
};
