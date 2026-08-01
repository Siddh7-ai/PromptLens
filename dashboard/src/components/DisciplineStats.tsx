import React from 'react';
import { MetricsSummary } from '../types';
import { Zap, ShieldCheck } from 'lucide-react';

interface DisciplineStatsProps {
  metrics: MetricsSummary | null;
}

export const DisciplineStats: React.FC<DisciplineStatsProps> = ({ metrics }) => {
  const stats = metrics?.discipline_stats || {
    off: { requests: 0, output_tokens: 0 },
    lite: { requests: 0, output_tokens: 0 },
    full: { requests: 0, output_tokens: 0 },
    ultra: { requests: 0, output_tokens: 0 },
  };

  const modeOrder = ['off', 'lite', 'full', 'ultra'] as const;

  return (
    <div className="headroom-card p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-[#1f1f1f] pb-3">
        <div className="flex items-center space-x-2">
          <Zap className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-white">Agent Discipline — Output Token Savings</h3>
        </div>
        <span className="text-[11px] text-[#888888] font-mono flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> System Ruleset Injection
        </span>
      </div>

      <div className="grid grid-cols-4 gap-3 text-xs">
        {modeOrder.map((mode) => {
          const item = stats[mode] || { requests: 0, output_tokens: 0 };
          return (
            <div key={mode} className="bg-[#141414] border border-[#262626] rounded-lg p-3 space-y-1">
              <div className="text-[11px] font-bold text-[#888888] uppercase tracking-wider">{mode} Mode</div>
              <div className="text-lg font-mono font-bold text-white">
                {item.output_tokens.toLocaleString()} <span className="text-[10px] text-[#666666] font-sans font-normal">out tokens</span>
              </div>
              <div className="text-[11px] text-[#666666]">{item.requests} proxied requests</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
