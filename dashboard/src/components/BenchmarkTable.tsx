import React from 'react';
import { BenchmarkTask } from '../types';

const INITIAL_BENCHMARKS: BenchmarkTask[] = [
  { id: 1, name: 'Python Pytest Failure Trace', category: 'Pins failure anchors & error stack traces, drops passing noise', baseline: 1061, compressed: 730, savings_pct: 22.6, correctness: '100% Pass' },
  { id: 2, name: 'JSON arrays (tool outputs)', category: 'Statistical key sampling & structural depth truncation', baseline: 118154, compressed: 984, savings_pct: 99.1, correctness: '100% Pass' },
  { id: 3, name: 'Git diffs', category: 'Preserves change hunks, drops unchanged context', baseline: 606, compressed: 518, savings_pct: -0.5, correctness: '100% Pass' },
  { id: 4, name: 'Build/test logs', category: 'Collapses repetitive prefixes, pins compiler error codes', baseline: 1270, compressed: 682, savings_pct: 39.1, correctness: '100% Pass' },
  { id: 5, name: 'Plain text & file dumps', category: 'Generates Structural Index ToC & head-tail truncation', baseline: 947, compressed: 465, savings_pct: 41.3, correctness: '100% Pass' },
];

export const BenchmarkTable: React.FC = () => {
  return (
    <div className="headroom-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">What gets compressed</h2>
          <p className="text-xs text-[#888888]">Pre-computed token savings across 5 representative real-world AI agent tool outputs.</p>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded bg-[#161616] text-[#aaaaaa] border border-[#2e2e2e]">
          5 / 5 Tasks Passing
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-[#1f1f1f] bg-[#0f0f0f] text-[#888888] font-medium">
              <th className="py-3 px-4">Content type</th>
              <th className="py-3 px-4">What happens</th>
              <th className="py-3 px-4 text-right">Baseline Tokens</th>
              <th className="py-3 px-4 text-right">Compressed Tokens</th>
              <th className="py-3 px-4 text-right">Typical savings</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#181818] text-[#cccccc]">
            {INITIAL_BENCHMARKS.map((task) => (
              <tr key={task.id} className="hover:bg-[#121212] transition">
                <td className="py-3 px-4 font-semibold text-white">{task.name}</td>
                <td className="py-3 px-4 text-[#888888]">{task.category}</td>
                <td className="py-3 px-4 text-right font-mono text-[#888888]">{task.baseline.toLocaleString()}</td>
                <td className="py-3 px-4 text-right font-mono text-white font-semibold">{task.compressed.toLocaleString()}</td>
                <td className="py-3 px-4 text-right font-mono font-semibold text-white">{task.savings_pct.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
