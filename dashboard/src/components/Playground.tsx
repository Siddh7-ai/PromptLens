import React, { useState, useEffect } from 'react';
import { Play, Copy, Check, RotateCcw, FileText, Database, GitBranch } from 'lucide-react';
import { CompressionResult } from '../types';

const DEFAULT_PYTEST_PROMPT =
  'Traceback (most recent call last):\n' +
  '  File "app.py", line 42, in <module>\n' +
  '    user = db.query(User).filter(User.id == user_id).first()\n' +
  '  File "db.py", line 120, in query\n' +
  '    connection = self.pool.get_connection()\n' +
  Array.from({ length: 25 }, (_, i) => `  File "worker_${i}.py", line ${i * 5}, in process_task`).join('\n') + '\n' +
  'ConnectionError: Could not connect to PostgreSQL server at 127.0.0.1:5432';

const SAMPLE_PRESETS: Record<string, string> = {
  pytest: DEFAULT_PYTEST_PROMPT,
  json: JSON.stringify(
    Array.from({ length: 15 }, (_, i) => ({
      id: i + 1,
      user: `user_${i + 1}`,
      role: i % 2 === 0 ? 'admin' : 'member',
      status: 'active',
      created_at: '2026-01-01T00:00:00Z',
    })),
    null,
    2
  ),
  gitdiff:
    'diff --git a/src/proxy/server.py b/src/proxy/server.py\n' +
    'index 8a3f1b..9c4d2e 100644\n' +
    '--- a/src/proxy/server.py\n' +
    '+++ b/src/proxy/server.py\n' +
    '@@ -120,6 +120,8 @@ def process_anthropic_payload(payload):\n' +
    '     # Unchanged context line 1\n' +
    '     # Unchanged context line 2\n' +
    '+    baseline_tokens = get_token_count(json.dumps(payload))\n' +
    '+    processed_payload = compress_tool_results(payload)\n' +
    '     # Unchanged context line 3\n' +
    '     # Unchanged context line 4',
};

export const Playground: React.FC = () => {
  // Restore custom prompt & results from localStorage across page switches
  const [inputContent, setInputContent] = useState<string>(() => {
    return localStorage.getItem('promptlens_pg_input') || DEFAULT_PYTEST_PROMPT;
  });

  const [result, setResult] = useState<CompressionResult | null>(() => {
    const saved = localStorage.getItem('promptlens_pg_result');
    return saved ? JSON.parse(saved) : null;
  });

  const [loading, setLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  // Sync state to localStorage whenever changed
  useEffect(() => {
    localStorage.setItem('promptlens_pg_input', inputContent);
  }, [inputContent]);

  useEffect(() => {
    if (result) {
      localStorage.setItem('promptlens_pg_result', JSON.stringify(result));
    } else {
      localStorage.removeItem('promptlens_pg_result');
    }
  }, [result]);

  const handleCompress = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/compress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: inputContent }),
      });
      if (resp.ok) {
        const data: CompressionResult = await resp.json();
        setResult(data);
      }
    } catch (err) {
      console.error('Playground compression error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (result) {
      navigator.clipboard.writeText(result.compressed_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleResetToDefault = () => {
    setInputContent(DEFAULT_PYTEST_PROMPT);
    setResult(null);
    localStorage.removeItem('promptlens_pg_input');
    localStorage.removeItem('promptlens_pg_result');
  };

  const handleLoadPreset = (key: string) => {
    if (SAMPLE_PRESETS[key]) {
      setInputContent(SAMPLE_PRESETS[key]);
      setResult(null);
    }
  };

  return (
    <div className="headroom-card p-6 space-y-6">
      {/* Header with Sample Presets & Reset Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1c1c1c] pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Interactive Prompt Compression Playground ✨</h2>
          <p className="text-xs text-[#888888] mt-1">
            Test prompt compression live in your browser. Your prompt is saved across page navigation.
          </p>
        </div>
        <button
          onClick={handleResetToDefault}
          className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#141414] hover:bg-[#1f1f1f] text-[#cccccc] border border-[#2e2e2e] transition flex items-center space-x-1.5 self-start"
        >
          <RotateCcw className="w-3.5 h-3.5 text-[#888888]" />
          <span>Reset to Default Sample</span>
        </button>
      </div>

      {/* Preset Quick Load Buttons */}
      <div className="flex items-center space-x-2 text-xs">
        <span className="text-[#666666] font-semibold uppercase tracking-wider text-[10px]">Load Preset:</span>
        <button
          onClick={() => handleLoadPreset('pytest')}
          className="px-2.5 py-1 rounded-md bg-[#141414] hover:bg-[#1f1f1f] text-[#cccccc] border border-[#242424] transition flex items-center space-x-1.5"
        >
          <FileText className="w-3 h-3 text-emerald-400" />
          <span>Pytest Log</span>
        </button>
        <button
          onClick={() => handleLoadPreset('json')}
          className="px-2.5 py-1 rounded-md bg-[#141414] hover:bg-[#1f1f1f] text-[#cccccc] border border-[#242424] transition flex items-center space-x-1.5"
        >
          <Database className="w-3 h-3 text-blue-400" />
          <span>REST API JSON</span>
        </button>
        <button
          onClick={() => handleLoadPreset('gitdiff')}
          className="px-2.5 py-1 rounded-md bg-[#141414] hover:bg-[#1f1f1f] text-[#cccccc] border border-[#242424] transition flex items-center space-x-1.5"
        >
          <GitBranch className="w-3 h-3 text-purple-400" />
          <span>Git Diff</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Input Panel */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-[#888888] uppercase tracking-wider block">
            Raw Input Content (Text / JSON / Logs)
          </label>
          <textarea
            value={inputContent}
            onChange={(e) => setInputContent(e.target.value)}
            rows={14}
            className="w-full bg-[#050505] text-[#cccccc] border border-[#1f1f1f] rounded-xl p-3 text-xs font-mono focus:outline-none focus:border-[#444444] transition resize-none"
            placeholder="Paste raw log or JSON here..."
          />
          <button
            onClick={handleCompress}
            disabled={loading || !inputContent.trim()}
            className="w-full py-2.5 rounded-xl text-xs font-semibold bg-white hover:bg-[#e0e0e0] disabled:opacity-50 text-black transition flex items-center justify-center space-x-2"
          >
            <Play className="w-3.5 h-3.5 fill-black" />
            <span>{loading ? 'Compressing...' : 'Compress with PromptLens'}</span>
          </button>
        </div>

        {/* Output Panel */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-[#888888] uppercase tracking-wider block">
              Compressed Output Payload
            </label>
            {result && (
              <button
                onClick={handleCopy}
                className="text-xs text-[#aaaaaa] hover:text-white flex items-center space-x-1"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied!' : 'Copy Result'}</span>
              </button>
            )}
          </div>
          <div className="relative">
            <textarea
              value={result ? result.compressed_text : 'Click "Compress with PromptLens" to view result...'}
              readOnly
              rows={14}
              className="w-full bg-[#050505] text-[#aaaaaa] border border-[#1f1f1f] rounded-xl p-3 text-xs font-mono focus:outline-none resize-none"
            />
          </div>

          {result && (
            <div className="flex items-center justify-between p-3 rounded-xl bg-[#0c0c0c] border border-[#1f1f1f] text-xs animate-fadeIn">
              <div>
                Original: <span className="font-mono text-white font-bold">{result.original_tokens}</span> tokens | Compressed:{' '}
                <span className="font-mono text-white font-bold">{result.compressed_tokens}</span> tokens
              </div>
              <span className="font-bold text-white bg-[#1c1c1c] px-2.5 py-0.5 rounded border border-[#2e2e2e]">
                {result.savings_pct.toFixed(1)}% Saved
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
