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
  ShieldCheck,
  GitCompare,
  X
} from 'lucide-react';

export type NavView =
  | 'overview'
  | 'quickstart'
  | 'installation'
  | 'how-compression-works'
  | 'playground'
  | 'output-verification'
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

interface NavItemConfig {
  id: NavView;
  label: string;
  icon: React.ElementType;
  iconColor?: string;
  badge?: React.ReactNode;
}

interface NavCategoryConfig {
  title: string;
  items: NavItemConfig[];
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

  const navCategories: NavCategoryConfig[] = [
    {
      title: 'Getting Started',
      items: [
        { id: 'overview', label: 'Overview & Stats', icon: LayoutDashboard, iconColor: 'text-emerald-400' },
        { id: 'quickstart', label: 'Quickstart', icon: Terminal, iconColor: 'text-emerald-400' },
        { id: 'installation', label: 'Installation', icon: Code, iconColor: 'text-neutral-400' },
      ],
    },
    {
      title: 'Compression Engine',
      items: [
        { id: 'how-compression-works', label: 'How Compression Works', icon: BookOpen, iconColor: 'text-emerald-400' },
        { id: 'playground', label: 'Interactive Playground ✨', icon: Play, iconColor: 'text-emerald-400' },
        { id: 'output-verification', label: 'Output Verification 🔍', icon: GitCompare, iconColor: 'text-emerald-400' },
      ],
    },
    {
      title: 'Reversible Compression',
      items: [
        {
          id: 'vault',
          label: 'Vault Inspector (CCR)',
          icon: Database,
          iconColor: 'text-emerald-400',
          badge: vaultCount > 0 ? (
            <span className="px-1.5 py-0.2 text-[9px] font-mono rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold">
              {vaultCount}
            </span>
          ) : undefined,
        },
      ],
    },
    {
      title: 'Observability',
      items: [
        { id: 'analytics', label: 'Token Savings Hub', icon: TrendingUp, iconColor: 'text-emerald-400' },
        { id: 'benchmarks', label: '5-Task Benchmarks', icon: BarChart3, iconColor: 'text-neutral-400' },
      ],
    },
    {
      title: 'Architecture & Proxy',
      items: [
        { id: 'proxy-server', label: 'Proxy Server', icon: Server, iconColor: 'text-emerald-400' },
        { id: 'architecture', label: 'Architecture', icon: Layers, iconColor: 'text-neutral-400' },
      ],
    },
    {
      title: 'Configuration',
      items: [
        { id: 'settings', label: 'Rule Settings & Sliders', icon: Sliders, iconColor: 'text-emerald-400' },
      ],
    },
    {
      title: 'Help',
      items: [
        { id: 'troubleshooting', label: 'Troubleshooting & FAQs', icon: HelpCircle, iconColor: 'text-neutral-400' },
      ],
    },
  ];

  const q = searchQuery.trim().toLowerCase();

  const filteredCategories = navCategories
    .map((cat) => ({
      ...cat,
      items: cat.items.filter(
        (item) =>
          item.label.toLowerCase().includes(q) ||
          cat.title.toLowerCase().includes(q) ||
          item.id.toLowerCase().includes(q)
      ),
    }))
    .filter((cat) => cat.items.length > 0);

  return (
    <aside className="w-68 md:w-72 bg-[#080808] border-r border-[#1a1a1a] flex flex-col justify-between h-screen sticky top-0 shrink-0 select-none">
      <div className="p-4 space-y-5 overflow-y-auto scrollbar-thin scrollbar-thumb-neutral-800">
        {/* Header Logo */}
        <div
          onClick={() => navigateTo('overview')}
          className="flex items-center space-x-3 px-2 pt-1 cursor-pointer group"
        >
          <PromptLensLogo className="w-8 h-6 object-contain" />
          <div className="flex items-center space-x-2">
            <span className="font-extrabold text-lg tracking-tight text-white">PromptLens</span>
            <span className="px-1.5 py-0.5 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded">
              v0.1
            </span>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative px-1 pt-1">
          <Search className="w-4 h-4 text-neutral-500 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search docs or vault..."
            className="w-full bg-[#121212] text-sm text-neutral-200 placeholder-neutral-500 border border-[#222222] rounded-xl pl-9 pr-8 py-2 focus:outline-none focus:border-emerald-500/50 transition font-sans"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-2.5 text-neutral-500 hover:text-white transition"
              title="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Headroom Sidebar Categories */}
        <div className="space-y-5 pt-1 text-sm">
          {filteredCategories.length > 0 ? (
            filteredCategories.map((category) => (
              <div key={category.title} className="space-y-1">
                <div className="px-3 text-[11px] font-bold text-neutral-400 uppercase tracking-wider flex items-center justify-between">
                  <span>{category.title}</span>
                </div>
                {category.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = currentView === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => navigateTo(item.id)}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition ${
                        isActive
                          ? 'bg-neutral-850 text-white font-bold border border-neutral-750'
                          : 'text-neutral-300 hover:text-white hover:bg-neutral-900/70'
                      }`}
                    >
                      <div className="flex items-center space-x-2.5">
                        <Icon className={`w-4 h-4 ${item.iconColor || 'text-neutral-400'}`} />
                        <span className="text-sm">{item.label}</span>
                      </div>
                      {item.badge}
                    </button>
                  );
                })}
              </div>
            ))
          ) : (
            <div className="px-3 py-6 text-center space-y-2">
              <p className="text-sm text-neutral-500">No navigation items found for</p>
              <p className="text-sm font-mono text-emerald-400 truncate">&quot;{searchQuery}&quot;</p>
              <button
                onClick={() => setSearchQuery('')}
                className="mt-2 text-xs text-neutral-400 hover:text-white underline"
              >
                Clear search
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Footer info */}
      <div className="p-4 border-t border-[#1a1a1a] bg-[#050505]">
        <div className="flex items-center justify-between text-sm text-neutral-300">
          <span className="flex items-center gap-2 font-medium">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Proxy Active
          </span>
          <span className="font-mono text-xs text-neutral-500">:8000</span>
        </div>
      </div>
    </aside>
  );
};
