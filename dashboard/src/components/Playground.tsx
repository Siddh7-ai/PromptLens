import React, { useState, useEffect, useRef } from 'react';
import { Play, Copy, Check, RotateCcw, FileText, Database, Code, Bug, RefreshCw, ChevronDown } from 'lucide-react';
import { CompressionResult } from '../types';

const SAMPLE_PRESETS: Record<string, string> = {
  codemod: `Add JWT authentication to the login and user routes.

\`\`\`javascript
// filepath: routes/user.js
const express = require('express');
const router = express.Router();
const User = require('../models/user');

router.post('/login', async (req, res) => {
    const { email, password } = req.body;
    const user = await User.findOne({ email });
    if (!user || user.password !== password) {
        return res.status(401).json({ error: 'Invalid credentials' });
    }
    return res.json({ success: true, user });
});

router.get('/profile', async (req, res) => {
    const user = await User.findById(req.query.id);
    res.json(user);
});

module.exports = router;
\`\`\`

\`\`\`javascript
// filepath: models/user.js
const mongoose = require('mongoose');

const UserSchema = new mongoose.Schema({
    email: { type: String, required: true },
    password: { type: String, required: true },
    name: String,
    role: { type: String, default: 'user' }
});

module.exports = mongoose.model('User', UserSchema);
\`\`\`

\`\`\`javascript
// filepath: utils/analytics.js
// 150 lines of background analytics tracking
function trackPageView(page, user) {
    console.log('page view tracked', page, user);
}
function trackEvent(evt, data) {
    console.log('event', evt, data);
}
module.exports = { trackPageView, trackEvent };
\`\`\``,

  debugging: `Why am I getting this TypeError: Cannot read property 'map' of undefined in StudentList?

\`\`\`javascript
// filepath: components/StudentList.jsx
import React, { useEffect, useState } from 'react';
import { fetchStudents } from '../api/studentApi';

export function StudentList() {
    const [data, setData] = useState();

    useEffect(() => {
        fetchStudents().then(res => setData(res.data));
    }, []);

    return (
        <div className="student-list">
            <h2>Enrolled Students</h2>
            <ul>
                {data.items.map(s => (
                    <li key={s.id}>{s.name} - Grade: {s.grade}</li>
                ))}
            </ul>
        </div>
    );
}
\`\`\`

\`\`\`log
[ERROR] Uncaught TypeError: Cannot read properties of undefined (reading 'map')
    at StudentList (StudentList.jsx:14)
    at renderWithHooks (react-dom.development.js:14985)
    at mountIndeterminateComponent (react-dom.development.js:17811)
\`\`\``,

  refactor: `Refactor this student management class to follow Single Responsibility and Open-Closed principles.

\`\`\`python
# filepath: student_manager.py
class StudentManager:
    def __init__(self, db_conn):
        self.db = db_conn

    def register_student(self, name: str, email: str, major: str):
        if "@" not in email:
            raise ValueError("Invalid email format")
        
        query = f"INSERT INTO students (name, email, major) VALUES ('{name}', '{email}', '{major}')"
        self.db.execute(query)

        import smtplib
        server = smtplib.SMTP('smtp.school.edu')
        server.sendmail("admin@school.edu", email, f"Welcome {name}!")

        with open("daily_report.txt", "a") as f:
            f.write(f"Registered {name} ({major})\\n")
\`\`\``,

  pytest: `Traceback (most recent call last):
  File "app.py", line 42, in <module>
    user = db.query(User).filter(User.id == user_id).first()
  File "db.py", line 120, in query
    connection = self.pool.get_connection()
${Array.from({ length: 20 }, (_, i) => `  File "worker_${i}.py", line ${i * 5}, in process_task`).join('\n')}
ConnectionError: Could not connect to PostgreSQL server at 127.0.0.1:5432`,

  json: JSON.stringify(
    Array.from({ length: 50 }, (_, i) => ({
      id: i + 1,
      user: `user_${i + 1}_admin`,
      email: `user_${i + 1}@company.io`,
      role: i === 0 ? 'admin' : 'member',
      status: 'active',
      created_at: '2026-01-01T00:00:00Z',
    })),
    null,
    2
  ),
};

export const Playground: React.FC = () => {
  const [inputContent, setInputContent] = useState<string>(() => {
    try {
      const saved = localStorage.getItem('promptlens_pg_input');
      // Only restore if payload is under 35KB to ensure instant page load and zero UI freezing
      if (saved && saved.length <= 35000) {
        return saved;
      }
    } catch (e) {
      console.warn('Could not read saved playground input:', e);
    }
    return SAMPLE_PRESETS.codemod;
  });

  const [mode, setMode] = useState<string>('v5');
  const [budget, setBudget] = useState<number>(3000);
  const [isBudgetOpen, setIsBudgetOpen] = useState<boolean>(false);
  const [result, setResult] = useState<CompressionResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const budgetRef = useRef<HTMLDivElement>(null);

  const BUDGET_OPTIONS = [
    { value: 500, label: '500 Tokens (Ultra-Compact)' },
    { value: 1500, label: '1,500 Tokens (Compact)' },
    { value: 3000, label: '3,000 Tokens (Standard)' },
    { value: 8000, label: '8,000 Tokens (8k Context)' },
    { value: 32000, label: '32,000 Tokens (32k Context)' },
    { value: 128000, label: '128,000 Tokens (128k Context)' },
  ];

  // Safely persist to localStorage with debouncing & quota guards
  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        if (inputContent && inputContent.length <= 35000) {
          localStorage.setItem('promptlens_pg_input', inputContent);
        }
      } catch (e) {
        // Quota or access error, ignore safely
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [inputContent]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (budgetRef.current && !budgetRef.current.contains(e.target as Node)) {
        setIsBudgetOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleCompress = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/compress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: inputContent,
          mode: mode,
          budget: budget,
        }),
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
    if (!result) return;
    navigator.clipboard.writeText(result.compressed_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleResetToDefault = () => {
    setInputContent(SAMPLE_PRESETS.codemod);
    setResult(null);
  };

  const handleLoadPreset = (key: string) => {
    if (SAMPLE_PRESETS[key]) {
      setInputContent(SAMPLE_PRESETS[key]);
      setResult(null);
    }
  };

  const formatTaskCategory = (cat?: string) => {
    if (!cat) return 'General Coding';
    return cat.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  return (
    <div className="headroom-card p-6 space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1c1c1c] pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
            <span>Multi-Stage Coding Prompt Compressor</span>
            <span className="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-500/30">
              v2–v5 Pipeline
            </span>
          </h2>
          <p className="text-xs text-[#888888] mt-1">
            Task-Aware & Dependency-Aware AST Context Optimization with Knapsack Token Budgeting.
          </p>
        </div>
        <button
          onClick={handleResetToDefault}
          className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#141414] hover:bg-[#1f1f1f] text-[#cccccc] border border-[#2e2e2e] transition flex items-center space-x-1.5 self-start"
        >
          <RotateCcw className="w-3.5 h-3.5 text-[#888888]" />
          <span>Reset Sample</span>
        </button>
      </div>

      {/* Control Bar: Mode Selector & Budget */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl bg-[#0d0d0d] border border-[#1f1f1f]">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-semibold text-[#888888] uppercase tracking-wider">Compression Mode:</span>
          {[
            { id: 'v5', label: 'v5 Budget Knapsack', desc: 'Full Pipeline' },
            { id: 'v4', label: 'v4 Task+Dep Graph', desc: 'Call Graph Expansion' },
            { id: 'v3', label: 'v3 Semantic Match', desc: 'Vector / Embedding Similarity' },
            { id: 'v2', label: 'v2 AST Skeletons', desc: 'Structural Outlines' },
            { id: 'v1', label: 'v1 Rule-Based', desc: 'Log Truncation' },
          ].map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
                mode === m.id
                  ? 'bg-emerald-500 text-black font-bold shadow-md shadow-emerald-500/20'
                  : 'bg-[#181818] text-[#aaaaaa] hover:text-white border border-[#282828]'
              }`}
              title={m.desc}
            >
              {m.label}
            </button>
          ))}
        </div>

        {/* Custom Dark Theme Budget Dropdown */}
        <div className="relative flex items-center space-x-2 text-xs" ref={budgetRef}>
          <span className="text-[#888888] font-medium">Budget Limit:</span>
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsBudgetOpen(!isBudgetOpen)}
              className="bg-[#141414] hover:bg-[#1c1c1c] text-white border border-[#282828] hover:border-[#3a3a3a] rounded-lg px-3 py-1.5 text-xs flex items-center justify-between space-x-2 transition cursor-pointer font-medium min-w-[190px]"
            >
              <span>{BUDGET_OPTIONS.find((o) => o.value === budget)?.label || `${budget.toLocaleString()} Tokens`}</span>
              <ChevronDown className={`w-3.5 h-3.5 text-[#888888] transition-transform duration-200 ${isBudgetOpen ? 'rotate-180 text-emerald-400' : ''}`} />
            </button>

            {isBudgetOpen && (
              <div className="absolute right-0 mt-1.5 w-[210px] bg-[#121212] border border-[#262626] rounded-xl shadow-2xl z-50 py-1 overflow-hidden animate-fadeIn backdrop-blur-md">
                {BUDGET_OPTIONS.map((opt) => {
                  const isSelected = opt.value === budget;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => {
                        setBudget(opt.value);
                        setIsBudgetOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between transition cursor-pointer ${
                        isSelected
                          ? 'bg-emerald-500/15 text-emerald-300 font-semibold'
                          : 'text-[#cccccc] hover:bg-[#1c1c1c] hover:text-white'
                      }`}
                    >
                      <span>{opt.label}</span>
                      {isSelected && <Check className="w-3.5 h-3.5 text-emerald-400" />}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Preset Buttons */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="text-[#666666] font-semibold uppercase tracking-wider text-[10px]">Load Task Category:</span>
        <button
          onClick={() => handleLoadPreset('codemod')}
          className="px-2.5 py-1 rounded-md bg-[#141414] hover:bg-[#1f1f1f] text-[#cccccc] border border-[#242424] transition flex items-center space-x-1.5"
        >
          <Code className="w-3 h-3 text-cyan-400" />
          <span>Code Modification (Auth)</span>
        </button>
        <button
          onClick={() => handleLoadPreset('debugging')}
          className="px-2.5 py-1 rounded-md bg-[#141414] hover:bg-[#1f1f1f] text-[#cccccc] border border-[#242424] transition flex items-center space-x-1.5"
        >
          <Bug className="w-3 h-3 text-rose-400" />
          <span>Debugging (TypeError)</span>
        </button>
        <button
          onClick={() => handleLoadPreset('refactor')}
          className="px-2.5 py-1 rounded-md bg-[#141414] hover:bg-[#1f1f1f] text-[#cccccc] border border-[#242424] transition flex items-center space-x-1.5"
        >
          <RefreshCw className="w-3 h-3 text-amber-400" />
          <span>Refactoring (SOLID)</span>
        </button>
        <button
          onClick={() => handleLoadPreset('pytest')}
          className="px-2.5 py-1 rounded-md bg-[#141414] hover:bg-[#1f1f1f] text-[#cccccc] border border-[#242424] transition flex items-center space-x-1.5"
        >
          <FileText className="w-3 h-3 text-emerald-400" />
          <span>Pytest Trace</span>
        </button>
        <button
          onClick={() => handleLoadPreset('json')}
          className="px-2.5 py-1 rounded-md bg-[#141414] hover:bg-[#1f1f1f] text-[#cccccc] border border-[#242424] transition flex items-center space-x-1.5"
        >
          <Database className="w-3 h-3 text-blue-400" />
          <span>REST API JSON</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Input Panel */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-[#888888] uppercase tracking-wider block">
              Raw Coding Prompt & Code Context
            </label>
            <span className="text-[11px] font-mono text-[#666666]">
              {inputContent.length.toLocaleString()} chars
            </span>
          </div>
          <textarea
            value={inputContent}
            onChange={(e) => setInputContent(e.target.value)}
            rows={16}
            className="w-full bg-[#050505] text-[#cccccc] border border-[#1f1f1f] rounded-xl p-3.5 text-xs font-mono focus:outline-none focus:border-[#444444] transition resize-none leading-relaxed"
            placeholder="Paste prompt, code snippets, or logs here..."
          />
          <button
            onClick={handleCompress}
            disabled={loading || !inputContent.trim()}
            className="w-full py-2.5 rounded-xl text-xs font-bold bg-white hover:bg-[#e0e0e0] disabled:opacity-50 text-black transition flex items-center justify-center space-x-2 shadow-lg cursor-pointer h-[38px]"
          >
            <Play className="w-3.5 h-3.5 fill-black" />
            <span>{loading ? 'Optimizing Context Pipeline...' : 'Run Multi-Stage Compression'}</span>
          </button>
        </div>

        {/* Output Panel */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <label className="text-xs font-semibold text-[#888888] uppercase tracking-wider block">
                Compressed Context Payload
              </label>
              {result?.task_category && (
                <span className="text-[10px] font-bold bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded border border-purple-500/30">
                  🎯 {formatTaskCategory(result.task_category)}
                </span>
              )}
            </div>

            {result && (
              <button
                onClick={handleCopy}
                className="text-xs text-[#aaaaaa] hover:text-white flex items-center space-x-1 cursor-pointer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied!' : 'Copy Result'}</span>
              </button>
            )}
          </div>

          <div className="relative">
            <textarea
              value={result ? result.compressed_text : 'Click "Run Multi-Stage Compression" to view output...'}
              readOnly
              rows={16}
              className="w-full bg-[#050505] text-[#cccccc] border border-[#1f1f1f] rounded-xl p-3.5 text-xs font-mono focus:outline-none resize-none leading-relaxed"
            />
          </div>

          {/* Aligned Output Summary Bar matching left button height */}
          {result ? (
            <div className="flex items-center justify-between px-3 py-2 rounded-xl bg-[#0c0c0c] border border-[#1f1f1f] text-xs h-[38px]">
              <div>
                Original: <span className="font-mono text-white font-bold">{result.original_tokens.toLocaleString()}</span> tok | Compressed:{' '}
                <span className="font-mono text-white font-bold">{result.compressed_tokens.toLocaleString()}</span> tok
              </div>
              <span className="font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 text-[11px]">
                {result.savings_pct.toFixed(1)}% Saved
              </span>
            </div>
          ) : (
            <div className="flex items-center justify-center px-3 py-2 rounded-xl bg-[#080808] border border-[#1a1a1a] text-xs text-[#555555] h-[38px]">
              Summary will appear here after compression
            </div>
          )}
        </div>
      </div>

      {/* FULL WIDTH BOTTOM SECTION (Spans below BOTH Left and Right Panels) */}
      {result && (
        <div className="pt-4 border-t border-[#1a1a1a] space-y-3 animate-fadeIn">
          {/* Tri-State Retention Decisions Bar */}
          <div className="flex flex-wrap items-center justify-between p-3.5 rounded-xl bg-[#0d0d0d] border border-[#1f1f1f] text-xs gap-3">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-white uppercase tracking-wider">Retention Decisions:</span>
              <span className="text-[11px] text-[#777777]">(Smart AST Allocation)</span>
            </div>
            <div className="flex items-center space-x-2.5">
              <span className="bg-emerald-500/15 text-emerald-300 px-3 py-1 rounded-lg border border-emerald-500/25 font-mono text-xs font-semibold">
                Preserved: {result.preserved_count || 0}
              </span>
              <span className="bg-amber-500/15 text-amber-300 px-3 py-1 rounded-lg border border-amber-500/25 font-mono text-xs font-semibold">
                Summarized: {result.summarized_count || 0}
              </span>
              <span className="bg-rose-500/15 text-rose-300 px-3 py-1 rounded-lg border border-rose-500/25 font-mono text-xs font-semibold">
                Omitted: {result.omitted_count || 0}
              </span>
            </div>
          </div>

          {/* 5-Stage Token Reduction Pipeline in 5 columns */}
          {result.stage_metrics && result.stage_metrics.length > 0 && (
            <div className="p-4 rounded-xl bg-[#090909] border border-[#1c1c1c] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-[#888888] uppercase tracking-wider">
                  Multi-Stage Token Reduction Pipeline:
                </span>
                <span className="text-[11px] font-mono text-emerald-400 font-semibold">
                  Total Latency: {result.stage_metrics.reduce((acc, sm) => acc + sm.latency_ms, 0).toFixed(1)}ms
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
                {result.stage_metrics.map((sm, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-[#121212] border border-[#222222] text-center hover:border-emerald-500/30 transition">
                    <div className="text-[11px] text-[#888888] font-medium truncate" title={sm.stage_name}>{sm.stage_name}</div>
                    <div className="text-sm font-bold text-white font-mono mt-1">{sm.token_count.toLocaleString()} tok</div>
                    <div className="text-[11px] text-emerald-400 font-semibold mt-0.5">
                      {sm.reduction_pct.toFixed(1)}% ({sm.latency_ms.toFixed(1)}ms)
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
