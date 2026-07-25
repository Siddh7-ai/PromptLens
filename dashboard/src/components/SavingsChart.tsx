import React, { useState } from 'react';
import { RequestLog } from '../types';
import { Zap, DollarSign, Layers, BarChart3, PieChart, Sparkles, Filter } from 'lucide-react';

interface SavingsChartProps {
  requests: RequestLog[];
}

export const SavingsChart: React.FC<SavingsChartProps> = ({ requests }) => {
  const [viewMode, setViewMode] = useState<'comparison' | 'donut' | 'pipeline'>('donut');

  // Fallback benchmark data if live request history is empty
  const rawChartData =
    requests.length > 0
      ? requests.slice(0, 6)
      : [
          { id: 1, path: 'large_json_array.json', baseline_tokens: 118154, compressed_tokens: 991, savings_pct: 99.2 },
          { id: 2, path: 'pytest_failure.log', baseline_tokens: 1061, compressed_tokens: 829, savings_pct: 21.9 },
          { id: 3, path: 'env_vars.txt', baseline_tokens: 947, compressed_tokens: 657, savings_pct: 30.6 },
          { id: 4, path: 'git_diff.patch', baseline_tokens: 606, compressed_tokens: 498, savings_pct: 17.8 },
          { id: 5, path: 'npm_build.log', baseline_tokens: 376, compressed_tokens: 376, savings_pct: 0.0 },
        ];

  const totalBaseline = rawChartData.reduce((acc, d) => acc + d.baseline_tokens, 0);
  const totalCompressed = rawChartData.reduce((acc, d) => acc + d.compressed_tokens, 0);
  const totalSaved = Math.max(0, totalBaseline - totalCompressed);
  const avgSavingsPct = totalBaseline > 0 ? (totalSaved / totalBaseline) * 100 : 0;
  const usdSaved = (totalSaved / 1_000_000) * 3.0;

  const maxTokens = Math.max(...rawChartData.map((d) => d.baseline_tokens), 1000);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-emerald-400 animate-pulse" />
            Token Optimization Hub
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            Visual analytics comparing raw incoming prompt size against PromptLens optimized payloads.
          </p>
        </div>

        {/* View Mode Switcher Buttons */}
        <div className="inline-flex p-1.5 bg-neutral-900/90 border border-neutral-800 rounded-2xl shadow-inner self-start sm:self-auto backdrop-blur-md">
          <button
            onClick={() => setViewMode('donut')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all duration-300 ${
              viewMode === 'donut'
                ? 'bg-gradient-to-r from-emerald-500/20 to-teal-500/20 text-emerald-300 border border-emerald-500/40 shadow-lg shadow-emerald-500/10'
                : 'text-neutral-400 hover:text-white'
            }`}
          >
            <PieChart className="w-4 h-4" />
            <span>Radial Ring Gauge</span>
          </button>
          <button
            onClick={() => setViewMode('pipeline')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all duration-300 ${
              viewMode === 'pipeline'
                ? 'bg-gradient-to-r from-emerald-500/20 to-teal-500/20 text-emerald-300 border border-emerald-500/40 shadow-lg shadow-emerald-500/10'
                : 'text-neutral-400 hover:text-white'
            }`}
          >
            <Filter className="w-4 h-4" />
            <span>Compression Pipeline</span>
          </button>
          <button
            onClick={() => setViewMode('comparison')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all duration-300 ${
              viewMode === 'comparison'
                ? 'bg-gradient-to-r from-emerald-500/20 to-teal-500/20 text-emerald-300 border border-emerald-500/40 shadow-lg shadow-emerald-500/10'
                : 'text-neutral-400 hover:text-white'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Pillar Bars</span>
          </button>
        </div>
      </div>

      {/* Highlights Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-neutral-900/80 border border-neutral-800 rounded-2xl p-5 flex items-center justify-between transition hover:border-emerald-500/30">
          <div>
            <p className="text-xs text-neutral-400 font-semibold uppercase tracking-wider">Total Tokens Cut</p>
            <p className="text-2xl font-black text-white mt-1">{totalSaved.toLocaleString()}</p>
          </div>
          <div className="w-11 h-11 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Zap className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-neutral-900/80 border border-neutral-800 rounded-2xl p-5 flex items-center justify-between transition hover:border-emerald-500/30">
          <div>
            <p className="text-xs text-neutral-400 font-semibold uppercase tracking-wider">Estimated Money Saved</p>
            <p className="text-2xl font-black text-emerald-400 mt-1">${usdSaved.toFixed(4)}</p>
          </div>
          <div className="w-11 h-11 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <DollarSign className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-neutral-900/80 border border-neutral-800 rounded-2xl p-5 flex items-center justify-between transition hover:border-purple-500/30">
          <div>
            <p className="text-xs text-neutral-400 font-semibold uppercase tracking-wider">Payloads Evaluated</p>
            <p className="text-2xl font-black text-white mt-1">{rawChartData.length}</p>
          </div>
          <div className="w-11 h-11 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
            <Layers className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Main Graph Card Container */}
      <div className="bg-neutral-950 border border-neutral-850 rounded-2xl p-6 shadow-2xl relative overflow-hidden backdrop-blur-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

        {/* VIEW 1: RADIAL RING GAUGE (DONUT) */}
        {viewMode === 'donut' && (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
            {/* Left SVG Donut Gauge */}
            <div className="md:col-span-5 flex flex-col items-center justify-center p-4">
              <div className="relative w-64 h-64 flex items-center justify-center overflow-visible">
                {/* Seamless Circular Backdrop Glow */}
                <div className="absolute inset-4 bg-emerald-500/15 rounded-full blur-2xl pointer-events-none" />

                <svg className="w-full h-full transform -rotate-90 overflow-visible relative z-10" viewBox="0 0 100 100">
                  {/* Outer Background Ring */}
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    className="text-neutral-850"
                    strokeWidth="10"
                    stroke="currentColor"
                    fill="transparent"
                  />
                  {/* Glowing Emerald Progress Arc */}
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    className="text-emerald-400 transition-all duration-1000 ease-out"
                    strokeWidth="10"
                    strokeDasharray="251.2"
                    strokeDashoffset={251.2 - (251.2 * avgSavingsPct) / 100}
                    strokeLinecap="round"
                    stroke="currentColor"
                    fill="transparent"
                  />
                </svg>

                {/* Center Percentage Display */}
                <div className="absolute z-20 flex flex-col items-center justify-center text-center">
                  <span className="text-4xl font-black text-white tracking-tight">
                    {avgSavingsPct.toFixed(1)}%
                  </span>
                  <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-widest mt-1">
                    Tokens Saved
                  </span>
                </div>
              </div>
            </div>

            {/* Right Metric Breakdown */}
            <div className="md:col-span-7 space-y-5">
              <div>
                <h3 className="text-lg font-bold text-white">Efficiency Breakdown</h3>
                <p className="text-xs text-neutral-400">Proportion of tokens cut vs context delivered to LLM</p>
              </div>

              {/* Card 1: Tokens Cut */}
              <div className="p-4 rounded-xl bg-neutral-900/80 border border-emerald-500/30 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 rounded-full bg-emerald-400 shadow-md shadow-emerald-500/50" />
                  <div>
                    <p className="text-xs text-neutral-400 font-semibold">Tokens Cut (Saved)</p>
                    <p className="text-lg font-bold text-white">{totalSaved.toLocaleString()} tokens</p>
                  </div>
                </div>
                <span className="px-2.5 py-1 rounded-md text-xs font-black bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  {avgSavingsPct.toFixed(1)}% Cut
                </span>
              </div>

              {/* Card 2: Tokens Delivered */}
              <div className="p-4 rounded-xl bg-neutral-900/80 border border-neutral-800 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 rounded-full bg-neutral-600" />
                  <div>
                    <p className="text-xs text-neutral-400 font-semibold">Tokens Delivered to LLM</p>
                    <p className="text-lg font-bold text-white">{totalCompressed.toLocaleString()} tokens</p>
                  </div>
                </div>
                <span className="px-2.5 py-1 rounded-md text-xs font-bold bg-neutral-800 text-neutral-400">
                  {(100 - avgSavingsPct).toFixed(1)}% Payload
                </span>
              </div>

              {/* Summary note */}
              <div className="p-3 rounded-xl bg-neutral-900/40 border border-neutral-850 flex items-center justify-between text-xs text-neutral-400">
                <span>Baseline Incoming Volume:</span>
                <strong className="text-white font-mono">{totalBaseline.toLocaleString()} tokens</strong>
              </div>
            </div>
          </div>
        )}

        {/* VIEW 2: COMPRESSION PIPELINE (FUNNEL) */}
        {viewMode === 'pipeline' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-base font-bold text-white">Context Compression Pipeline Flow</h3>
              <p className="text-xs text-neutral-400">How raw tool outputs are processed through PromptLens rules</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
              {/* STAGE 1 */}
              <div className="p-5 rounded-2xl bg-neutral-900/90 border border-neutral-800 flex flex-col justify-between space-y-4">
                <div>
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
                    Stage 1: Raw Output
                  </span>
                  <h4 className="text-xl font-bold text-white mt-2">{totalBaseline.toLocaleString()} <span className="text-xs font-normal text-neutral-400">tokens</span></h4>
                  <p className="text-xs text-neutral-400 mt-1">Uncompressed tool outputs (JSON arrays, stack traces, git diffs)</p>
                </div>
                <div className="w-full bg-neutral-800 rounded-full h-2">
                  <div className="bg-red-500/60 h-full rounded-full w-full" />
                </div>
              </div>

              {/* STAGE 2 */}
              <div className="p-5 rounded-2xl bg-neutral-900/90 border border-emerald-500/40 flex flex-col justify-between space-y-4 relative shadow-lg shadow-emerald-500/5">
                <div>
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                    Stage 2: PromptLens Rule Engine
                  </span>
                  <h4 className="text-xl font-bold text-emerald-400 mt-2">-{totalSaved.toLocaleString()} <span className="text-xs font-normal text-emerald-500">tokens</span></h4>
                  <ul className="text-xs text-neutral-300 mt-2 space-y-1">
                    <li className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      <span>Rule-Based JSON Skimming</span>
                    </li>
                    <li className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      <span>Log & Trace Trimming</span>
                    </li>
                    <li className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      <span>SHA-256 Vaulting & Tool Injection</span>
                    </li>
                  </ul>
                </div>
                <div className="w-full bg-neutral-800 rounded-full h-2">
                  <div className="bg-emerald-400 h-full rounded-full w-full animate-pulse" />
                </div>
              </div>

              {/* STAGE 3 */}
              <div className="p-5 rounded-2xl bg-neutral-900/90 border border-teal-500/40 flex flex-col justify-between space-y-4 shadow-lg shadow-teal-500/5">
                <div>
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-teal-300 bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/30">
                    Stage 3: LLM Context Delivered
                  </span>
                  <h4 className="text-xl font-bold text-white mt-2">{totalCompressed.toLocaleString()} <span className="text-xs font-normal text-neutral-400">tokens</span></h4>
                  <p className="text-xs text-neutral-400 mt-1">Ultra-lean prompt payload sent to Anthropic API model</p>
                </div>
                <div className="w-full bg-neutral-800 rounded-full h-2">
                  <div className="bg-teal-400 h-full rounded-full" style={{ width: `${Math.max(2, (totalCompressed / totalBaseline) * 100)}%` }} />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* VIEW 3: PILLAR COMPARISON BARS */}
        {viewMode === 'comparison' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-neutral-800 pb-4">
              <div>
                <h3 className="text-base font-bold text-white">Vertical Pillar Comparison</h3>
                <p className="text-xs text-neutral-400">Gray Pillar = Original Tokens | Glowing Green Pillar = PromptLens Tokens</p>
              </div>
              <div className="flex items-center space-x-4 text-xs font-mono">
                <div className="flex items-center space-x-2">
                  <span className="w-3 h-3 rounded bg-red-500/30 border border-red-500/50 inline-block" />
                  <span className="text-neutral-400">Original</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-3 h-3 rounded bg-emerald-500 inline-block shadow-sm shadow-emerald-500" />
                  <span className="text-emerald-400 font-bold">PromptLens</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4 items-end pt-4 min-h-[220px]">
              {rawChartData.map((item, idx) => {
                const baselineH = Math.max(20, (item.baseline_tokens / maxTokens) * 160);
                const compressedH = Math.max(8, (item.compressed_tokens / maxTokens) * 160);

                return (
                  <div key={idx} className="flex flex-col items-center space-y-3 group p-3 rounded-xl bg-neutral-900/60 border border-neutral-800 hover:border-emerald-500/40 transition">
                    <span className="text-[10px] font-mono text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      {item.savings_pct.toFixed(0)}% Saved
                    </span>

                    {/* Dual Pillars */}
                    <div className="flex items-end space-x-2 h-[160px] w-full justify-center">
                      {/* Baseline Pillar */}
                      <div
                        className="w-5 bg-neutral-700 rounded-t-md transition-all duration-700 group-hover:bg-neutral-600"
                        style={{ height: `${baselineH}px` }}
                        title={`Original: ${item.baseline_tokens} tokens`}
                      />
                      {/* Compressed Pillar */}
                      <div
                        className="w-5 bg-gradient-to-t from-emerald-600 via-emerald-400 to-teal-300 rounded-t-md transition-all duration-700 shadow-lg shadow-emerald-500/40"
                        style={{ height: `${compressedH}px` }}
                        title={`Compressed: ${item.compressed_tokens} tokens`}
                      />
                    </div>

                    <span className="text-[11px] font-mono text-neutral-300 truncate w-full text-center font-semibold">
                      {item.path}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
