import React, { useState } from 'react';
import { Play, Copy, Check } from 'lucide-react';
import { CompressionResult } from '../types';

export const Playground: React.FC = () => {
  const [inputContent, setInputContent] = useState<string>(
    'Traceback (most recent call last):\n' +
    '  File "app.py", line 42, in <module>\n' +
    '    user = db.query(User).filter(User.id == user_id).first()\n' +
    '  File "db.py", line 120, in query\n' +
    '    connection = self.pool.get_connection()\n' +
    Array.from({ length: 30 }, (_, i) => `  File "worker_${i}.py", line ${i * 5}, in process_task`).join('\n') + '\n' +
    'ConnectionError: Could not connect to PostgreSQL server at 127.0.0.1:5432'
  );
  const [result, setResult] = useState<CompressionResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const handleCompress = async () => {
    setLoading(true);
    try {
      const resp = await fetch('http://localhost:8000/api/compress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: inputContent })
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

  return (
    <div className="headroom-card p-6 space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Interactive Prompt Compression Playground ✨</h2>
        <p className="text-xs text-[#888888] mt-1">
          Paste any raw JSON, stack trace, or build log below to preview PromptLens token reduction live in your browser!
        </p>
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
            <div className="flex items-center justify-between p-3 rounded-xl bg-[#0c0c0c] border border-[#1f1f1f] text-xs">
              <div>
                Original: <span className="font-mono text-white font-bold">{result.original_tokens}</span> tokens | Compressed: <span className="font-mono text-white font-bold">{result.compressed_tokens}</span> tokens
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
