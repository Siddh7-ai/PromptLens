import React from 'react';
import { PromptLensLogo } from './PromptLensLogo';
import {
  LayoutDashboard,
  Database,
  Play,
  TrendingUp,
  Sliders,
  Search,
  Terminal,
  Code,
  BookOpen,
  Server,
  Layers,
  HelpCircle,
  BarChart3,
  ShieldCheck
} from 'lucide-react';

export type NavView =
  | 'overview'
  | 'quickstart'
  | 'installation'
  | 'how-compression-works'
  | 'playground'
  | 'vault'
  | 'analytics'
  | 'benchmarks'
  | 'proxy-server'
  | 'architecture'
  | 'settings'
  | 'troubleshooting';

interface SidebarProps {
  currentView: NavView;
  setCurrentView: (view: NavView) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  vaultCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  setCurrentView,
  searchQuery,
  setSearchQuery,
  vaultCount
}) => {
  const navigateTo = (view: NavView) => {
    const path = view === 'overview' ? '/overview' : `/${view}`;
    window.history.pushState({}, '', path);
    setCurrentView(view);
  };

  return (
    <aside className="w-64 bg-[#080808] border-r border-[#1a1a1a] flex flex-col justify-between h-screen sticky top-0 shrink-0 select-none">
      <div className="p-4 space-y-4 overflow-y-auto scrollbar-thin scrollbar-thumb-neutral-800">
        {/* Header Logo */}
        <div
          onClick={() => navigateTo('overview')}
          className="flex items-center space-x-3 px-2 pt-1 cursor-pointer group"
        >
          <PromptLensLogo className="w-7 h-5 object-contain" />
          <div className="flex items-center space-x-2">
            <span className="font-extrabold text-base tracking-tight text-white">PromptLens</span>
            <span className="px-1.5 py-0.5 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded">
              v0.1
            </span>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative px-1 pt-1">
          <Search className="w-3.5 h-3.5 text-neutral-500 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search docs or vault..."
            className="w-full bg-[#121212] text-xs text-neutral-200 placeholder-neutral-500 border border-[#222222] rounded-xl pl-8 pr-8 py-1.5 focus:outline-none focus:border-emerald-500/50 transition font-sans"
          />
          <kbd className="absolute right-3 top-2.5 px-1.5 py-0.5 text-[9px] font-mono text-neutral-500 bg-[#1a1a1a] border border-[#2e2e2e] rounded">
            Ctrl K
          </kbd>
        </div>

        {/* Headroom Sidebar Categories */}
        <div className="space-y-4 pt-2 text-xs">
          {/* CATEGORY 1: Getting Started */}
          <div className="space-y-1">
            <div className="px-3 text-[10px] font-bold text-neutral-500 uppercase tracking-widest">
              Getting Started
            </div>
            <button
              onClick={() => navigateTo('overview')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-lg font-medium transition ${
                currentView === 'overview'
                  ? 'bg-neutral-850 text-white font-bold border border-neutral-750'
                  : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5 text-emerald-400" />
              <span>Overview & Stats</span>
            </button>
            <button
              onClick={() => navigateTo('quickstart')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-lg font-medium transition ${
                currentView === 'quickstart'
                  ? 'bg-neutral-850 text-white font-bold border border-neutral-750'
                  : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
              }`}
            >
              <Terminal className="w-3.5 h-3.5 text-emerald-400" />
              <span>Quickstart</span>
            </button>
            <button
              onClick={() => navigateTo('installation')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-lg font-medium transition ${
                currentView === 'installation'
                  ? 'bg-neutral-850 text-white font-bold border border-neutral-750'
                  : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
              }`}
            >
              <Code className="w-3.5 h-3.5 text-neutral-400" />
              <span>Installation</span>
            </button>
          </div>

          {/* CATEGORY 2: Compression */}
          <div className="space-y-1">
            <div className="px-3 text-[10px] font-bold text-neutral-500 uppercase tracking-widest">
              Compression Engine
            </div>
            <button
              onClick={() => navigateTo('how-compression-works')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-lg font-medium transition ${
                currentView === 'how-compression-works'
                  ? 'bg-neutral-850 text-white font-bold border border-neutral-750'
                  : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5 text-emerald-400" />
              <span>How Compression Works</span>
            </button>
            <button
              onClick={() => navigateTo('playground')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-lg font-medium transition ${
                currentView === 'playground'
                  ? 'bg-neutral-850 text-white font-bold border border-neutral-750'
                  : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
              }`}
            >
              <Play className="w-3.5 h-3.5 text-emerald-400" />
              <span>Interactive Playground ✨</span>
            </button>
          </div>

          {/* CATEGORY 3: Reversible Vault */}
          <div className="space-y-1">
            <div className="px-3 text-[10px] font-bold text-neutral-500 uppercase tracking-widest flex items-center justify-between">
              <span>Reversible Compression</span>
              {vaultCount > 0 && (
                <span className="px-1.5 py-0.2 text-[9px] font-mono rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold">
                  {vaultCount}
                </span>
              )}
            </div>
            <button
              onClick={() => navigateTo('vault')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-lg font-medium transition ${
                currentView === 'vault'
                  ? 'bg-neutral-850 text-white font-bold border border-neutral-750'
                  : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
              }`}
            >
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <span>Vault Inspector (CCR)</span>
            </button>
          </div>

          {/* CATEGORY 4: Observability */}
          <div className="space-y-1">
            <div className="px-3 text-[10px] font-bold text-neutral-500 uppercase tracking-widest">
              Observability
            </div>
            <button
              onClick={() => navigateTo('analytics')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-lg font-medium transition ${
                currentView === 'analytics'
                  ? 'bg-neutral-850 text-white font-bold border border-neutral-750'
                  : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
              <span>Token Savings Hub</span>
            </button>
            <button
              onClick={() => navigateTo('benchmarks')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-lg font-medium transition ${
                currentView === 'benchmarks'
                  ? 'bg-neutral-850 text-white font-bold border border-neutral-750'
                  : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5 text-neutral-400" />
              <span>5-Task Benchmarks</span>
            </button>
          </div>

          {/* CATEGORY 5: Proxy & Architecture */}
          <div className="space-y-1">
            <div className="px-3 text-[10px] font-bold text-neutral-500 uppercase tracking-widest">
              Architecture & Proxy
            </div>
            <button
              onClick={() => navigateTo('proxy-server')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-lg font-medium transition ${
                currentView === 'proxy-server'
                  ? 'bg-neutral-850 text-white font-bold border border-neutral-750'
                  : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
              }`}
            >
              <Server className="w-3.5 h-3.5 text-emerald-400" />
              <span>Proxy Server</span>
            </button>
            <button
              onClick={() => navigateTo('architecture')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-lg font-medium transition ${
                currentView === 'architecture'
                  ? 'bg-neutral-850 text-white font-bold border border-neutral-750'
                  : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
              }`}
            >
              <Layers className="w-3.5 h-3.5 text-neutral-400" />
              <span>Architecture</span>
            </button>
          </div>

          {/* CATEGORY 6: Configuration */}
          <div className="space-y-1">
            <div className="px-3 text-[10px] font-bold text-neutral-500 uppercase tracking-widest">
              Configuration
            </div>
            <button
              onClick={() => navigateTo('settings')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-lg font-medium transition ${
                currentView === 'settings'
                  ? 'bg-neutral-850 text-white font-bold border border-neutral-750'
                  : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
              }`}
            >
              <Sliders className="w-3.5 h-3.5 text-emerald-400" />
              <span>Rule Settings & Sliders</span>
            </button>
          </div>

          {/* CATEGORY 7: Help */}
          <div className="space-y-1">
            <div className="px-3 text-[10px] font-bold text-neutral-500 uppercase tracking-widest">
              Help
            </div>
            <button
              onClick={() => navigateTo('troubleshooting')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-lg font-medium transition ${
                currentView === 'troubleshooting'
                  ? 'bg-neutral-850 text-white font-bold border border-neutral-750'
                  : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
              }`}
            >
              <HelpCircle className="w-3.5 h-3.5 text-neutral-400" />
              <span>Troubleshooting & FAQs</span>
            </button>
          </div>
        </div>
      </div>

      {/* Footer info */}
      <div className="p-4 border-t border-[#1a1a1a] bg-[#050505]">
        <div className="flex items-center justify-between text-xs text-neutral-400">
          <span className="flex items-center gap-1.5 font-medium">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Proxy Active
          </span>
          <span className="font-mono text-[10px] text-neutral-500">:8000</span>
        </div>
      </div>
    </aside>
  );
};
