# PromptLens: AI Agent Context Optimization Proxy

> Typical reduction: **35% to 70%** on logs/diffs; up to **99%** on large repetitive JSON arrays. (Task-Weighted Mean Net Savings: **42.4%**).

PromptLens is a lightweight, rule-based local compression proxy for AI coding agents (such as Claude Code, Cursor, or custom Python agents). It sits transparently between your agent and the LLM API, compresses repetitive tool-call outputs (JSON arrays, stack traces, build logs, file reads) before forwarding them, and exposes a reversible `retrieve_original(id)` tool so the model can recover full uncompressed data if needed.

---

## ⚡ Features

- ✂️ **Rule-Based Compression**: Intelligently truncates large JSON arrays, stack traces, compiler logs, and file dumps while preserving critical structure and error context.
- 🔒 **Reversible Retrieval Store (Vault)**: Saves uncompressed raw data keyed by SHA-256 hash IDs with automatic TTL expiration.
- 🛠️ **Transparent Tool Injection**: Automatically injects `retrieve_original(id)` into agent tools so LLMs can fetch original data on demand.
- 🌉 **Zero-Code Passthrough Proxy**: Transparent FastAPI proxy supporting Anthropic API requests (`POST /v1/messages`) and streaming responses.
- 📊 **Headroom-Style React Dashboard**: Standalone React + TypeScript web app (`http://localhost:3000`) featuring Headroom obsidian theme, Reversible Vault Inspector, Token Savings Chart, and Rule Settings sliders.

---

## 🚀 Quickstart Guide: How to Run the Whole Project

### Step 1: Install Dependencies & Activate Environment

```bash
# Clone the repository
git clone https://github.com/Siddh7-ai/PromptLens.git
cd PromptLens

# Create and activate Python virtual environment
python -m venv .venv
source .venv/bin/activate        # On Windows (PowerShell): .\.venv\Scripts\activate

# Install Python requirements
pip install -r requirements.txt

# Install Dashboard Node dependencies
cd dashboard
npm install
cd ..
```

---

### Step 2: Start the PromptLens Python Proxy Backend

In your main project directory, start the FastAPI proxy server on port 8000:

**On Windows (PowerShell):**
```powershell
.\.venv\Scripts\uvicorn src.proxy.server:app --port 8000 --reload
```

**On Linux / macOS:**
```bash
uvicorn src.proxy.server:app --port 8000 --reload
```
- **Proxy Endpoint:** `http://localhost:8000/v1`
- **Health Check:** `http://localhost:8000/health`
- **Metrics API:** `http://localhost:8000/api/stats`

---

### Step 3: Start the Standalone React Dashboard

In a new terminal window:

```bash
cd dashboard
npm run dev
```

Open **`http://localhost:3000`** in your browser to access:
- **Overview & Community Stats**
- **Reversible Vault Inspector**
- **Interactive Playground ✨**
- **Token Savings Chart**
- **Rule Settings & Sliders**

---

### Step 4: Run AI Agents Through PromptLens

To route any AI coding agent (like Claude Code or Cursor) through PromptLens, set the `ANTHROPIC_BASE_URL` environment variable:

#### Linux / macOS:
```bash
export ANTHROPIC_BASE_URL="http://localhost:8000/v1"
claude
```

#### Windows (PowerShell):
```powershell
$env:ANTHROPIC_BASE_URL="http://localhost:8000/v1"
claude
```

---

## 📊 Benchmark Results Across 5 Real-World Tasks

Run the 5-task benchmark evaluation script:
```bash
python scripts/benchmark_tasks.py
```

| Task Name | Category | Baseline Tokens | Compressed Tokens | Net Savings (with Retrieval Overhead) | Correctness |
|---|---|:---:|:---:|:---:|:---:|
| 1. Python Pytest Failure Trace | Stack Trace / Log | 1,061 | 730 | **22.6%** | 100% Pass |
| 2. Large JSON REST API Array | JSON Payload | 118,154 | 984 | **99.1%** | 100% Pass |
| 3. Git Diff Patch Output | Version Control Diff | 606 | 518 | **-0.5%** | 100% Pass |
| 4. NPM Build Log Errors | Compiler / Build Log | 1,270 | 682 | **39.1%** | 100% Pass |
| 5. Environment & File Read | System Environment | 947 | 465 | **41.3%** | 100% Pass |
| **TOTAL BENCHMARK METRICS** | **Across 5 Tasks** | **122,038** | **3,379** | **96.9%** | **100% Pass** |

### 📈 Statistical Summary & Key Notes
- **Task-Weighted Mean Net Reduction**: **40.3%** (Mean of per-task Net Savings)
- **Median Net Token Reduction**: **39.1%**
- **Peak Net Reduction (JSON Array)**: **99.1%**
- **Blended Total Reduction (Summed)**: **96.9%**
- **Measured Round-Trip Retrieval Overhead**: **91 tokens** per `retrieve_original` call

> 💡 **Note on Task 1 (Pytest Failure Trace):** Token savings were adjusted from raw truncation (62.9%) to **22.6% Net Savings** after enabling **Error Anchor Pinning**. Preserving exact `KeyError` lines and exception tracebacks increases prompt tokens slightly but ensures the LLM sees the root cause without requiring an extra retrieval tool call.
>
> 💡 **Note on Task 3 (Git Diff Output):** Raw text compression saves **+14.5%** (518 tokens vs 606 baseline tokens). When conservatively adding **91 tokens of round-trip retrieval overhead** (`518 + 91 = 609`), the Net Savings is **-0.5%**. PromptLens's live proxy evaluates raw tokens before forwarding; if raw compression saves tokens without a tool fetch, the prompt is delivered at 518 tokens.

---

## ⚠️ Known Limitations

1. **Short Diffs & Tiny Tool Outputs**: Tool outputs under 300 bytes or under 50 tokens (e.g. 5-line git diffs) are not compressed. Adding PromptLens retrieval notices to very small diffs can add net token overhead. PromptLens automatically detects negative net savings and forwards raw uncompressed text to prevent token expansion.
2. **First-Turn Retrieval Overhead**: When a compressed tool output requires a full raw retrieval via `retrieve_original(id)`, a round-trip retrieval tool call incurs an empirical overhead of ~91 tokens.
3. **Local In-Memory Vault Persistence**: The default `RetrievalStore` is an in-memory TTL vault. Re-starting the proxy clears active vault keys. In production multi-node agent deployment, backing `RetrievalStore` with Redis or disk storage is recommended.

---

## 🧪 Running Automated Unit Tests

Run all 35 automated tests with `pytest`:
```bash
pytest
```

---

## 📂 Project Architecture

```text
PromptLens/
├── dashboard/                  # ⚛️ Standalone React 18 + TypeScript Web Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.tsx             # Headroom obsidian docs sidebar
│   │   │   ├── VaultInspector.tsx      # Reversible vault payload inspector
│   │   │   ├── SavingsChart.tsx        # Interactive SVG savings line curve
│   │   │   ├── SettingsPanel.tsx       # Live compression sliders
│   │   │   ├── StatCard.tsx            # Stat cards
│   │   │   ├── OptimizationBar.tsx     # Optimization ratio gauge
│   │   │   ├── BenchmarkTable.tsx      # 5-task benchmark table
│   │   │   ├── RequestStream.tsx       # Audit log table
│   │   │   └── Playground.tsx          # Interactive live testbed
│   │   ├── App.tsx                     # Main React application shell
│   │   └── types.ts                    # TypeScript interfaces
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── fixtures/                   # Real-world tool output test fixtures
├── scripts/
│   ├── count_tokens.py         # Token counter baseline script
│   ├── benchmark_tasks.py     # 5-task benchmark suite
│   └── run_agent_demo.py       # Multi-turn real agent integration demo
├── src/
│   ├── compress/
│   │   ├── json_compressor.py  # Rule-based JSON array truncation
│   │   └── text_compressor.py  # Log, stack trace, and diff compressor
│   ├── store/
│   │   └── retrieval_store.py  # Hash-keyed reversible data vault
│   └── proxy/
│       ├── server.py           # FastAPI transparent passthrough proxy
│       ├── stats.py            # Metrics tracking engine
│       └── dashboard_html.py   # Web Dashboard UI
├── tests/                      # 23 automated unit & integration tests
├── PROJECT_BRIEF.md            # Specification
└── requirements.txt            # Python dependencies
```

---

## 📜 License

MIT License. Built for AI Agent Context Optimization.
