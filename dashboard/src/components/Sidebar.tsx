import React from 'react';
import {
  LayoutDashboard,
  Database,
  Play,
  TrendingUp,
  Sliders,
  Search,
  Zap,
  Github,
  CheckCircle2
} from 'lucide-react';

export type NavView = 'overview' | 'vault' | 'playground' | 'analytics' | 'settings';

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
  return (
    <aside className="w-64 bg-[#0a0a0a] border-r border-[#1f1f1f] flex flex-col justify-between h-screen sticky top-0 shrink-0 select-none">
      <div className="p-4 space-y-5 overflow-y-auto">
        {/* Header Logo */}
        <div className="flex items-center space-x-3 px-2 pt-1">
          <div className="w-7 h-7 rounded-md bg-[#1c1c1c] border border-[#2e2e2e] flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-base tracking-tight text-white">PromptLens</span>
            <span className="px-1.5 py-0.5 text-[10px] font-mono text-[#888888] bg-[#141414] border border-[#262626] rounded">
              v0.1
            </span>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative px-1">
          <Search className="w-3.5 h-3.5 text-[#666666] absolute left-3.5 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search vault or logs..."
            className="w-full bg-[#121212] text-xs text-[#cccccc] placeholder-[#555555] border border-[#222222] rounded-lg pl-8 pr-8 py-1.5 focus:outline-none focus:border-[#444444] transition font-sans"
          />
          <kbd className="absolute right-3 top-2 px-1.5 py-0.5 text-[9px] font-mono text-[#555555] bg-[#1a1a1a] border border-[#2e2e2e] rounded">
            Ctrl K
          </kbd>
        </div>

        {/* Navigation Sections */}
        <div className="space-y-4 pt-1">
          {/* Section 1: Getting Started */}
          <div className="space-y-1">
            <div className="px-3 text-[11px] font-semibold text-[#666666] uppercase tracking-wider">
              Getting Started
            </div>
            <button
              onClick={() => setCurrentView('overview')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                currentView === 'overview'
                  ? 'bg-[#222222] text-white font-semibold'
                  : 'text-[#888888] hover:text-white hover:bg-[#121212]'
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              <span>Overview & Stats</span>
            </button>
          </div>

          {/* Section 2: Reversible Vault */}
          <div className="space-y-1">
            <div className="px-3 text-[11px] font-semibold text-[#666666] uppercase tracking-wider flex items-center justify-between">
              <span>Reversible Store</span>
              {vaultCount > 0 && (
                <span className="px-1.5 py-0.2 text-[9px] font-mono rounded bg-[#1c1c1c] text-[#aaaaaa]">
                  {vaultCount}
                </span>
              )}
            </div>
            <button
              onClick={() => setCurrentView('vault')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                currentView === 'vault'
                  ? 'bg-[#222222] text-white font-semibold'
                  : 'text-[#888888] hover:text-white hover:bg-[#121212]'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>Vault Inspector</span>
            </button>
          </div>

          {/* Section 3: Interactive Tools */}
          <div className="space-y-1">
            <div className="px-3 text-[11px] font-semibold text-[#666666] uppercase tracking-wider">
              Interactive Tools
            </div>
            <button
              onClick={() => setCurrentView('playground')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                currentView === 'playground'
                  ? 'bg-[#222222] text-white font-semibold'
                  : 'text-[#888888] hover:text-white hover:bg-[#121212]'
              }`}
            >
              <Play className="w-3.5 h-3.5" />
              <span>Playground ✨</span>
            </button>
            <button
              onClick={() => setCurrentView('analytics')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                currentView === 'analytics'
                  ? 'bg-[#222222] text-white font-semibold'
                  : 'text-[#888888] hover:text-white hover:bg-[#121212]'
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5" />
              <span>Token Savings Chart</span>
            </button>
          </div>

          {/* Section 4: Configuration */}
          <div className="space-y-1">
            <div className="px-3 text-[11px] font-semibold text-[#666666] uppercase tracking-wider">
              Configuration
            </div>
            <button
              onClick={() => setCurrentView('settings')}
              className={`w-full flex items-center space-x-2.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                currentView === 'settings'
                  ? 'bg-[#222222] text-white font-semibold'
                  : 'text-[#888888] hover:text-white hover:bg-[#121212]'
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Rules & Settings</span>
            </button>
          </div>
        </div>
      </div>

      {/* Footer Status */}
      <div className="p-4 border-t border-[#1f1f1f] bg-[#070707] space-y-3">
        <div className="flex items-center justify-between text-xs text-[#888888]">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-medium text-white">Proxy Online</span>
          </div>
          <span className="font-mono text-[10px] text-[#555555]">Port 8000</span>
        </div>
        <a
          href="https://github.com/Siddh7-ai/PromptLens"
          target="_blank"
          rel="noreferrer"
          className="flex items-center space-x-2 text-xs text-[#666666] hover:text-white transition"
        >
          <Github className="w-3.5 h-3.5" />
          <span>GitHub Repository</span>
        </a>
      </div>
    </aside>
  );
};
