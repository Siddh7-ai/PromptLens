import React from 'react';
import { Activity, RefreshCw } from 'lucide-react';

interface NavbarProps {
  onRefresh: () => void;
  activeTab: 'overview' | 'playground';
  setActiveTab: (tab: 'overview' | 'playground') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onRefresh, activeTab, setActiveTab }) => {
  return (
    <header className="border-b border-[#1f1f1f] bg-[#000000] sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-[#181818] border border-[#2e2e2e] flex items-center justify-center">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-semibold text-base tracking-tight text-white">PromptLens</span>
                <span className="px-2 py-0.5 text-[10px] font-mono font-medium rounded bg-[#1a1a1a] text-[#888888] border border-[#2e2e2e]">
                  v0.1.0
                </span>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-1 bg-[#0d0d0d] p-1 rounded-lg border border-[#1f1f1f]">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                activeTab === 'overview'
                  ? 'bg-[#222222] text-white shadow-sm'
                  : 'text-[#888888] hover:text-white hover:bg-[#181818]'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('playground')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                activeTab === 'playground'
                  ? 'bg-[#222222] text-white shadow-sm'
                  : 'text-[#888888] hover:text-white hover:bg-[#181818]'
              }`}
            >
              Playground ✨
            </button>
          </nav>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-[#121212] border border-[#262626] text-[#888888] text-xs font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 pulse-dot"></span>
            <span className="hidden sm:inline text-white">Proxy Active</span>
          </div>
          <button
            onClick={onRefresh}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#141414] hover:bg-[#1a1a1a] text-[#cccccc] border border-[#262626] transition flex items-center space-x-2"
          >
            <RefreshCw className="w-3.5 h-3.5 text-[#888888]" />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>
    </header>
  );
};
