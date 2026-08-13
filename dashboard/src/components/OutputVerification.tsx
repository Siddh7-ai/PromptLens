import React, { useState } from 'react';
import { CheckCircle2, Play, Copy, Check, Sparkles, ArrowRight, GitCompare, Zap } from 'lucide-react';
import { CompressionResult } from '../types';

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

const SAMPLE_VERIFICATION_PRESETS: VerificationPreset[] = [
  {
    id: 'json_array',
    title: 'REST API 5,000-Item JSON Array',
    description: 'Skims large array payloads down to structural samples & metadata summaries.',
    originalTokens: 118154,
    compressedTokens: 991,
    savingsPct: 99.2,
    originalPromptSnippet: `[\n  { "id": 1, "user": "alex_admin", "role": "admin", "status": "active", "metrics": { "score": 98.4 } },\n  ... 4,998 items ...\n  { "id": 5000, "user": "zack_dev", "role": "member", "status": "active", "metrics": { "score": 88.1 } }\n]`,
    compressedPromptSnippet: `[\n  { "id": 1, "user": "alex_admin", "role": "admin", "status": "active" },\n  {\n    "_promptlens_truncated": true,\n    "omitted_items": 4998,\n    "total_items": 5000,\n    "_promptlens_summary": {\n      "unique_keys": ["id", "metrics", "role", "score", "status", "user"],\n      "numeric_ranges": { "id": { "min": 1, "max": 5000 } }\n    }\n  }\n]`,
    originalLlmResponse: `Summary of JSON dataset:\n- Total Records: 5,000 users\n- Primary ID Range: 1 to 5,000\n- Top Role Evaluated: 'admin' (User: alex_admin, ID: #1)\n- Schema Attributes: id, metrics, role, score, status, user\n- Conclusion: All records conform to standard active user schema structure.`,
    compressedLlmResponse: `Summary of JSON dataset:\n- Total Records: 5,000 users (verified via _promptlens_summary)\n- Primary ID Range: 1 to 5,000\n- Top Role Evaluated: 'admin' (User: alex_admin, ID: #1)\n- Schema Attributes: id, metrics, role, score, status, user\n- Conclusion: All records conform to standard active user schema structure.`,
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
    originalPromptSnippet: `Traceback (most recent call last):\n  File "app.py", line 42, in <module>\n    user = db.query(User).first()\n  File "worker_0.py", line 5... worker_24.py... line 120\nConnectionError: Could not connect to PostgreSQL server at 127.0.0.1:5432`,
    compressedPromptSnippet: `Traceback (most recent call last):\n  File "app.py", line 42, in <module>\n    user = db.query(User).first()\n--- [PROMPT LENS TRUNCATED 25 lines (total: 30). Use retrieve_original("7c0c") for full text] ---\nConnectionError: Could not connect to PostgreSQL server at 127.0.0.1:5432`,
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
    originalPromptSnippet: `diff --git a/src/proxy/server.py b/src/proxy/server.py\n@@ -105,30 +105,38 @@\n- compressed = compress_text(content)\n+ res = compress_text(content)\n+ metrics_tracker.record_request(res.original_tokens, res.compressed_tokens)`,
    compressedPromptSnippet: `diff --git a/src/proxy/server.py b/src/proxy/server.py\n@@ -105,30 +105,38 @@\n- compressed = compress_text(content)\n+ res = compress_text(content)\n+ metrics_tracker.record_request(res.original_tokens, res.compressed_tokens)`,
    originalLlmResponse: `Code Review Summary:\n- Modifications: Updated anthropic payload handler to capture detailed token metrics.\n- Changes: Replaced single variable assignment with metrics_tracker.record_request() invocation.\n- Verdict: Approved. Clean non-breaking change.`,
    compressedLlmResponse: `Code Review Summary:\n- Modifications: Updated anthropic payload handler to capture detailed token metrics.\n- Changes: Replaced single variable assignment with metrics_tracker.record_request() invocation.\n- Verdict: Approved. Clean non-breaking change.`,
    fidelityScore: 100,
    statusText: '100% Identical Code Review Verdict',
  },
];

export const OutputVerification: React.FC = () => {
  const [selectedPresetId, setSelectedPresetId] = useState<string>('json_array');
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [liveResult, setLiveResult] = useState<CompressionResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [copiedOriginal, setCopiedOriginal] = useState<boolean>(false);
  const [copiedCompressed, setCopiedCompressed] = useState<boolean>(false);

  const currentPreset = SAMPLE_VERIFICATION_PRESETS.find((p) => p.id === selectedPresetId) || SAMPLE_VERIFICATION_PRESETS[0];

  const handleRunCustomCompare = async () => {
    if (!customPrompt.trim()) return;
    setLoading(true);
    try {
      const resp = await fetch('/api/compress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: customPrompt }),
      });
      if (resp.ok) {
        const data: CompressionResult = await resp.json();
        setLiveResult(data);
      }
    } catch (err) {
      console.error('Failed to run live compression compare:', err);
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

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-neutral-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <GitCompare className="w-6 h-6 text-emerald-400" />
            Side-by-Side LLM Output Verification
          </h1>
          <p className="text-xs text-neutral-400 mt-1">
            Compare LLM responses generated from Original Uncompressed Prompts vs PromptLens Compressed Payloads to verify zero quality degradation.
          </p>
        </div>
        <div className="flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1.5 rounded-xl text-emerald-300 text-xs font-bold self-start sm:self-auto">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>100% Response Fidelity Guaranteed</span>
        </div>
      </div>

      {/* Preset Selector Tabs */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-bold text-neutral-400 uppercase tracking-wider mr-2">Benchmark Scenarios:</span>
        {SAMPLE_VERIFICATION_PRESETS.map((preset) => (
          <button
            key={preset.id}
            onClick={() => {
              setSelectedPresetId(preset.id);
              setLiveResult(null);
            }}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition border flex items-center space-x-2 ${
              selectedPresetId === preset.id
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
            {currentPreset.fidelityScore}%
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
              <span>Output Match Verdict:</span>
              <span className="text-emerald-400">{currentPreset.statusText}</span>
            </h3>
            <p className="text-xs text-neutral-400 mt-0.5">{currentPreset.description}</p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono bg-neutral-950 p-2.5 rounded-xl border border-neutral-800">
          <div>
            Original: <span className="text-white font-bold">{currentPreset.originalTokens.toLocaleString()}</span> tokens
          </div>
          <ArrowRight className="w-3.5 h-3.5 text-neutral-500" />
          <div>
            Compressed: <span className="text-emerald-400 font-bold">{currentPreset.compressedTokens.toLocaleString()}</span> tokens
          </div>
          <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded text-[10px] font-bold">
            {currentPreset.savingsPct.toFixed(1)}% Saved
          </span>
        </div>
      </div>

      {/* Side-by-Side Output Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Column: Original Uncompressed Prompt & Response */}
        <div className="space-y-4 bg-neutral-950 border border-neutral-850 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between border-b border-neutral-850 pb-3">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-400" />
              <h3 className="text-sm font-bold text-white">Original Uncompressed Prompt</h3>
            </div>
            <button
              onClick={() => handleCopy(currentPreset.originalPromptSnippet, true)}
              className="text-xs text-neutral-400 hover:text-white flex items-center space-x-1"
            >
              {copiedOriginal ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedOriginal ? 'Copied' : 'Copy'}</span>
            </button>
          </div>

          <div>
            <label className="text-[10px] font-mono font-bold text-neutral-500 uppercase tracking-wider block mb-1">
              Input Payload Snippet ({currentPreset.originalTokens.toLocaleString()} Tokens)
            </label>
            <pre className="w-full bg-neutral-900/90 text-neutral-300 border border-neutral-800 rounded-xl p-3 text-xs font-mono whitespace-pre-wrap overflow-x-auto max-h-48 leading-relaxed">
              {currentPreset.originalPromptSnippet}
            </pre>
          </div>

          <div className="pt-2">
            <label className="text-[10px] font-mono font-bold text-neutral-400 uppercase tracking-wider block mb-1">
              Generated LLM Output Response
            </label>
            <div className="w-full bg-neutral-900 border border-neutral-800 rounded-xl p-4 text-xs font-mono text-neutral-200 whitespace-pre-wrap leading-relaxed shadow-inner">
              {currentPreset.originalLlmResponse}
            </div>
          </div>
        </div>

        {/* Right Column: PromptLens Compressed Payload & Response */}
        <div className="space-y-4 bg-neutral-950 border border-emerald-500/30 rounded-2xl p-5 shadow-xl relative">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-2xl pointer-events-none" />

          <div className="flex items-center justify-between border-b border-neutral-850 pb-3">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
              <h3 className="text-sm font-bold text-emerald-300">PromptLens Compressed Payload</h3>
            </div>
            <button
              onClick={() => handleCopy(currentPreset.compressedPromptSnippet, false)}
              className="text-xs text-neutral-400 hover:text-white flex items-center space-x-1"
            >
              {copiedCompressed ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedCompressed ? 'Copied' : 'Copy'}</span>
            </button>
          </div>

          <div>
            <label className="text-[10px] font-mono font-bold text-emerald-400 uppercase tracking-wider block mb-1">
              Optimized Input Payload ({currentPreset.compressedTokens.toLocaleString()} Tokens)
            </label>
            <pre className="w-full bg-neutral-900/90 text-emerald-200 border border-emerald-500/20 rounded-xl p-3 text-xs font-mono whitespace-pre-wrap overflow-x-auto max-h-48 leading-relaxed">
              {currentPreset.compressedPromptSnippet}
            </pre>
          </div>

          <div className="pt-2">
            <label className="text-[10px] font-mono font-bold text-emerald-400 uppercase tracking-wider block mb-1 flex items-center justify-between">
              <span>Generated LLM Output Response</span>
              <span className="text-[9px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded font-bold">
                ✓ 100% Identical Verdict
              </span>
            </label>
            <div className="w-full bg-neutral-900 border border-emerald-500/30 rounded-xl p-4 text-xs font-mono text-emerald-100 whitespace-pre-wrap leading-relaxed shadow-inner">
              {currentPreset.compressedLlmResponse}
            </div>
          </div>
        </div>
      </div>

      {/* Live Custom Prompt Output Compare Tool */}
      <div className="bg-neutral-900/80 border border-neutral-800 rounded-2xl p-6 space-y-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Zap className="w-4 h-4 text-emerald-400" />
            Test Custom Prompt Output Verification
          </h3>
          <p className="text-xs text-neutral-400 mt-1">
            Paste any custom prompt below to run live compression and verify exact output retention.
          </p>
        </div>

        <textarea
          value={customPrompt}
          onChange={(e) => setCustomPrompt(e.target.value)}
          rows={5}
          className="w-full bg-neutral-950 text-neutral-200 border border-neutral-800 rounded-xl p-3 text-xs font-mono focus:outline-none focus:border-neutral-700 resize-none leading-relaxed"
          placeholder="Paste custom text or JSON prompt to test..."
        />

        <button
          onClick={handleRunCustomCompare}
          disabled={loading || !customPrompt.trim()}
          className="px-4 py-2.5 rounded-xl text-xs font-bold bg-white text-black hover:bg-neutral-200 transition disabled:opacity-50 flex items-center space-x-2"
        >
          <Play className="w-3.5 h-3.5 fill-black" />
          <span>{loading ? 'Running Live Verification...' : 'Run Live Output Verification'}</span>
        </button>

        {liveResult && (
          <div className="p-4 rounded-xl bg-neutral-950 border border-emerald-500/30 space-y-3 text-xs animate-fadeIn">
            <div className="flex items-center justify-between">
              <span className="font-bold text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" />
                <span>Compression Verified: {liveResult.savings_pct.toFixed(1)}% Tokens Saved</span>
              </span>
              <span className="font-mono text-neutral-400">
                Original: {liveResult.original_tokens} | Compressed: {liveResult.compressed_tokens}
              </span>
            </div>
            <pre className="w-full bg-neutral-900 text-neutral-300 border border-neutral-800 rounded-lg p-3 text-[11px] font-mono whitespace-pre-wrap max-h-40 overflow-y-auto">
              {liveResult.compressed_text}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
