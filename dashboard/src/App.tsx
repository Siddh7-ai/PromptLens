import React, { useState, useEffect } from 'react';
import { Sidebar, NavView } from './components/Sidebar';
import { StatCard } from './components/StatCard';
import { OptimizationBar } from './components/OptimizationBar';
import { BenchmarkTable } from './components/BenchmarkTable';
import { RequestStream } from './components/RequestStream';
import { Playground } from './components/Playground';
import { VaultInspector } from './components/VaultInspector';
import { SavingsChart } from './components/SavingsChart';
import { SettingsPanel } from './components/SettingsPanel';
import { DocsView } from './components/DocsView';
import { MetricsSummary } from './types';
import { RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<NavView>('overview');
  const [searchQuery, setSearchQuery] = useState<string>('');
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

  // Sync URL Path <-> NavView state cleanly
  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 3000);

    const syncViewFromUrl = () => {
      const pathname = window.location.pathname.replace(/^\//, '') || 'overview';
      const validViews: NavView[] = [
        'overview',
        'quickstart',
        'installation',
        'how-compression-works',
        'playground',
        'vault',
        'analytics',
        'benchmarks',
        'proxy-server',
        'architecture',
        'settings',
        'troubleshooting',
      ];
      if (validViews.includes(pathname as NavView)) {
        setCurrentView(pathname as NavView);
      }
    };

    syncViewFromUrl();
    window.addEventListener('popstate', syncViewFromUrl);

    return () => {
      clearInterval(interval);
      window.removeEventListener('popstate', syncViewFromUrl);
    };
  }, []);

  const handleNavigate = (view: NavView) => {
    const path = view === 'overview' ? '/overview' : `/${view}`;
    window.history.pushState({}, '', path);
    setCurrentView(view);
  };

  const vaultCount = metrics.recent_requests.filter((r) => r.retrieval_id !== '-').length;

  return (
    <div className="min-h-screen bg-[#000000] text-white flex font-sans antialiased">
      {/* Headroom Sidebar */}
      <Sidebar
        currentView={currentView}
        setCurrentView={handleNavigate}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        vaultCount={vaultCount}
      />

      {/* Main View Area */}
      <div className="flex-1 min-w-0 overflow-y-auto h-screen scroll-smooth">
        {/* Top Header Bar */}
        <header className="border-b border-[#1f1f1f] bg-[#050505] px-8 py-3.5 flex items-center justify-between sticky top-0 z-40">
          <div className="flex items-center space-x-3 text-xs text-[#888888]">
            <span className="font-mono text-[#555555]">PromptLens</span>
            <span>/</span>
            <span className="font-medium text-white capitalize">{currentView.replace(/-/g, ' ')}</span>
          </div>
          <button
            onClick={fetchStats}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#141414] hover:bg-[#1a1a1a] text-[#cccccc] border border-[#262626] transition flex items-center space-x-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5 text-[#888888]" />
            <span>Refresh Stats</span>
          </button>
        </header>

        {/* Dynamic Content Views */}
        <main className="p-8 max-w-7xl mx-auto space-y-8">
          {currentView === 'overview' && (
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
                  value={vaultCount}
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
          )}

          {currentView === 'vault' && <VaultInspector />}

          {currentView === 'playground' && <Playground />}

          {currentView === 'analytics' && <SavingsChart requests={metrics.recent_requests} />}

          {currentView === 'benchmarks' && <BenchmarkTable />}

          {currentView === 'settings' && <SettingsPanel />}

          {['quickstart', 'installation', 'how-compression-works', 'architecture', 'proxy-server', 'troubleshooting'].includes(
            currentView
          ) && <DocsView view={currentView} onNavigate={handleNavigate} />}
        </main>
      </div>
    </div>
  );
};
