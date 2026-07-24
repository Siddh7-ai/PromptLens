import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { StatCard } from './components/StatCard';
import { OptimizationBar } from './components/OptimizationBar';
import { BenchmarkTable } from './components/BenchmarkTable';
import { RequestStream } from './components/RequestStream';
import { Playground } from './components/Playground';
import { MetricsSummary } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'playground'>('overview');
  const [metrics, setMetrics] = useState<MetricsSummary>({
    total_requests: 0,
    total_baseline_tokens: 0,
    total_compressed_tokens: 0,
    total_tokens_saved: 0,
    overall_savings_pct: 0,
    estimated_usd_saved: 0,
    total_retrievals: 0,
    recent_requests: [],
  });

  const fetchStats = async () => {
    try {
      const resp = await fetch('http://localhost:8000/api/stats');
      if (resp.ok) {
        const data: MetricsSummary = await resp.json();
        setMetrics(data);
      }
    } catch (err) {
      console.error('Failed to fetch stats from proxy:', err);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen pb-16 bg-[#000000] text-white font-sans">
      <Navbar onRefresh={fetchStats} activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-8">
        {activeTab === 'overview' ? (
          <>
            {/* Header Summary */}
            <div className="space-y-1">
              <h1 className="text-3xl font-bold tracking-tight text-white">Community stats</h1>
              <p className="text-sm text-[#888888]">
                Real-time token reduction, rule-based compression metrics, and reversible vault storage.
              </p>
            </div>

            {/* Stat Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Tokens Saved"
                value={metrics.total_tokens_saved.toLocaleString()}
                subtitle="Tokens Cut from LLM context window"
                badge={`+${metrics.overall_savings_pct.toFixed(1)}%`}
              />
              <StatCard
                title="Cost Saved"
                value={`$${metrics.estimated_usd_saved.toFixed(4)}`}
                subtitle="Based on $3.00/1M input tokens"
              />
              <StatCard
                title="Active Instances"
                value={metrics.recent_requests.filter((r) => r.retrieval_id !== '-').length}
                subtitle="Active original payloads stored in vault"
              />
              <StatCard
                title="Requests Optimized"
                value={metrics.total_requests}
                subtitle="Proxied requests / tool retrievals"
                badge={`${metrics.total_retrievals} fetches`}
              />
            </div>

            {/* Context Optimization Bar */}
            <OptimizationBar
              baselineTokens={metrics.total_baseline_tokens}
              compressedTokens={metrics.total_compressed_tokens}
              savingsPct={metrics.overall_savings_pct}
            />

            {/* 5-Task Benchmark Comparison Suite */}
            <BenchmarkTable />

            {/* Recent Requests Audit Stream */}
            <RequestStream logs={metrics.recent_requests} />
          </>
        ) : (
          <Playground />
        )}
      </main>
    </div>
  );
};
