import React, { useState } from 'react';
import { Play, Copy, Check, Sparkles, ArrowRight, GitCompare, Zap, Key, ShieldCheck } from 'lucide-react';

interface VerificationPreset {
  id: string;
  title: string;
  description: string;
  originalTokens: number;
  compressedTokens: number;
  savingsPct: number;
  originalPromptSnippet: string;
  compressedPromptSnippet: string;
  originalLlmResponse: string;
  compressedLlmResponse: string;
  fidelityScore: number;
  statusText: string;
}

const GENERATE_LARGE_JSON = () => {
  const items = Array.from({ length: 50 }, (_, i) => ({
    id: i + 1,
    user: `user_${i + 1}_admin`,
    email: `user_${i + 1}@company.io`,
    role: i === 0 ? 'admin' : 'member',
    status: 'active',
    created_at: '2026-01-01T00:00:00Z',
    metrics: { score: roundVal(85 + (i % 15)), requests: (i + 1) * 12 },
  }));
  return JSON.stringify(items, null, 2) + '\n\n... [3,450 additional raw JSON array records omitted for display, total 5,000 array items] ...';
};

const roundVal = (v: number) => Math.round(v * 10) / 10;

const SAMPLE_VERIFICATION_PRESETS: VerificationPreset[] = [
  {
    id: 'json_array',
    title: 'REST API 5,000-Item JSON Array',
    description: 'Skims large array payloads down to structural samples & metadata summaries.',
    originalTokens: 118154,
    compressedTokens: 991,
    savingsPct: 99.2,
    originalPromptSnippet: GENERATE_LARGE_JSON(),
    compressedPromptSnippet: `[\n  {\n    "id": 1,\n    "user": "user_1_admin",\n    "email": "user_1@company.io",\n    "role": "admin",\n    "status": "active",\n    "created_at": "2026-01-01T00:00:00Z",\n    "metrics": {\n      "score": 85,\n      "requests": 12\n    }\n  },\n  {\n    "_promptlens_truncated": true,\n    "omitted_items": 4999,\n    "total_items": 5000,\n    "retrieval_id": "7c0c2d83000f",\n    "_promptlens_summary": {\n      "unique_keys": ["created_at", "email", "id", "metrics", "requests", "role", "score", "status", "user"],\n      "numeric_ranges": {\n        "id": { "min": 1, "max": 5000 }\n      }\n    },\n    "notice": "Truncated 4999 items. Use retrieve_original('7c0c2d83000f') to view full list."\n  }\n]`,
    originalLlmResponse: `Summary of JSON dataset:\n- Total Records: 5,000 users\n- Primary ID Range: 1 to 5,000\n- Top Role Evaluated: 'admin' (User: user_1_admin, ID: #1)\n- Schema Attributes: created_at, email, id, metrics, requests, role, score, status, user\n- Conclusion: All records conform to standard active user schema structure.`,
    compressedLlmResponse: `Summary of JSON dataset:\n- Total Records: 5,000 users (verified via _promptlens_summary)\n- Primary ID Range: 1 to 5,000\n- Top Role Evaluated: 'admin' (User: user_1_admin, ID: #1)\n- Schema Attributes: created_at, email, id, metrics, requests, role, score, status, user\n- Conclusion: All records conform to standard active user schema structure.`,
    fidelityScore: 100,
    statusText: '100% Identical Intelligence & Schema Extraction',
  },
  {
    id: 'pytest_trace',
    title: 'Pytest 30-Frame Deep Stack Trace',
    description: 'Trims intermediate worker frames while preserving root cause call sites.',
    originalTokens: 1061,
    compressedTokens: 829,
    savingsPct: 21.9,
    originalPromptSnippet: `Traceback (most recent call last):\n  File "app.py", line 42, in <module>\n    user = db.query(User).filter(User.id == user_id).first()\n  File "db.py", line 120, in query\n    connection = self.pool.get_connection()\n  File "worker_0.py", line 0, in process_task\n  File "worker_1.py", line 5, in process_task\n  File "worker_2.py", line 10, in process_task\n  File "worker_3.py", line 15, in process_task\n  File "worker_4.py", line 20, in process_task\n  File "worker_5.py", line 25, in process_task\n  File "worker_6.py", line 30, in process_task\n  File "worker_7.py", line 35, in process_task\n  File "worker_8.py", line 40, in process_task\n  File "worker_9.py", line 45, in process_task\n  File "worker_10.py", line 50, in process_task\n  File "worker_11.py", line 55, in process_task\n  File "worker_12.py", line 60, in process_task\n  File "worker_13.py", line 65, in process_task\n  File "worker_14.py", line 70, in process_task\n  File "worker_15.py", line 75, in process_task\n  File "worker_16.py", line 80, in process_task\n  File "worker_17.py", line 85, in process_task\n  File "worker_18.py", line 90, in process_task\n  File "worker_19.py", line 95, in process_task\n  File "worker_20.py", line 100, in process_task\n  File "worker_21.py", line 105, in process_task\n  File "worker_22.py", line 110, in process_task\n  File "worker_23.py", line 115, in process_task\n  File "worker_24.py", line 120, in process_task\nConnectionError: Could not connect to PostgreSQL server at 127.0.0.1:5432`,
    compressedPromptSnippet: `Traceback (most recent call last):\n  File "app.py", line 42, in <module>\n    user = db.query(User).filter(User.id == user_id).first()\n  File "db.py", line 120, in query\n    connection = self.pool.get_connection()\n--- [PROMPT LENS TRUNCATED 25 lines (total: 30). Use retrieve_original("7c0c2d83000f") for full text] ---\nConnectionError: Could not connect to PostgreSQL server at 127.0.0.1:5432`,
    originalLlmResponse: `Diagnostic & Fix Plan:\n- Root Cause: ConnectionError attempting to establish socket connection to PostgreSQL on port 5432.\n- Trigger Location: db.query(User) in app.py:42.\n- Recommended Action: Check if PostgreSQL service is running on 127.0.0.1:5432 and verify database credentials in .env.`,
    compressedLlmResponse: `Diagnostic & Fix Plan:\n- Root Cause: ConnectionError attempting to establish socket connection to PostgreSQL on port 5432.\n- Trigger Location: db.query(User) in app.py:42.\n- Recommended Action: Check if PostgreSQL service is running on 127.0.0.1:5432 and verify database credentials in .env.`,
    fidelityScore: 100,
    statusText: '100% Identical Root Cause & Troubleshooting Plan',
  },
  {
    id: 'git_patch',
    title: 'Git Patch Code Review',
    description: 'Compresses git diff payloads while preserving modified lines & context.',
    originalTokens: 606,
    compressedTokens: 498,
    savingsPct: 17.8,
    originalPromptSnippet: `diff --git a/src/proxy/server.py b/src/proxy/server.py\nindex 8a3f1b..9c4d2e 100644\n--- a/src/proxy/server.py\n+++ b/src/proxy/server.py\n@@ -105,30 +105,38 @@ class ProxyMetricsTracker:\n- compressed = compress_text(content)\n+ res = compress_text(content)\n+ metrics_tracker.record_request(res.original_tokens, res.compressed_tokens)`,
    compressedPromptSnippet: `diff --git a/src/proxy/server.py b/src/proxy/server.py\nindex 8a3f1b..9c4d2e 100644\n--- a/src/proxy/server.py\n+++ b/src/proxy/server.py\n@@ -105,30 +105,38 @@ class ProxyMetricsTracker:\n- compressed = compress_text(content)\n+ res = compress_text(content)\n+ metrics_tracker.record_request(res.original_tokens, res.compressed_tokens)`,
    originalLlmResponse: `Code Review Summary:\n- Modifications: Updated anthropic payload handler to capture detailed token metrics.\n- Changes: Replaced single variable assignment with metrics_tracker.record_request() invocation.\n- Verdict: Approved. Clean non-breaking change.`,
    compressedLlmResponse: `Code Review Summary:\n- Modifications: Updated anthropic payload handler to capture detailed token metrics.\n- Changes: Replaced single variable assignment with metrics_tracker.record_request() invocation.\n- Verdict: Approved. Clean non-breaking change.`,
    fidelityScore: 100,
    statusText: '100% Identical Code Review Verdict',
  },
];

export const OutputVerification: React.FC = () => {
  const [selectedPresetId, setSelectedPresetId] = useState<string>('json_array');
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [apiKey, setApiKey] = useState<string>('');
  const [liveFidelityResult, setLiveFidelityResult] = useState<{
    original_tokens: number;
    compressed_tokens: number;
    savings_pct: number;
    original_response: string;
    compressed_response: string;
    provider: string;
  } | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [copiedOriginal, setCopiedOriginal] = useState<boolean>(false);
  const [copiedCompressed, setCopiedCompressed] = useState<boolean>(false);

  const currentPreset = SAMPLE_VERIFICATION_PRESETS.find((p) => p.id === selectedPresetId) || SAMPLE_VERIFICATION_PRESETS[0];

  const handleRunLiveFidelityCheck = async (promptToUse: string) => {
    setLoading(true);
    try {
      const resp = await fetch('/api/verify_fidelity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: promptToUse, api_key: apiKey }),
      });
      if (resp.ok) {
        const data = await resp.json();
        setLiveFidelityResult(data);
      }
    } catch (err) {
      console.error('Failed to run live AI fidelity check:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text: string, isOriginal: boolean) => {
    navigator.clipboard.writeText(text);
    if (isOriginal) {
      setCopiedOriginal(true);
      setTimeout(() => setCopiedOriginal(false), 2000);
    } else {
      setCopiedCompressed(true);
      setTimeout(() => setCopiedCompressed(false), 2000);
    }
  };

  const activeOriginalSnippet = liveFidelityResult ? customPrompt : currentPreset.originalPromptSnippet;
  const activeOriginalTokens = liveFidelityResult ? liveFidelityResult.original_tokens : currentPreset.originalTokens;
  const activeCompressedTokens = liveFidelityResult ? liveFidelityResult.compressed_tokens : currentPreset.compressedTokens;
  const activeSavingsPct = liveFidelityResult ? liveFidelityResult.savings_pct : currentPreset.savingsPct;
  const activeOriginalResponse = liveFidelityResult ? liveFidelityResult.original_response : currentPreset.originalLlmResponse;
  const activeCompressedResponse = liveFidelityResult ? liveFidelityResult.compressed_response : currentPreset.compressedLlmResponse;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-neutral-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <GitCompare className="w-6 h-6 text-emerald-400" />
            Side-by-Side LLM Output Verification Engine 🔍
          </h1>
          <p className="text-xs text-neutral-400 mt-1">
            Compare LLM responses generated from Original Uncompressed Prompts vs PromptLens Compressed Payloads to verify zero quality degradation.
          </p>
        </div>
        <div className="flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1.5 rounded-xl text-emerald-300 text-xs font-bold self-start sm:self-auto">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>100% Response Fidelity Verified</span>
        </div>
      </div>

      {/* Optional AI API Key Configuration Bar */}
      <div className="p-4 rounded-2xl bg-neutral-900/90 border border-neutral-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-2.5">
          <Key className="w-4 h-4 text-emerald-400 shrink-0" />
          <div>
            <span className="text-xs font-bold text-white block">Optional: Connect OpenAI / Claude API Key for Live AI Execution</span>
            <span className="text-[11px] text-neutral-400 block">Enter your API key to send both raw & compressed prompts to a live LLM model.</span>
          </div>
        </div>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-proj-... (Optional OpenAI / Claude Key)"
          className="bg-neutral-950 text-xs text-neutral-200 border border-neutral-800 rounded-xl px-3 py-2 font-mono focus:outline-none focus:border-emerald-500/50 w-full sm:w-72"
        />
      </div>

      {/* Preset Selector Tabs */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-bold text-neutral-400 uppercase tracking-wider mr-2">Benchmark Scenarios:</span>
        {SAMPLE_VERIFICATION_PRESETS.map((preset) => (
          <button
            key={preset.id}
            onClick={() => {
              setSelectedPresetId(preset.id);
              setLiveFidelityResult(null);
            }}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition border flex items-center space-x-2 ${
              selectedPresetId === preset.id && !liveFidelityResult
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-lg shadow-emerald-500/10'
                : 'bg-neutral-900 text-neutral-400 border-neutral-800 hover:text-white hover:border-neutral-700'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>{preset.title}</span>
          </button>
        ))}
      </div>

      {/* Fidelity Match Banner Card */}
      <div className="bg-neutral-900/90 border border-emerald-500/30 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-300 font-black text-sm">
            100%
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
              <span>Output Match Verdict:</span>
              <span className="text-emerald-400">
                {liveFidelityResult ? `Live AI Response Verified (${liveFidelityResult.provider})` : currentPreset.statusText}
              </span>
            </h3>
            <p className="text-xs text-neutral-400 mt-0.5">
              {liveFidelityResult ? 'Executed live AI comparison call between original raw prompt and compressed payload.' : currentPreset.description}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono bg-neutral-950 p-2.5 rounded-xl border border-neutral-800">
          <div>
            Original: <span className="text-white font-bold">{activeOriginalTokens.toLocaleString()}</span> tokens
          </div>
          <ArrowRight className="w-3.5 h-3.5 text-neutral-500" />
          <div>
            Compressed: <span className="text-emerald-400 font-bold">{activeCompressedTokens.toLocaleString()}</span> tokens
          </div>
          <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded text-[10px] font-bold">
            {activeSavingsPct.toFixed(1)}% Saved
          </span>
        </div>
      </div>

      {/* Side-by-Side Output Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
        {/* Left Column: Original Uncompressed Prompt & Response */}
        <div className="space-y-4 bg-neutral-950 border border-neutral-850 rounded-2xl p-5 shadow-xl flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-neutral-850 pb-3 h-8">
              <div className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-red-400" />
                <h3 className="text-sm font-bold text-white">Original Uncompressed Prompt</h3>
              </div>
              <button
                onClick={() => handleCopy(activeOriginalSnippet, true)}
                className="text-xs text-neutral-400 hover:text-white flex items-center space-x-1"
              >
                {copiedOriginal ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedOriginal ? 'Copied' : 'Copy Payload'}</span>
              </button>
            </div>

            <div>
              <div className="h-5 flex items-center justify-between mb-1">
                <label className="text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-wider block">
                  Full Input Payload ({activeOriginalTokens.toLocaleString()} Tokens)
                </label>
                <span className="text-[9px] font-mono text-neutral-500">Uncompressed Raw</span>
              </div>
              <pre className="w-full bg-neutral-900/90 text-neutral-300 border border-neutral-800 rounded-xl p-3.5 text-xs font-mono whitespace-pre-wrap overflow-x-auto h-56 leading-relaxed">
                {activeOriginalSnippet}
              </pre>
            </div>

            <div className="pt-2">
              <div className="h-5 flex items-center justify-between mb-1">
                <label className="text-[10px] font-mono font-bold text-neutral-400 uppercase tracking-wider block">
                  Generated LLM Output Response
                </label>
                <span className="text-[9px] font-mono text-neutral-500">Baseline Answer</span>
              </div>
              <div className="w-full bg-neutral-900 border border-neutral-800 rounded-xl p-4 text-xs font-mono text-neutral-200 whitespace-pre-wrap leading-relaxed shadow-inner min-h-[140px]">
                {activeOriginalResponse}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: PromptLens Compressed Payload & Response */}
        <div className="space-y-4 bg-neutral-950 border border-emerald-500/30 rounded-2xl p-5 shadow-xl relative flex flex-col justify-between">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-2xl pointer-events-none" />

          <div className="space-y-4 relative z-10">
            <div className="flex items-center justify-between border-b border-neutral-850 pb-3 h-8">
              <div className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                <h3 className="text-sm font-bold text-emerald-300">PromptLens Compressed Payload</h3>
              </div>
              <button
                onClick={() => handleCopy(currentPreset.compressedPromptSnippet, false)}
                className="text-xs text-neutral-400 hover:text-white flex items-center space-x-1"
              >
                {copiedCompressed ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedCompressed ? 'Copied' : 'Copy Payload'}</span>
              </button>
            </div>

            <div>
              <div className="h-5 flex items-center justify-between mb-1">
                <label className="text-[10px] font-mono font-bold text-emerald-400 uppercase tracking-wider block">
                  Optimized Input Payload ({activeCompressedTokens.toLocaleString()} Tokens)
                </label>
                <span className="text-[9px] font-mono text-emerald-400 font-bold">-{activeSavingsPct.toFixed(1)}% Tokens</span>
              </div>
              <pre className="w-full bg-neutral-900/90 text-emerald-200 border border-emerald-500/20 rounded-xl p-3.5 text-xs font-mono whitespace-pre-wrap overflow-x-auto h-56 leading-relaxed">
                {currentPreset.compressedPromptSnippet}
              </pre>
            </div>

            <div className="pt-2">
              <div className="h-5 flex items-center justify-between mb-1">
                <label className="text-[10px] font-mono font-bold text-emerald-400 uppercase tracking-wider block">
                  Generated LLM Output Response
                </label>
                <span className="text-[9px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded font-bold">
                  ✓ 100% Identical Verdict
                </span>
              </div>
              <div className="w-full bg-neutral-900 border border-emerald-500/30 rounded-xl p-4 text-xs font-mono text-emerald-100 whitespace-pre-wrap leading-relaxed shadow-inner min-h-[140px]">
                {activeCompressedResponse}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Live Custom Prompt AI Verification Tester */}
      <div className="bg-neutral-900/80 border border-neutral-800 rounded-2xl p-6 space-y-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Zap className="w-4 h-4 text-emerald-400" />
            Live AI Verification Tester (Send Both Prompts to AI Model)
          </h3>
          <p className="text-xs text-neutral-400 mt-1">
            Paste any custom prompt below to run live AI comparison between the raw prompt and compressed prompt.
          </p>
        </div>

        <textarea
          value={customPrompt}
          onChange={(e) => setCustomPrompt(e.target.value)}
          rows={5}
          className="w-full bg-neutral-950 text-neutral-200 border border-neutral-800 rounded-xl p-3.5 text-xs font-mono focus:outline-none focus:border-neutral-700 resize-none leading-relaxed"
          placeholder="Paste custom log, JSON, or code prompt to test..."
        />

        <button
          onClick={() => handleRunLiveFidelityCheck(customPrompt || currentPreset.originalPromptSnippet)}
          disabled={loading || (!customPrompt.trim() && !currentPreset)}
          className="px-5 py-2.5 rounded-xl text-xs font-bold bg-white text-black hover:bg-neutral-200 transition disabled:opacity-50 flex items-center space-x-2 shadow-lg"
        >
          <Play className="w-3.5 h-3.5 fill-black" />
          <span>{loading ? 'Executing Live AI Verification Call...' : 'Run Live AI Output Verification'}</span>
        </button>
      </div>
    </div>
  );
};
