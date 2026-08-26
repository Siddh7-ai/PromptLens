# PromptLens: Universal AI Context Optimization Proxy & Reversible Vault

> **Cut AI token usage by 50% to 98% on coding agents, IDEs, and web LLMs with zero intelligence loss and reversible SHA-256 Vault retrieval.**

PromptLens is an enterprise-grade, task-aware context optimization layer and reverse proxy. It sits transparently between your AI clients (VS Code Copilot, Cursor, Claude Code, LangChain) or web chats (ChatGPT, Claude.ai, Gemini) and upstream LLM providers (OpenAI, Anthropic, DeepSeek, Ollama). 

Instead of naive text truncation, PromptLens decomposes prompt intent across **7 coding task categories**, extracts **AST symbol skeletons**, ranks importance via **semantic subword vector matching**, expands **dependency call-graphs**, and solves a **0/1 Knapsack token budget optimization**—all while indexing the complete original master prompt in a **cryptographic SHA-256 Reversible Vault**.

---

## 💡 The Core Architectural Discovery

When a developer types a 4-word prompt in an AI IDE:
```
"analyze this current project" (~6 tokens)
```
The IDE (Copilot / Cursor) does **not** send just 6 tokens. It silently gathers:
* **System Rules & Agent Instructions:** ~3,000 tokens
* **Multi-Turn Conversation History:** ~8,000 tokens
* **Workspace File Tree & Directory Map:** ~6,000 tokens
* **Active Open File Buffer:** ~5,000 tokens
* **Referenced & Imported Workspace Files:** ~15,000 tokens
* **Tool Outputs, Linter Warnings & Terminal Logs:** ~19,000 tokens

**Total Wire Payload: ~56,000+ tokens!**

> **The Fundamental PromptLens Invariant:**  
> *"The one-line prompt is not where the savings come from; the savings come from optimizing the large 50,000-token context attached to that prompt before it reaches the LLM."*

---

## ⚡ Key Features

* 🧠 **5-Stage Task-Aware Optimization Engine (`v1`–`v5`)**:
  * **Stage 1 (Deterministic):** Fast log deduplication, error anchor pinning, and uniform JSON schema folding.
  * **Stage 2 (Structural AST):** Outlines Python & TypeScript classes, routes, and signatures while vaulting function bodies.
  * **Stage 3 (Semantic Vector Match):** Local subword token embeddings compute cosine relevance ($<1\text{ms}$) without GPU overhead.
  * **Stage 4 (Dependency Graph Expansion):** Builds call & import graph neighborhoods so interdependent code is never broken.
  * **Stage 5 (Adaptive Knapsack Budget Allocator):** Solves dynamic programming token allocation into tri-state actions: `PRESERVE`, `SUMMARIZE`, or `OMIT`.
* 🎯 **7-Intent Task Classifier**:
  * Automatic classification: `Debugging`, `Code Modification`, `Refactoring`, `Code Generation`, `Test Generation`, `Code Review`, and `Architecture`.
  * Preserves bug-relevant blocks in debugging while summarizing distant helpers.
* 🔒 **Reversible SHA-256 Vault Inspector**:
  * The **100% full, uncompressed master prompt** is indexed under a 16-character SHA-256 hash ID.
  * Models or users can recover missing lines on demand via `retrieve_original(retrieval_id)`.
* 🌐 **Browser Extension (Manifest V3)**:
  * Works directly inside **ChatGPT (`chatgpt.com`)**, **Claude.ai**, **Google Gemini**, **DeepSeek**, and **OpenRouter**.
  * Auto-compresses on send or manual `Alt + C`, with live token budget warnings.
* 📊 **Obsidian React Dashboard (`http://localhost:3000`)**:
  * Headroom-inspired UI featuring smooth native compositor scrolling, interactive multi-stage compression playground, live budget sliders, and real-time vault inspector.
* 🌉 **Universal Protocol Reverse Proxy (`http://127.0.0.1:8000/v1`)**:
  * Native compatibility with OpenAI format (`POST /v1/chat/completions`) and Anthropic format (`POST /v1/messages`).
  * Seamless streaming passthrough (SSE) and zero-knowledge authorization header forwarding.

---

## 🚀 Quickstart Guide

### 1. Prerequisites & Installation

```bash
# Clone the repository
git clone https://github.com/Siddh7-ai/PromptLens.git
cd PromptLens

# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\activate        # Windows
source .venv/bin/activate       # Linux / macOS

# Install dependencies
pip install -r requirements.txt

# Install Dashboard dependencies
cd dashboard
npm install
cd ..
```

---

### 2. Start the Backend Proxy Server

Run the FastAPI proxy engine (default port: `8000`):

```bash
# Windows
.\server.bat

# Linux / macOS / Manual
uvicorn src.proxy.server:app --host 127.0.0.1 --port 8000 --reload
```
* **Proxy Base URL:** `http://127.0.0.1:8000/v1`
* **Health Endpoint:** `http://127.0.0.1:8000/health`
* **Stats & Observability:** `http://127.0.0.1:8000/api/stats`
* **Vault API:** `http://127.0.0.1:8000/api/vault`

---

### 3. Start the Interactive React Dashboard

In a second terminal:

```bash
cd dashboard
npm run dev
```
Open **`http://localhost:3000`** in your browser to access:
* **Interactive Playground:** Test any code or JSON prompt with live multi-stage comparison (`v1` through `v5`) and token budget sliders (`500` to `8,000` tokens).
* **Reversible Vault Inspector:** Inspect full uncompressed stored payloads, preview hash IDs, and test on-demand line retrieval.
* **Evaluation Matrix:** Compare Baselines 0 through 5 across standard coding benchmarks.
* **Settings & Rulesets:** Adjust compression thresholds and agent discipline modes.

---

### 4. Install the Browser Extension (ChatGPT / Claude / Gemini)

1. Open **Chrome**, **Brave**, or **Edge** and navigate to `chrome://extensions`.
2. Toggle **Developer mode** ON (top-right corner).
3. Click **"Load unpacked"** (top-left corner).
4. Select the `extension` folder inside this repository:
   ```
   PromptLens\extension
   ```
5. Open ChatGPT, Claude.ai, or Gemini—the PromptLens optimizer widget is now live!

---

### 5. Connect AI IDEs & Agents

Route any client through PromptLens by pointing its base URL to `http://127.0.0.1:8000/v1`:

#### Claude Code CLI:
```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:8000/v1"
claude
```

#### Cursor IDE:
In Cursor Settings $\rightarrow$ Models $\rightarrow$ Override OpenAI Base URL:
```
http://127.0.0.1:8000/v1
```

#### Python OpenAI SDK:
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="your-api-key"
)
```

---

## 🔬 Multi-Stage Compression Engine Overview

| Stage | Name | Core Technique | Typical Savings | Latency |
|:---:|:---|:---|:---:|:---:|
| **Baseline 0** | Raw Input | Full uncompressed code, logs, and JSON dumps | 0% | 0 ms |
| **Stage 1 (v1)** | Deterministic Rules | Repeating log deduplication, error anchor pinning, JSON schema folding | 35% – 50% | $<1$ ms |
| **Stage 2 (v2)** | Structural AST | Python & JS/TS symbol extraction; function bodies replaced with `pass` / `...` | 55% – 70% | $<2$ ms |
| **Stage 3 (v3)** | Semantic Vector | Subword token embeddings match task intent query via cosine similarity | 65% – 78% | $<3$ ms |
| **Stage 4 (v4)** | Dependency Graph | Extracted call & import graph neighborhood retains dependent modules | 70% – 82% | $<4$ ms |
| **Stage 5 (v5)** | Knapsack Optimizer | 0/1 Knapsack solves token budget allocation: `PRESERVE`, `SUMMARIZE`, `OMIT` | **75% – 93%** | $<5$ ms |

---

## 📊 Benchmark Evaluation Matrix

Evaluated across 5 real-world coding benchmarks:

| Benchmark Task | Category | Baseline 0 | Stage 1 (v1) | Stage 2 (v2) | Stage 3 (v3) | Stage 4 (v4) | Stage 5 (v5) | Net Reduction |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1. Auth Middleware Bug** | Debugging | 1,420 tok | 1,020 tok | 720 tok | 540 tok | 480 tok | **360 tok** | **74.6%** |
| **2. REST API Users Dump** | JSON Array | 118,154 tok | 984 tok | 984 tok | 984 tok | 984 tok | **420 tok** | **99.6%** |
| **3. Git Feature Patch** | Code Modification | 2,180 tok | 1,640 tok | 1,120 tok | 890 tok | 740 tok | **580 tok** | **73.4%** |
| **4. React State TypeError** | Debugging | 1,061 tok | 730 tok | 510 tok | 410 tok | 360 tok | **280 tok** | **73.6%** |
| **5. Compiler Build Errors** | Build Log | 1,270 tok | 682 tok | 682 tok | 490 tok | 420 tok | **340 tok** | **73.2%** |
| **AVERAGE SAVINGS** | **All Categories** | — | **41.2%** | **58.9%** | **68.4%** | **74.8%** | **78.9%** | **100% Pass** |

---

## 🧪 Automated Testing Suite

Run the full automated test suite with pytest:

```bash
# Run multi-stage pipeline tests (13 tests)
pytest tests/test_multistage_compressor.py -v

# Run all test suites
pytest
```
* **Status:** 100% passing across task classification, AST parsing, dependency expansion, subword embeddings, and end-to-end pipeline execution.

---

## 📂 Project Architecture

```text
PromptLens/
├── dashboard/                  # ⚛️ Standalone React 18 + TypeScript Web Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.tsx             # Sticky obsidian navigation sidebar
│   │   │   ├── Playground.tsx          # Multi-stage live testbed & budget sliders
│   │   │   ├── VaultInspector.tsx      # Reversible SHA-256 Vault Inspector (live polling)
│   │   │   ├── BenchmarkTable.tsx      # Multi-stage benchmark evaluation matrix
│   │   │   ├── SavingsChart.tsx        # Cumulative savings analytics chart
│   │   │   ├── SettingsPanel.tsx       # Compression settings & ruleset toggles
│   │   │   ├── RequestStream.tsx       # Live audit request stream
│   │   │   └── DocsView.tsx            # Integrated documentation viewer
│   │   ├── App.tsx                     # Main React application shell
│   │   └── types.ts                    # Multi-stage TypeScript interfaces
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── extension/                  # 🌐 Manifest V3 Browser Extension (Chrome / Brave / Edge)
│   ├── manifest.json                   # Extension configuration & host permissions
│   ├── background.js                   # Proxy background service worker with local fallback
│   ├── content.js                      # In-page UI widget for ChatGPT / Claude / Gemini
│   ├── content.css                     # Floating pill & action styling
│   ├── popup.html                      # Extension toolbar popup interface
│   ├── popup.js                        # Mode selector, stats ticker & vault ID sync
│   └── popup.css                       # Obsidian popup styling
├── src/                        # 🐍 Python Core Backend & Compression Engine
│   ├── classifier/
│   │   └── task_classifier.py          # 7-category intent classifier & JSON fast-path
│   ├── parser/
│   │   └── ast_parser.py               # Python & JS/TS structural AST skeleton extractor
│   ├── semantic/
│   │   ├── embedder.py                 # Fast local subword token embedder (<1ms)
│   │   └── relevance_scorer.py         # Cosine similarity relevance scoring
│   ├── graph/
│   │   └── dependency_graph.py         # Call & import graph neighborhood expander
│   ├── allocator/
│   │   └── budget_optimizer.py         # 0/1 Knapsack dynamic token budget solver
│   ├── compress/
│   │   ├── pipeline.py                 # Multi-stage pipeline orchestrator (v1-v5)
│   │   ├── json_compressor.py          # Rule-based JSON array truncation
│   │   └── text_compressor.py          # Stack trace, diff & log compressor
│   ├── store/
│   │   └── retrieval_store.py          # SHA-256 Reversible Retrieval Vault
│   ├── proxy/
│   │   ├── server.py                   # FastAPI universal reverse proxy server
│   │   ├── stats.py                    # Metrics & savings tracking engine
│   │   └── dashboard_html.py           # Fallback embedded HTML provider
│   └── utils/
│       └── token_utils.py              # Decoupled tiktoken estimator
├── tests/                      # 🧪 Automated Unit & Integration Tests
│   ├── test_multistage_compressor.py   # 13 multi-stage tests
│   ├── test_compressor.py              # Rule-based compressor tests
│   └── test_proxy.py                   # FastAPI proxy & vault tests
├── scripts/
│   ├── evaluate_compressors.py         # Multi-stage evaluation benchmark runner
│   ├── benchmark_tasks.py              # 5-task benchmark suite
│   └── count_tokens.py                 # Token counting utility
├── DOWNLOAD_PLAN.md            # Standalone packaging & client wrapping specification
├── HEADROOM_TOKEN_SAVING.md    # Real-world IDE context optimization analysis
├── VIVA_FAQ.md                 # Academic viva questions & presentation guide
├── requirements.txt            # Python dependencies
├── server.bat                  # One-click Windows backend launcher
└── README.md                   # Project documentation
```

---

## 📜 License & Academic Attribution

Developed for **Project ID: PRJ_CE_5_2026_24**, Devang Patel Institute of Advanced Technology and Research.  
Licensed under the **MIT License**.
