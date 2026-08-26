import React from 'react';
import { NavView } from './Sidebar';
import { Terminal, Zap, Server, Code, ArrowRight, Bot, Globe, Box, SlidersHorizontal, Database, ArrowDown, BarChart3, HelpCircle } from 'lucide-react';

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
            <h3 className="text-base font-bold text-emerald-400">Stage 1: Deterministic Engine</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Fast, zero-AI cleaning. Deduplicates repetitive build logs, trims compiler warnings, strips binary noise, and compresses JSON arrays and git diffs.
            </p>
          </div>

          <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-3">
            <h3 className="text-base font-bold text-emerald-400">Stage 2: Structural AST Skeletons</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Parses source code into class hierarchies, method signatures, and route endpoints (Python & JS/TS). Replaces large function bodies with valid skeletons to retain syntax and save 70–80% tokens.
            </p>
          </div>

          <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-3">
            <h3 className="text-base font-bold text-emerald-400">Stage 3: Semantic Relevance Embeddings</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Generates subword embeddings in &lt;1ms on CPU and calculates cosine similarity between the user prompt instruction and candidate functions to filter out irrelevant files.
            </p>
          </div>

          <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-3">
            <h3 className="text-base font-bold text-emerald-400">Stage 4: AST Dependency Graph Expansion</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Builds static call-graphs and import-graphs. If editing <code className="text-emerald-300">login()</code>, it automatically pulls in connected dependencies like <code className="text-emerald-300">validateUser()</code> and <code className="text-emerald-300">UserModel</code>.
            </p>
          </div>

          <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-6 space-y-3 md:col-span-2">
            <h3 className="text-base font-bold text-emerald-400">Stage 5: Knapsack Token Budget Allocator</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Formulated as mathematical knapsack optimization: <code className="text-emerald-400">max Σ(Relevance_i × Action_i)</code> subject to token budget <code className="text-emerald-400">Σ(Tokens_i) ≤ Budget_B</code>. Produces Tri-State decisions: <strong>PRESERVE</strong> (full code), <strong>SUMMARIZE</strong> (AST skeletons), or <strong>OMIT</strong> (stored in SHA-256 Vault).
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (view === 'architecture') {
    return (
      <div className="space-y-6 animate-fadeIn">
        {/* Header Section matching slide design */}
        <div>
          <span className="text-[11px] font-mono font-bold tracking-widest text-emerald-400 uppercase">
            ARCHITECTURE
          </span>
          <h1 className="text-3xl font-black tracking-tight text-white mt-1">
            Full System Architecture — Every Piece Explained
          </h1>
        </div>

        {/* Canvas Diagram Container */}
        <div className="bg-neutral-950/90 border border-neutral-850 rounded-3xl p-6 lg:p-8 shadow-2xl relative overflow-hidden backdrop-blur-2xl">
          <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

          {/* Main Top Horizontal Diagram Grid (Left Inputs -> Center Proxy -> Right Upstream LLM) */}
          <div className="flex flex-col xl:flex-row items-center justify-between gap-4 relative z-10">
            
            {/* LEFT COLUMN: Input Clients */}
            <div className="w-full xl:w-64 shrink-0 space-y-3.5">
              {/* Card 1: AI coding agent */}
              <div className="bg-neutral-900/80 border border-neutral-800 rounded-2xl p-4 shadow-lg relative group hover:border-emerald-500/40 transition-all duration-300">
                <div className="flex items-start space-x-3">
                  <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
                    <Bot className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white tracking-tight">AI coding agent</h3>
                    <p className="text-[11px] text-neutral-400 mt-0.5 leading-snug">Claude Code, Cursor, custom scripts</p>
                  </div>
                </div>
              </div>

              {/* Card 2: Browser extension */}
              <div className="bg-neutral-900/80 border border-neutral-800 rounded-2xl p-4 shadow-lg relative group hover:border-emerald-500/40 transition-all duration-300">
                <div className="flex items-start space-x-3">
                  <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
                    <Globe className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white tracking-tight">Browser extension</h3>
                    <p className="text-[11px] text-neutral-400 mt-0.5 leading-snug">ChatGPT, Claude.ai, Gemini, DeepSeek</p>
                  </div>
                </div>
              </div>
            </div>

            {/* CONNECTOR LEFT TO CENTER */}
            <div className="hidden xl:flex items-center justify-center text-emerald-400/80 shrink-0 px-1">
              <ArrowRight className="w-6 h-6 animate-pulse" />
            </div>
            <div className="flex xl:hidden items-center justify-center text-emerald-400/80 my-1">
              <ArrowDown className="w-5 h-5 animate-pulse" />
            </div>

            {/* CENTER COLUMN: PromptLens Proxy Container (Outer Box) */}
            <div className="w-full xl:flex-1 bg-neutral-950/90 border-2 border-emerald-500/30 rounded-3xl p-5 lg:p-6 shadow-2xl shadow-emerald-500/5 relative">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-lg lg:text-xl font-black text-emerald-400 tracking-tight flex items-center gap-2">
                    PromptLens Proxy
                  </h2>
                  <p className="text-[11px] font-mono text-neutral-400 mt-0.5">FastAPI · localhost:8000</p>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                  Core Proxy Engine
                </span>
              </div>

              {/* 3x2 Inner Sub-components Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                {/* 1. Task Classifier & Intent */}
                <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-3.5 hover:border-emerald-500/40 transition-all duration-300 shadow-md">
                  <div className="p-1.5 w-fit rounded-lg bg-emerald-500/10 text-emerald-400 mb-2 border border-emerald-500/20">
                    <Bot className="w-4 h-4" />
                  </div>
                  <h4 className="text-xs font-bold text-white">1. Task Classifier & Intent</h4>
                  <p className="text-[11px] text-neutral-400 mt-1 leading-relaxed">7 Coding Intents: Debugging, Refactoring, Gen, Mod, Review, Tests, Docs</p>
                </div>

                {/* 2. Structural AST Parser */}
                <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-3.5 hover:border-emerald-500/40 transition-all duration-300 shadow-md">
                  <div className="p-1.5 w-fit rounded-lg bg-emerald-500/10 text-emerald-400 mb-2 border border-emerald-500/20">
                    <Code className="w-4 h-4" />
                  </div>
                  <h4 className="text-xs font-bold text-white">2. Structural AST Parser</h4>
                  <p className="text-[11px] text-neutral-400 mt-1 leading-relaxed">Extracts class, method, function skeletons for Python, JS/TS, Go, Java</p>
                </div>

                {/* 3. Semantic Relevance Scorer */}
                <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-3.5 hover:border-emerald-500/40 transition-all duration-300 shadow-md">
                  <div className="p-1.5 w-fit rounded-lg bg-emerald-500/10 text-emerald-400 mb-2 border border-emerald-500/20">
                    <Zap className="w-4 h-4" />
                  </div>
                  <h4 className="text-xs font-bold text-white">3. Semantic Embedder</h4>
                  <p className="text-[11px] text-neutral-400 mt-1 leading-relaxed">Subword cosine vectors matching symbols directly to user prompt intent</p>
                </div>

                {/* 4. Dependency Call Graph */}
                <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-3.5 hover:border-emerald-500/40 transition-all duration-300 shadow-md">
                  <div className="p-1.5 w-fit rounded-lg bg-emerald-500/10 text-emerald-400 mb-2 border border-emerald-500/20">
                    <Box className="w-4 h-4" />
                  </div>
                  <h4 className="text-xs font-bold text-white">4. Dependency Call Graph</h4>
                  <p className="text-[11px] text-neutral-400 mt-1 leading-relaxed">1-hop & 2-hop neighborhood expansion connecting callers to helper models</p>
                </div>

                {/* 5. Knapsack Budget Allocator */}
                <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-3.5 hover:border-emerald-500/40 transition-all duration-300 shadow-md">
                  <div className="p-1.5 w-fit rounded-lg bg-emerald-500/10 text-emerald-400 mb-2 border border-emerald-500/20">
                    <SlidersHorizontal className="w-4 h-4" />
                  </div>
                  <h4 className="text-xs font-bold text-white">5. Knapsack Budget Allocator</h4>
                  <p className="text-[11px] text-neutral-400 mt-1 leading-relaxed">Tri-State action decider: PRESERVE full code, SUMMARIZE skeletons, OMIT</p>
                </div>

                {/* 6. Reversible Vault & Tool Injector */}
                <div className="bg-neutral-900/90 border border-neutral-800 rounded-2xl p-3.5 hover:border-emerald-500/40 transition-all duration-300 shadow-md">
                  <div className="p-1.5 w-fit rounded-lg bg-emerald-500/10 text-emerald-400 mb-2 border border-emerald-500/20">
                    <Database className="w-4 h-4" />
                  </div>
                  <h4 className="text-xs font-bold text-white">6. Reversible Vault & Tool</h4>
                  <p className="text-[11px] text-neutral-400 mt-1 leading-relaxed">SHA-256 prompt storage with retrieve_original() on-demand tool recovery</p>
                </div>
              </div>
            </div>

            {/* CONNECTOR CENTER TO RIGHT */}
            <div className="hidden xl:flex items-center justify-center text-emerald-400/80 shrink-0 px-1">
              <ArrowRight className="w-6 h-6 animate-pulse" />
            </div>
            <div className="flex xl:hidden items-center justify-center text-emerald-400/80 my-1">
              <ArrowDown className="w-5 h-5 animate-pulse" />
            </div>

            {/* RIGHT COLUMN: Upstream LLM Server */}
            <div className="w-full xl:w-64 shrink-0">
              <div className="bg-neutral-900/80 border border-neutral-800 rounded-2xl p-4 shadow-lg relative group hover:border-emerald-500/40 transition-all duration-300">
                <div className="flex items-start space-x-3">
                  <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
                    <Server className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white tracking-tight">LLM API server</h3>
                    <p className="text-[11px] text-neutral-400 mt-0.5 leading-snug">
                      Anthropic Claude, or any OpenAI-compatible model (Ollama, Groq, etc.)
                    </p>
                  </div>
                </div>
              </div>
            </div>

          </div>

          {/* BOTTOM SECTION CONNECTOR + WEB DASHBOARD */}
          <div className="flex flex-col items-center mt-8 space-y-2 relative z-10">
            {/* Arrow & Badge */}
            <div className="flex flex-col items-center text-emerald-400">
              <span className="text-[11px] font-mono text-emerald-300 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/30 mb-1">
                reads live stats via /api/stats
              </span>
              <ArrowDown className="w-5 h-5 animate-bounce text-emerald-400" />
            </div>

            {/* Web Dashboard Card */}
            <div className="w-full max-w-md bg-neutral-900/80 border border-neutral-800 rounded-2xl p-5 shadow-xl hover:border-emerald-500/40 transition-all duration-300">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <BarChart3 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white tracking-tight">Web dashboard</h3>
                  <p className="text-xs text-neutral-400 mt-0.5 font-mono">localhost:3000 — live stats & vault inspector</p>
                </div>
              </div>
            </div>
          </div>

          {/* Footer Text */}
          <div className="mt-8 pt-4 border-t border-neutral-900 flex justify-between items-center text-[11px] font-mono text-neutral-500 relative z-10">
            <span>PromptLens — AI Agent Context Optimization Proxy</span>
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
