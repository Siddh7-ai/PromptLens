# 🗺️ PromptLens: Project Evolution Roadmap & Technical Architecture

> **Core Research Vision**: Evolution from a surface-level tool log compressor to a **General-Purpose, Task-Aware, Dependency-Aware Context Optimization Engine** for AI Agents.

---

## 🎯 Executive Summary & Core Paradigm Shift

Current prompt compression systems (and PromptLens v1) compress content based primarily on **surface text appearance** (e.g., regex pattern matching, JSON array lengths, stack traces, and fixed head/tail line truncation).

This roadmap defines the transition to **Task-Aware & Dependency-Aware Context Compression**:
> *"Don't compress based only on what the text looks like. Compress based on what the coding task requires."*

```
Coding Prompt (User Request + Code/Context)
                     │
                     ▼
          Task Intent Classifier
                     │
       ┌─────────────┴─────────────┐
       ▼                           ▼
AST Code Parser          Dependency Call Graph
       │                           │
       └─────────────┬─────────────┘
                     ▼
       Semantic Relevance Scorer
                     │
                     ▼
         Knapsack Budget Allocator
                     │
     ┌───────────────┼───────────────┐
     ▼               ▼               ▼
 PRESERVE        SUMMARIZE         OMIT
(Full Code)    (AST Skeleton)  (Vault SHA-256)
     │               │               │
     └───────────────┼───────────────┘
                     ▼
           Compressed LLM Prompt
```

---

## 📊 Current System Audit (PromptLens v1 — Baseline)

| Component | Status | Description |
|---|---|---|
| **Deterministic Truncation** | ✅ Complete | Terminal logs, compiler output, stack trace deduplication (`src/compress/text_compressor.py`). |
| **JSON Stride Sampling** | ✅ Complete | Array stride sampling preserving dictionary keys (`src/compress/json_compressor.py`). |
| **Reversible Retrieval Vault** | ✅ Complete | Uncompressed text stored with SHA-256 ID; injected `retrieve_original(id)` tool for on-demand fetch (`src/store/retrieval_store.py`). |
| **Transparent Proxy** | ✅ Complete | FastAPI proxy intercepting Anthropic `/v1/messages` (`src/proxy/server.py`). |
| **React Dashboard & Extension** | ✅ Complete | Real-time analytics UI (`dashboard/`) and Manifest V3 web chat interceptor (`extension/`). |
| **Regex Structural ToC** | 🟡 Basic | Heuristic line index generator. Needs replacement with AST parsing. |

---

## 🚀 Version Progression Roadmap (v1 ➔ v5)

```
PromptLens v1 (Rule-Based Log/JSON Baseline)
      │
      ▼
PromptLens v2 (AST Code Outliner & Structural Compressor)
      │
      ▼
PromptLens v3 (Semantic Vector Embeddings & Similarity Index)
      │
      ▼
PromptLens v4 (Task Intent Classifier + Call-Graph Dependency Expansion)
      │
      ▼
PromptLens v5 (Adaptive Knapsack Token-Budget Optimization)
```

---

### 🔹 PromptLens v1: Rule-Based Baseline (Completed)
- Output-oriented filtering for logs, stack traces, git diffs, and large JSON arrays.
- Baseline for measuring empirical token savings and accuracy improvements.

### 🔹 PromptLens v2: AST Structural Code Compressor (Immediate Next Step)
- **Goal**: Replace plain text head/tail line slicing with Abstract Syntax Tree (AST) code skeletons.
- **Implementation**:
  - Python code: `ast` module parsing.
  - Multi-language support (JS, TS, Rust, Go, Java): `tree-sitter`.
- **Output**:
  - Converts 500-line source files into clean signatures (class declarations, method headers, route decorators, docstrings) while omitting body implementations.

### 🔹 PromptLens v3: Semantic Relevance Engine
- **Goal**: Rank code chunks by semantic similarity to the user's prompt.
- **Implementation**:
  - Local CPU-friendly embeddings (`fastembed` or `sentence-transformers/all-MiniLM-L6-v2`).
  - Cosine similarity scoring between prompt vector and chunk vectors.

### 🔹 PromptLens v4: Task-Aware & Dependency-Aware Compressor
- **Goal**: Classify user intent and expand dependency call-graphs.
- **Task Intent Classification**:
  - `Code Generation`: Preserve requirements, specs, constraints, outputs.
  - `Code Modification`: Identify target files and 1-hop dependencies.
  - `Debugging`: Prioritize error message, stack trace, affected lines.
  - `Explanation`: Preserve high-level class structures & data flow.
  - `Refactoring`: Preserve interfaces, relationships, duplicated logic.
  - `Test Generation`: Identify target functions & existing test suites.
- **Call-Graph Dependency Expansion**:
  - Trace import trees and function calls (e.g., target `login()` expands to `validateUser()`, `UserModel`, `JWT utility`).
- **3-State Context Strategy**:
  1. **PRESERVE**: Direct target code & 1-hop dependencies (full source).
  2. **SUMMARIZE**: 2-hop context & structural AST skeletons.
  3. **OMIT**: Unrelated files & logs (saved to SHA-256 Vault).

### 🔹 PromptLens v5: Adaptive Token-Budget Optimizer
- **Goal**: Formulate prompt allocation as a constrained optimization problem.
- **Mathematical Model**:
  $$\max \sum_{i} R_i \cdot x_i \quad \text{subject to} \quad \sum_{i} T_i \cdot x_i \le B$$
  - $R_i$: Relevance score of chunk $i$
  - $T_i$: Token cost of chunk $i$
  - $B$: Context budget limit (e.g., 128,000 tokens)
  - $x_i \in \{\text{PRESERVE}, \text{SUMMARIZE}, \text{OMIT}\}$

---

## 🔬 Experimental Evaluation Plan (6 Baselines)

To validate PromptLens for thesis/research evaluation, the framework will benchmark 6 distinct baselines across identical coding tasks:

1. **Baseline 1**: No compression (Raw Context)
2. **Baseline 2**: Naive Head-Tail compression (First 10 + Last 10 lines)
3. **Baseline 3**: PromptLens v1 (Rule-based Log/JSON)
4. **Baseline 4**: PromptLens v3 (Semantic Vector Relevance)
5. **Baseline 5**: PromptLens v4 (Task-Aware Semantic Relevance)
6. **Baseline 6**: PromptLens v5 (Task + Dependency-Aware Knapsack Allocation)

### Evaluation Metrics
- **Task Success Rate (%)**
- **Code Correctness / Pass@1 Rate**
- **Compilation / Test Execution Success**
- **Token Compression Ratio (%)**
- **Time-to-First-Token (TTFT) / Latency (ms)**
- **API Cost Reduction ($)**

---

## 📅 Next Action Plan

1. **Review this roadmap with your sir**.
2. **Begin Phase 1 Implementation**: Build `src/compress/ast_parser.py` (PromptLens v2) to establish structural AST code outlining.
