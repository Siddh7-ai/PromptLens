# 🎓 PromptLens - College Project Viva & Faculty Q&A Guide

This guide contains simple, direct, 2-line answers for all typical faculty/professor questions during project evaluation, presentations, and viva.

---

### Q1: What is PromptLens and what problem does it solve?
> **Answer**: PromptLens is a local token compression proxy for AI agents. It achieves a **40.3% Task-Weighted Mean Net Token Reduction** (35%–70% on logs/diffs, up to 99% on JSON arrays) by compressing large tool outputs before sending them to the LLM.

---

### Q2: How does the Vault handle storing full prompts for lots of users?
> **Answer**: The Vault uses an automatic 1-hour self-deletion timer to clean up old prompts and saves identical prompts only once using SHA-256 hashes to prevent duplicate memory usage.

---

### Q3: What if 1,000 users use this system simultaneously? How will it scale?
> **Answer**: In our working prototype, the Vault runs efficiently in local RAM with self-cleaning TTL timers. For production scaling with 1,000+ users, the system is designed to plug directly into a free Cloud Database (like Upstash Redis) without changing any core logic.

---

### Q4: How does PromptLens compress data without losing important information?
> **Answer**: It preserves the top and bottom lines of outputs, generates a Table of Contents (ToC) for code structure, collapses repeated log lines, and automatically pins critical error/exception messages into the output.

---

### Q5: What if the LLM needs the full uncompressed original content?
> **Answer**: PromptLens automatically injects a `retrieve_original(id)` tool call into the LLM prompt. If the model needs full data or specific line ranges, it calls this tool to instantly fetch the raw original content from the Vault.

---

### Q6: What if an implementation plan or design document gets compressed? Is data lost?
> **Answer**: No data is lost. The top of the compressed output includes a structural Table of Contents (ToC), so the model knows exact line numbers and can use `retrieve_original(id, line_range=[X, Y])` to fetch specific sections for just ~40 tokens.

---

### Q7: How is the Table of Contents (ToC) generated for code vs custom/unstructured text?
> **Answer**: PromptLens scans lines using AST keyword prefixes (`def`, `class`, `function`, `struct`, `#`). If the text is completely unformatted, it uses a 2-level fallback engine with generic regex and equal line-block chunking.

---

### Q8: What if a user inputs text written in a completely custom or unknown format?
> **Answer**: If no standard symbols or regex patterns match, PromptLens falls back to automatic Line-Block Chunking, dividing the omitted content into equal line-number ranges (e.g. Lines 1-20, 21-40) so a ToC is always generated.

---

### Q9: How does Error Anchor Pinning guarantee critical log failures are never lost?
> **Answer**: Middle lines are scanned for error keywords (`Error`, `Exception`, `FAIL`, `Warning`, `Traceback`). Any lines containing failures are automatically pinned into a dedicated `[PromptLens Pinned Middle Errors/Exceptions]` section.

---

### Q10: How does Targeted Query & Line-Range Retrieval save tokens when fetching skipped data?
> **Answer**: Instead of re-downloading a 50,000-token file, the LLM requests exact line ranges (`line_range=[37, 44]`) or regex search matches, fetching the exact required snippet in less than 50 tokens.

---

### Q11: What happens if an invalid or malformed regex query is passed by the LLM?
> **Answer**: PromptLens uses a Regex Safety Guard (`try/except re.error`). If a regex is malformed (e.g., `[unclosed(`), it safely falls back to case-insensitive literal substring search without throwing server errors.

---

### Q12: How does Adaptive Stride Sampling work for massive JSON arrays?
> **Answer**: For 10,000+ item JSON arrays, PromptLens samples representative items across the head, middle, and tail (100 items max) to build a rich key/type summary (`_promptlens_summary`) without token bloat or CPU lag.

---

### Q13: What technology stack is used in this project?
> **Answer**:
> - **Backend**: Python, FastAPI, Tiktoken (for token counting), Uvicorn.
> - **Frontend**: React 18, TypeScript, Tailwind CSS, Vite.
> - **Testing**: Pytest (35 automated unit & integration tests).

---

### Q14: How do you calculate token savings and cost reduction?
> **Answer**: We compare incoming baseline tokens against compressed tokens using OpenAI's `tiktoken` library (cl100k_base encoding) and calculate cost savings based on standard API rates ($3.00 per 1M input tokens).

---

### Q15: Why did you build a proxy instead of modifying the AI agent code?
> **Answer**: Building a proxy allows **zero code modification** to the AI agent. Any AI agent (like Claude Code or Cursor) can be routed through PromptLens simply by setting an environment variable (`ANTHROPIC_BASE_URL`).

---

### Q16: What are the future scope and enhancements for this project?
> **Answer**: Future scope includes adding a Redis cloud storage driver for multi-tenant deployment, custom regex bypass rules in the dashboard, and multi-LLM support (OpenAI, Gemini, Anthropic).

---

### Q17: How does a prompt travel from the user to PromptLens, get processed, and reach the AI?
> **Answer**: 
> 1. **Routing**: The client application (or proxy setting) redirects the request to PromptLens (`http://localhost:8000/v1`) instead of directly contacting OpenAI/Anthropic.
> 2. **Processing & Vault Storage**: PromptLens intercepts the request, saves the full raw prompt into RAM (Vault) with a SHA-256 ID, compresses heavy JSON/logs/files, and injects a `retrieve_original` tool definition.
> 3. **Forwarding**: PromptLens sends the small, compressed prompt to the actual LLM API over HTTPS and passes the reply back to the user.

---

### Q18: How does HTTPS forwarding work in PromptLens (in 1 line)?
> **Answer**: PromptLens acts as an HTTP proxy that attaches your original API key to the new compressed prompt and forwards it securely to OpenAI's server (`https://api.openai.com`) using Python's `httpx` client.

---

### Q19: In simple terms, what is the exact step-by-step summary of PromptLens proxying?
> **Answer**: PromptLens intercepts the request $\rightarrow$ extracts the user's API key and prompt $\rightarrow$ stores raw prompt in Vault $\rightarrow$ compresses heavy JSON/logs/files $\rightarrow$ re-sends the compressed prompt with the user's API key to OpenAI $\rightarrow$ returns the answer.

---

### Q20: What are the 4 main types of data content PromptLens compresses?
> **Answer**: 
> 1. **Build Logs & Stack Traces** (collapses repeated log lines and pins error messages).
> 2. **Large JSON Arrays** (samples item structures using Adaptive Stride Sampling).
> 3. **Source Code Dumps** (creates a Table of Contents for functions and classes).
> 4. **Large Text & Markdown Dumps** (uses line-range block chunking for ToC).

---

### Q21: What is the key difference between Headroom and PromptLens?
> **Answer**: Headroom is a multi-language SDK library/middleware for general backend LLM apps, whereas PromptLens is a specialized local proxy designed for AI coding agents (zero-code setup) featuring a live React Dashboard, SHA-256 Vault Inspector, Error Anchor Pinning, and Adaptive Stride JSON Sampling.

---

### Q22: What are the main similarities between Headroom and PromptLens?
> **Answer**: Both systems act as intercepting HTTP proxies, compress heavy context payloads to reduce LLM API token costs by 50%-98%, store raw uncompressed data in a local retrieval store, and inject reversible retrieval tools so models can fetch skipped data on-demand.

---

### Q23: What is the minimum threshold required for PromptLens to compress content?
> **Answer**: PromptLens requires a minimum of **50 tokens** (or **300 bytes**). Small inputs (like 5-line git diffs) are automatically validated for positive net savings; if notice overhead exceeds raw savings, PromptLens returns uncompressed raw text.

---

### Q24: Does PromptLens store or log the user's secret API key?
> **Answer**: No. PromptLens runs 100% locally on `localhost:8000` and relays the original `Authorization: Bearer sk-...` header to OpenAI without logging or storing API keys.

---

### Q25: How does Vault RAM management prevent memory bloat over long usage?
> **Answer**: Vault items automatically expire after 1 hour (3600s TTL) and duplicate prompts are deduplicated under shared SHA-256 hash IDs.

---

### Q26: How was the correctness of PromptLens verified?
> **Answer**: It was verified using 35 automated Pytest unit and integration tests covering proxy routing, Error Anchor Pinning, JSON stride sampling, 50-turn stress tests, and Vault retrieval tools.

---

### Q27: How are token savings and cost reductions calculated?
> **Answer**: Using OpenAI's `tiktoken` (`cl100k_base`), savings are calculated as `(1 - Compressed_Tokens / Original_Tokens) * 100` based on $3.00 per 1M input tokens.

---

### Q28: What tech stack powers the PromptLens Dashboard?
> **Answer**: A modern frontend built with React 18, TypeScript, Tailwind CSS, and Vite connecting to FastAPI backend endpoints.

---

### Q29: What major Python libraries are used in PromptLens and what does each do?
> **Answer**:
> - **FastAPI**: Used to build the local HTTP proxy server and REST API endpoints.
> - **Uvicorn**: Asynchronous ASGI server used to run and host the FastAPI application.
> - **httpx**: Asynchronous HTTP client used to forward compressed prompts to OpenAI/Anthropic over HTTPS.
> - **tiktoken**: Official OpenAI BPE tokenizer used to calculate precise token counts.
> - **pytest**: Automated testing framework used for unit and integration test suites.
> - **hashlib & re** (Standard Library): Used for SHA-256 Vault hashing and regex pattern matching for Error Anchor Pinning & ToC parsing.

---

### Q30: How can PromptLens be deployed for multi-tenant developer usage in production?
> **Answer**: 
> 1. **Vault Storage**: Upgrade local RAM storage to a cloud Redis database (like Upstash Redis) for scalable multi-user caching.
> 2. **Backend & Dashboard**: Containerize FastAPI with Docker and host on Render/Railway, and host the React dashboard on Vercel.
> 3. **Distribution**: Publish as a PyPI CLI package (`pip install promptlens`) or host as a managed cloud proxy (`https://api.promptlens.ai/v1`).

---

### Q31: Is our current PromptLens architecture already aligned for a 2-command PyPI CLI deployment?
> **Answer**: Yes, 100%! Because PromptLens is built as a modular Python package (`src/`) with FastAPI and Uvicorn, simply defining a `[project.scripts]` entry in `pyproject.toml` enables any developer to run `pip install promptlens` and `promptlens start`.











