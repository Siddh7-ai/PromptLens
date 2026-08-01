import React from 'react';
import { NavView } from './Sidebar';
import { Terminal, Layers, Zap, Server, Code, ArrowRight, HelpCircle } from 'lucide-react';

interface DocsViewProps {
  view: NavView;
  onNavigate?: (view: NavView) => void;
}

export const DocsView: React.FC<DocsViewProps> = ({ view }) => {
  if (view === 'quickstart') {
    return (
      <div className="space-y-6 animate-fadeIn">
        <div>
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/30">
            Getting Started
          </span>
          <h1 className="text-3xl font-bold tracking-tight text-white mt-2 flex items-center gap-2">
            <Terminal className="w-7 h-7 text-emerald-400" />
            Quickstart Guide
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            Get PromptLens running locally in under 2 minutes and route your AI coding agents.
          </p>
        </div>

        {/* Step 1 */}
        <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-3 shadow-xl">
          <div className="flex items-center gap-3">
            <span className="w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs font-mono">
              01
            </span>
            <h2 className="text-base font-bold text-white">Start the Python Proxy Backend</h2>
          </div>
          <p className="text-xs text-neutral-400">Launch the FastAPI proxy server on port 8000 using uvicorn or the shortcut:</p>
          <div className="bg-neutral-950 p-4 rounded-xl border border-neutral-850 font-mono text-xs text-emerald-300">
            .\server <span className="text-neutral-500"># Or: uvicorn src.proxy.server:app --port 8000 --reload</span>
          </div>
        </div>

        {/* Step 2 */}
        <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-3 shadow-xl">
          <div className="flex items-center gap-3">
            <span className="w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs font-mono">
              02
            </span>
            <h2 className="text-base font-bold text-white">Connect Your AI Agent</h2>
          </div>
          <p className="text-xs text-neutral-400">Set the base URL environment variable in your terminal before launching Claude Code or Cursor:</p>
          <div className="bg-neutral-950 p-4 rounded-xl border border-neutral-850 font-mono text-xs text-emerald-300">
            $env:ANTHROPIC_BASE_URL="http://localhost:8000/v1"<br />
            claude
          </div>
        </div>

        {/* Step 3 */}
        <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-3 shadow-xl">
          <div className="flex items-center gap-3">
            <span className="w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs font-mono">
              03
            </span>
            <h2 className="text-base font-bold text-white">Evaluate Token Savings</h2>
          </div>
          <p className="text-xs text-neutral-400">Run the pre-configured 5-task real-world benchmark evaluation suite:</p>
          <div className="bg-neutral-950 p-4 rounded-xl border border-neutral-850 font-mono text-xs text-emerald-300">
            .\benchmark <span className="text-neutral-500"># Or: python scripts/benchmark_tasks.py</span>
          </div>
        </div>
      </div>
    );
  }

  if (view === 'installation') {
    return (
      <div className="space-y-6 animate-fadeIn">
        <div>
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/30">
            Installation
          </span>
          <h1 className="text-3xl font-bold tracking-tight text-white mt-2 flex items-center gap-2">
            <Code className="w-7 h-7 text-emerald-400" />
            Installation & Requirements
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            System requirements and dependency installation instructions.
          </p>
        </div>

        <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-4 shadow-xl">
          <h2 className="text-base font-bold text-white">Python Dependencies</h2>
          <div className="bg-neutral-950 p-4 rounded-xl border border-neutral-850 font-mono text-xs text-neutral-300 space-y-1">
            <p><span className="text-emerald-400">fastapi</span>==0.110.0</p>
            <p><span className="text-emerald-400">uvicorn</span>==0.28.0</p>
            <p><span className="text-emerald-400">httpx</span>==0.27.0</p>
            <p><span className="text-emerald-400">tiktoken</span>==0.6.0</p>
            <p><span className="text-emerald-400">pytest</span>==8.1.1</p>
          </div>
        </div>

        <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-4 shadow-xl">
          <h2 className="text-base font-bold text-white">Dashboard Dependencies (Node 18+)</h2>
          <div className="bg-neutral-950 p-4 rounded-xl border border-neutral-850 font-mono text-xs text-neutral-300 space-y-1">
            <p>cd dashboard</p>
            <p>npm install</p>
            <p>npm run dev</p>
          </div>
        </div>
      </div>
    );
  }

  if (view === 'how-compression-works') {
    return (
      <div className="space-y-6 animate-fadeIn">
        <div>
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/30">
            Compression Engine
          </span>
          <h1 className="text-3xl font-bold tracking-tight text-white mt-2 flex items-center gap-2">
            <Zap className="w-7 h-7 text-emerald-400" />
            How Compression Works
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            Rule-based structural compression algorithms designed specifically for LLM tool outputs.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-3">
            <h3 className="text-base font-bold text-emerald-400">1. JSON Array Skimming</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">
              When REST API calls return thousands of JSON array elements, PromptLens preserves the head, tail, key statistics, and boundary samples while truncating redundant middle array records.
            </p>
          </div>

          <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-3">
            <h3 className="text-base font-bold text-emerald-400">2. Stack Trace & Log Trimming</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Build logs and pytest failure outputs keep failure headers, error lines, and final exception call sites while dropping thousands of lines of passing log noise.
            </p>
          </div>

          <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-3">
            <h3 className="text-base font-bold text-emerald-400">3. Git Diff Compression</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Preserves modified diff hunks and file path headers while stripping out unchanged surrounding code context lines.
            </p>
          </div>

          <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-3">
            <h3 className="text-base font-bold text-emerald-400">4. Transparent Reversible Vault</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Original raw payloads are stored under SHA-256 hash IDs. PromptLens injects <code className="text-emerald-400">retrieve_original(id)</code> into LLM tools so models can recover full data on demand.
            </p>
          </div>

          <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-3 md:col-span-2">
            <h3 className="text-base font-bold text-emerald-400">5. Agent Discipline (System Ruleset Nudges)</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Injects lightweight prompt rulesets (<code className="text-emerald-400">rules/lite.md</code>, <code className="text-emerald-400">rules/full.md</code>, <code className="text-emerald-400">rules/ultra.md</code>) into the Anthropic system prompt to encourage the AI model to generate concise code, skip restating plans, and cut output tokens by ~20% to ~50%.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (view === 'architecture') {
    return (
      <div className="space-y-6 animate-fadeIn">
        <div>
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/30">
            System Architecture
          </span>
          <h1 className="text-3xl font-bold tracking-tight text-white mt-2 flex items-center gap-2">
            <Layers className="w-7 h-7 text-emerald-400" />
            System Architecture
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            High-level component flow between AI coding agents, PromptLens Proxy, and LLM APIs.
          </p>
        </div>

        <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-6 shadow-xl">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 font-mono text-xs text-center">
            <div className="p-4 rounded-xl bg-neutral-950 border border-neutral-800 text-white w-full">
              🤖 AI Coding Agent<br /><span className="text-[10px] text-neutral-500">(Claude / Cursor)</span>
            </div>
            <ArrowRight className="w-5 h-5 text-emerald-400 shrink-0 rotate-90 md:rotate-0" />
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/40 text-emerald-300 w-full shadow-lg shadow-emerald-500/10">
              ⚡ PromptLens Proxy<br /><span className="text-[10px] text-emerald-400">(FastAPI :8000)</span>
            </div>
            <ArrowRight className="w-5 h-5 text-emerald-400 shrink-0 rotate-90 md:rotate-0" />
            <div className="p-4 rounded-xl bg-neutral-950 border border-neutral-800 text-white w-full">
              🧠 LLM API<br /><span className="text-[10px] text-neutral-500">(Anthropic API)</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (view === 'proxy-server') {
    return (
      <div className="space-y-6 animate-fadeIn">
        <div>
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/30">
            Proxy Server
          </span>
          <h1 className="text-3xl font-bold tracking-tight text-white mt-2 flex items-center gap-2">
            <Server className="w-7 h-7 text-emerald-400" />
            Proxy Server Specification
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            API routes and passthrough configuration endpoints.
          </p>
        </div>

        <div className="space-y-4">
          <div className="bg-neutral-900/90 border border-neutral-800 rounded-xl p-4 flex items-center justify-between">
            <div className="space-y-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                POST /v1/messages
              </span>
              <p className="text-xs text-neutral-300">Anthropic API proxy endpoint. Compresses tool outputs and injects retrieval tools.</p>
            </div>
          </div>

          <div className="bg-neutral-900/90 border border-neutral-800 rounded-xl p-4 flex items-center justify-between">
            <div className="space-y-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
                GET /api/stats
              </span>
              <p className="text-xs text-neutral-300">Returns live metrics summary, USD financial savings, and recent request logs.</p>
            </div>
          </div>

          <div className="bg-neutral-900/90 border border-neutral-800 rounded-xl p-4 flex items-center justify-between">
            <div className="space-y-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-500/20 text-purple-400 border border-purple-500/30">
                GET /api/vault
              </span>
              <p className="text-xs text-neutral-300">Returns list of uncompressed raw payloads stored in the reversible vault.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (view === 'troubleshooting') {
    return (
      <div className="space-y-6 animate-fadeIn">
        <div>
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/30">
            Help & Support
          </span>
          <h1 className="text-3xl font-bold tracking-tight text-white mt-2 flex items-center gap-2">
            <HelpCircle className="w-7 h-7 text-emerald-400" />
            Troubleshooting & FAQs
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            Common questions and solutions.
          </p>
        </div>

        <div className="space-y-4">
          <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-5 space-y-2">
            <h3 className="text-base font-bold text-white">Q: How do I verify my agent is routing through PromptLens?</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Check that <code className="text-emerald-400">ANTHROPIC_BASE_URL="http://localhost:8000/v1"</code> is set. When your agent calls tools, you will see request entries appear instantly on the live dashboard.
            </p>
          </div>

          <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-5 space-y-2">
            <h3 className="text-base font-bold text-white">Q: Can the LLM still access uncompressed data if needed?</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Yes! PromptLens automatically injects the <code className="text-emerald-400">retrieve_original(id)</code> tool into prompt definitions. If an LLM needs exact line numbers or raw data, it calls this tool to fetch 100% exact raw content from the vault.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return null;
};
