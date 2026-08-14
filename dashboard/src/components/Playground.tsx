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

const DEFAULT_GITDIFF_PROMPT =
  'diff --git a/src/proxy/server.py b/src/proxy/server.py\n' +
  'index 8a3f1b..9c4d2e 100644\n' +
  '--- a/src/proxy/server.py\n' +
  '+++ b/src/proxy/server.py\n' +
  '@@ -105,30 +105,38 @@ class ProxyMetricsTracker:\n' +
  '     def record_request(self, original_tokens: int, compressed_tokens: int):\n' +
  '         self.total_requests += 1\n' +
  '         self.total_original_tokens += original_tokens\n' +
  '         self.total_compressed_tokens += compressed_tokens\n' +
  '         self.tokens_saved = self.total_original_tokens - self.total_compressed_tokens\n' +
  '\n' +
  '     def get_summary(self) -> dict:\n' +
  '         savings_percent = 0.0\n' +
  '         if self.total_original_tokens > 0:\n' +
  '             savings_percent = (self.tokens_saved / self.total_original_tokens) * 100.0\n' +
  '         return {\n' +
  '             \'total_requests\': self.total_requests,\n' +
  '             \'total_original\': self.total_original_tokens,\n' +
  '             \'total_compressed\': self.total_compressed_tokens,\n' +
  '             \'saved\': self.tokens_saved,\n' +
  '             \'savings_percent\': round(savings_percent, 2)\n' +
  '         }\n' +
  '\n' +
  '@@ -150,25 +158,35 @@ async def process_anthropic_payload(payload: dict) -> dict:\n' +
  '     if not isinstance(payload, dict):\n' +
  '         return payload\n' +
  '     \n' +
  '     messages = payload.get(\'messages\', [])\n' +
  '     for msg in messages:\n' +
  '         if msg.get(\'role\') == \'user\':\n' +
  '             content = msg.get(\'content\')\n' +
  '             if isinstance(content, str):\n' +
  '-                compressed = compress_text(content)\n' +
  '-                msg[\'content\'] = compressed.compressed_str\n' +
  '+                res = compress_text(content)\n' +
  '+                msg[\'content\'] = res.compressed_str\n' +
  '+                metrics_tracker.record_request(res.original_tokens, res.compressed_tokens)\n' +
  '             elif isinstance(content, list):\n' +
  '                 for block in content:\n' +
  '                     if block.get(\'type\') == \'text\' and \'text\' in block:\n' +
  '-                        compressed = compress_text(block[\'text\'])\n' +
  '-                        block[\'text\'] = compressed.compressed_str\n' +
  '+                        res = compress_text(block[\'text\'])\n' +
  '+                        block[\'text\'] = res.compressed_str\n' +
  '+                        metrics_tracker.record_request(res.original_tokens, res.compressed_tokens)\n' +
  '     return payload\n' +
  '\n' +
  'diff --git a/src/compress/text_compressor.py b/src/compress/text_compressor.py\n' +
  'index f21e8d..e49a1c 100644\n' +
  '--- a/src/compress/text_compressor.py\n' +
  '+++ b/src/compress/text_compressor.py\n' +
  '@@ -45,25 +45,35 @@ def compress_text(text: str, head_lines: int = 10, tail_lines: int = 10) -> Text:\n' +
  '     if original_tokens < min_token_threshold:\n' +
  '         return TextCompressionResult(\n' +
  '             compressed_str=text,\n' +
  '             retrieval_id=retrieval_id,\n' +
  '             original_tokens=original_tokens,\n' +
  '             compressed_tokens=original_tokens,\n' +
  '             is_compressed=False,\n' +
  '             compression_ratio=0.0\n' +
  '         )\n' +
  '\n' +
  '     lines = text.splitlines()\n' +
  '     if len(lines) <= (head_lines + tail_lines + 1):\n' +
  '         return TextCompressionResult(\n' +
  '             compressed_str=text,\n' +
  '             retrieval_id=retrieval_id,\n' +
  '             original_tokens=original_tokens,\n' +
  '             compressed_tokens=original_tokens,\n' +
  '             is_compressed=False,\n' +
  '             compression_ratio=0.0\n' +
  '         )\n' +
  '\n' +
  '     head = lines[:head_lines]\n' +
  '     tail = lines[-tail_lines:]\n' +
  '     omitted = len(lines) - (head_lines + tail_lines)\n' +
  '     marker = f\'--- [PROMPT LENS TRUNCATED {omitted} lines (total: {len(lines)}). Use retrieve_original("retrieval_id") for full text] ---\'\n' +
  '     compressed_str = \'\\n\'.join(head + [marker] + tail)\n' +
  '     compressed_tokens = get_token_count(compressed_str)\n' +
  '\n' +
  '     return TextCompressionResult(\n' +
  '         compressed_str=compressed_str,\n' +
  '         retrieval_id=retrieval_id,\n' +
  '         original_tokens=original_tokens,\n' +
  '         compressed_tokens=compressed_tokens,\n' +
  '         is_compressed=True,\n' +
  '         compression_ratio=round(1.0 - (compressed_tokens / original_tokens), 4)\n' +
  '     )';

const SAMPLE_PRESETS: Record<string, string> = {
  pytest: DEFAULT_PYTEST_PROMPT,
  json: JSON.stringify(
    Array.from({ length: 5000 }, (_, i) => ({
      id: i + 1,
      user: `user_${i + 1}_admin`,
      email: `user_${i + 1}@company.io`,
      role: i === 0 ? 'admin' : 'member',
      status: 'active',
      created_at: '2026-01-01T00:00:00Z',
      metrics: {
        score: 85 + (i % 15),
        requests: (i + 1) * 12,
      },
    })),
    null,
    2
  ),
  gitdiff: DEFAULT_GITDIFF_PROMPT,
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
  const [prettyPrint, setPrettyPrint] = useState<boolean>(true);

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

  const getFormattedOutput = (text: string): string => {
    if (!prettyPrint || !text) return text;
    try {
      const splitMarker = '\n\n[PromptLens:';
      if (text.includes(splitMarker)) {
        const parts = text.split(splitMarker);
        const jsonPart = parts[0].trim();
        const noticePart = splitMarker + parts.slice(1).join(splitMarker);
        const parsed = JSON.parse(jsonPart);
        return JSON.stringify(parsed, null, 2) + noticePart;
      }
      const parsed = JSON.parse(text);
      return JSON.stringify(parsed, null, 2);
    } catch (e) {
      return text;
    }
  };

  const formattedOutput = result ? getFormattedOutput(result.compressed_text) : '';

  const handleCopy = () => {
    if (result) {
      navigator.clipboard.writeText(formattedOutput);
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

  // Helper to extract omitted count from payload if present
  const getOmittedCount = (): number | null => {
    if (!result || !result.compressed_text) return null;
    try {
      const match = result.compressed_text.match(/"omitted_items":\s*(\d+)/);
      if (match) return parseInt(match[1], 10);
      const lineMatch = result.compressed_text.match(/TRUNCATED (\d+) lines/);
      if (lineMatch) return parseInt(lineMatch[1], 10);
    } catch (e) {
      return null;
    }
    return null;
  };

  const omittedCount = getOmittedCount();

  return (
    <div className="headroom-card p-6 space-y-6 animate-fadeIn">
      {/* Header with Sample Presets & Reset Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1c1c1c] pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Interactive Prompt Compression Playground ✨</h2>
          <p className="text-xs text-[#888888] mt-1">
            Test prompt compression live in your browser. Toggle between Pretty-Printed view and Minified payload.
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
            rows={15}
            className="w-full bg-[#050505] text-[#cccccc] border border-[#1f1f1f] rounded-xl p-3.5 text-xs font-mono focus:outline-none focus:border-[#444444] transition resize-none leading-relaxed"
            placeholder="Paste raw log or JSON here..."
          />
          <button
            onClick={handleCompress}
            disabled={loading || !inputContent.trim()}
            className="w-full py-2.5 rounded-xl text-xs font-bold bg-white hover:bg-[#e0e0e0] disabled:opacity-50 text-black transition flex items-center justify-center space-x-2 shadow-lg"
          >
            <Play className="w-3.5 h-3.5 fill-black" />
            <span>{loading ? 'Compressing Payload...' : 'Compress with PromptLens'}</span>
          </button>
        </div>

        {/* Output Panel */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <label className="text-xs font-semibold text-[#888888] uppercase tracking-wider block">
                Compressed Output Payload
              </label>
              {/* Pretty Print vs Raw Minified Mode Switcher */}
              <div className="inline-flex p-0.5 bg-[#141414] border border-[#242424] rounded-lg">
                <button
                  onClick={() => setPrettyPrint(true)}
                  className={`px-2 py-0.5 text-[10px] font-bold rounded transition ${
                    prettyPrint ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'text-[#888888] hover:text-white'
                  }`}
                  title="Format JSON with readable indentations"
                >
                  Pretty View
                </button>
                <button
                  onClick={() => setPrettyPrint(false)}
                  className={`px-2 py-0.5 text-[10px] font-bold rounded transition ${
                    !prettyPrint ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'text-[#888888] hover:text-white'
                  }`}
                  title="Raw minified single-line API format"
                >
                  Raw Minified
                </button>
              </div>
            </div>

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
              value={result ? formattedOutput : 'Click "Compress with PromptLens" to view result...'}
              readOnly
              rows={15}
              className="w-full bg-[#050505] text-[#cccccc] border border-[#1f1f1f] rounded-xl p-3.5 text-xs font-mono focus:outline-none resize-none leading-relaxed"
            />
          </div>

          {/* Results & Truncation Highlights Bar */}
          {result && (
            <div className="space-y-2 animate-fadeIn">
              <div className="flex flex-wrap items-center justify-between p-3 rounded-xl bg-[#0c0c0c] border border-[#1f1f1f] text-xs gap-2">
                <div>
                  Original: <span className="font-mono text-white font-bold">{result.original_tokens.toLocaleString()}</span> tokens | Compressed:{' '}
                  <span className="font-mono text-white font-bold">{result.compressed_tokens.toLocaleString()}</span> tokens
                </div>
                <span className="font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded border border-emerald-500/20">
                  {result.savings_pct.toFixed(1)}% Saved
                </span>
              </div>

              {/* Omitted Items Highlight Banner */}
              {omittedCount !== null && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs flex items-center justify-between text-emerald-300">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold">✂️ Truncation Active:</span>
                    <span>{omittedCount} records/lines omitted and stored in Vault</span>
                  </div>
                  {result.retrieval_id && (
                    <span className="font-mono text-[11px] bg-emerald-500/20 px-2 py-0.5 rounded border border-emerald-500/30 text-emerald-200">
                      ID: #{result.retrieval_id}
                    </span>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
