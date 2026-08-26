# PromptLens Universal Installation, Packaging & Client Wrapping Plan

> **Architectural Blueprint & Usability Strategy**  
> Based on the Headroom zero-friction client integration model: packaging the entire runtime, standalone CLI/GUI distribution, protocol-level abstraction, and seamless application wrapping (`wrap` / `unwrap`).

---

## 1. Core Usability Principle: Install vs. Connect

An enterprise-grade developer tool must cleanly separate two distinct lifecycle stages:

```
┌────────────────────────────────────────────────────────┐
│ STAGE 1: INSTALL                                       │
│ "PromptLens exists and runs locally on this computer"  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 2: CONNECT                                       │
│ "Target AI client routes traffic through PromptLens"   │
└────────────────────────────────────────────────────────┘
```

The end user should **never** be forced to manually manage:
* Python versions, `pip`, or virtual environments (`.venv`).
* Background daemon processes or manual port configuration.
* API routing formats or manual endpoint hacking.

### The Ideal User Flow:
```
Download PromptLensSetup.exe (or pip install promptlens)
         ↓
Double-Click & Install (100% bundled runtime)
         ↓
Local Proxy Automatically Active (127.0.0.1:8000)
         ↓
Click [ Connect VS Code ] or run `promptlens wrap vscode`
         ↓
Done — All AI traffic optimized seamlessly with live Vault retrieval
```

---

## 2. How Headroom is Downloaded & Installed (Under the Hood)

When you installed Headroom, you ran a simple command:
```bash
python -m pip install "headroom-ai[proxy]"
```

Although it looked like a simple download, pip executed a complex installation pipeline behind the scenes:

```
User runs pip command
         ↓
Pip queries PyPI (Python Package Index)
         ↓
Downloads pre-compiled wheel: headroom-ai-0.36.5-py3-none-any.whl
         ↓
Pip resolves & auto-downloads ~20 dependencies:
├── uvicorn, fastapi, starlette (HTTP reverse proxy engine)
├── httpx (Upstream provider HTTP connection pool)
├── click / typer (Terminal command-line engine)
├── pydantic (API schema validation)
└── tree-sitter / ast-grep (AST code outline parser)
         ↓
Pip reads [project.scripts] entry point from pyproject.toml:
    headroom = "headroom.cli:main"
         ↓
Pip generates the Windows C-shim executable:
    C:\Users\<User>\AppData\Local\Programs\Python\Python313\Scripts\headroom.exe
         ↓
User can immediately run: `headroom proxy` or `headroom wrap vscode`
```

### Why This Felt Effortless:
1. **The User Did Not Write Code:** They didn't configure a server or touch any source files.
2. **Automated Binary Creation:** Pip automatically created `headroom.exe` inside the user's system `PATH`.
3. **Multi-Channel Distribution:** Headroom also supports:
   * **uv tool install:** `uv tool install --python 3.13 "headroom-ai[all]"` (sandbox isolation).
   * **Docker:** `docker run -p 8787:8787 ghcr.io/headroomlabs-ai/headroom:latest`.
   * **npm SDK:** `npm install @headroom/sdk` (TypeScript wrapper).

---

## 3. How We Are Going to Make PromptLens Work the Exact Same Way

To achieve the exact same zero-friction experience in PromptLens, we will implement this 4-step deployment blueprint:

### Step 1: Create `pyproject.toml` with the `promptlens` Console Entry Point
We configure PromptLens as a distributable Python package:
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "promptlens"
version = "2.0.0"
description = "Universal AI Context Optimization Proxy & Reversible Vault"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.29.0",
    "httpx>=0.27.0",
    "pydantic>=2.7.0",
    "click>=8.1.0"
]

[project.scripts]
promptlens = "src.cli:main"
```
**The Result:** When anyone runs `pip install promptlens`, pip will automatically generate `promptlens.exe` in their system PATH.

---

### Step 2: Build the Unified CLI Engine (`src/cli.py`)
We create a Click-powered CLI that handles every lifecycle command:
```python
import click
import uvicorn
import subprocess
import json
import os
from pathlib import Path

@click.group()
def main():
    """PromptLens — Universal Context Optimization Proxy & Reversible Vault"""
    pass

@main.command()
@click.option("--port", default=8000, help="Proxy port (default: 8000)")
@click.option("--host", default="127.0.0.1", help="Host binding")
def proxy(port, host):
    """Start the PromptLens local optimization proxy."""
    click.echo(f"⚡ Starting PromptLens Proxy on http://{host}:{port}...")
    uvicorn.run("src.proxy.server:app", host=host, port=port, log_level="info")

@main.command()
@click.argument("target")
def wrap(target):
    """Connect an AI client (vscode, cursor, claude) to PromptLens."""
    if target == "vscode":
        settings_path = Path(os.environ["APPDATA"]) / "Code" / "User" / "settings.json"
        data = json.loads(settings_path.read_text("utf-8")) if settings_path.exists() else {}
        data.setdefault("github.copilot.advanced", {})["debug.overrideProxyUrl"] = "http://127.0.0.1:8000"
        settings_path.write_text(json.dumps(data, indent=2), "utf-8")
        click.echo("✓ Successfully wrapped VS Code Copilot! All traffic routes through PromptLens.")

@main.command()
@click.argument("target")
def unwrap(target):
    """Restore an AI client to its default direct cloud endpoint."""
    if target == "vscode":
        settings_path = Path(os.environ["APPDATA"]) / "Code" / "User" / "settings.json"
        if settings_path.exists():
            data = json.loads(settings_path.read_text("utf-8"))
            if "github.copilot.advanced" in data:
                data["github.copilot.advanced"].pop("debug.overrideProxyUrl", None)
            settings_path.write_text(json.dumps(data, indent=2), "utf-8")
        click.echo("✓ Successfully unwrapped VS Code. Direct GitHub connection restored.")
```

---

### Step 3: Package as a Standalone Windows Binary (`PromptLensSetup.exe`)
For non-Python users, we bundle Python + FastAPI + our React Dashboard into a single self-contained executable using **PyInstaller**:
```bash
pyinstaller --noconfirm --onedir --windowed \
  --name "PromptLens" \
  --add-data "dashboard/dist;dashboard/dist" \
  --add-data "src;src" \
  src/cli.py
```
This produces a `PromptLensSetup.exe` installer. The end user simply double-clicks and runs PromptLens with **zero Python knowledge**.

---

### Step 4: Side-by-Side Equivalence Table

| Headroom Command | PromptLens Equivalent | Behind-the-Scenes Action |
| :--- | :--- | :--- |
| `pip install "headroom-ai[proxy]"` | `pip install "promptlens[proxy]"` | Downloads wheel, auto-installs dependencies, generates `.exe` |
| `headroom proxy` | `promptlens proxy` | Launches FastAPI proxy on localhost with 5-stage engine |
| `headroom wrap vscode` | `promptlens wrap vscode` | Injects `overrideProxyUrl` into VS Code `settings.json` |
| `headroom unwrap vscode` | `promptlens unwrap vscode` | Cleans up `settings.json`, restores original Copilot config |
| `headroom wrap claude` | `promptlens wrap claude` | Wraps session `ANTHROPIC_BASE_URL` to local proxy |
| `headroom status` | `promptlens status` | Pings `/health`, returns live token & cost savings |
| *No equivalent (CLI only)* | **PromptLens Dashboard (`:3000`)** | Interactive Knapsack budget slider, Diff preview, Vault inspector |
| *No equivalent (CLI only)* | **PromptLens Browser Extension** | In-page injection for ChatGPT, Claude.ai, and Gemini web chats |

---

## 4. Packaging & Distribution Architecture

PromptLens offers two distribution pathways:

### Path A: Standalone Consumer Installer (`PromptLensSetup.exe`)
* **Target Audience:** Developers, researchers, and students who want a 1-click install without configuring Python.
* **Technology:** PyInstaller / Inno Setup bundling:
  * Embedded Python 3.12/3.13 runtime.
  * PromptLens FastAPI proxy server (`uvicorn` + `fastapi`).
  * AST parsers, subword tokenizers, and knapsack allocators.
  * Static production React Dashboard bundle.
* **Result:** User downloads `PromptLensSetup.exe` $\rightarrow$ Installs to `%LOCALAPPDATA%\PromptLens` $\rightarrow$ Registers system path `promptlens.exe` $\rightarrow$ Launches system tray icon and background proxy.

### Path B: Developer CLI Package (`pip install "promptlens[proxy]"`)
* **Target Audience:** Power users, Python agent engineers, and CI/CD pipelines.
* **Command:**
  ```bash
  pip install promptlens[proxy]
  # Or via uv:
  uv tool install "promptlens[all]"
  ```
* Automatically registers the console script entry point `promptlens` in the user's PATH.

---

## 5. How PromptLens Supports 50+ LLMs (Protocol-Level Abstraction)

PromptLens avoids hardcoding model-specific logic by operating strictly at the **API Protocol Layer**:

```
                       ANY AI CLIENT
           (VS Code Copilot, Cursor, LangChain, Claude Code)
                             │
                             ▼
                     ┌───────────────┐
                     │   PROMPTLENS  │
                     │  Local Proxy  │ (127.0.0.1:8000)
                     └───────┬───────┘
                             │
                  5-Stage Context Optimization
                  (AST, Semantic, Knapsack, Vault)
                             │
                             ▼
                       ORIGINAL API
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
    OpenAI Wire         Anthropic Wire      Google Gemini
  (/v1/chat/completions) (/v1/messages)    (GenerateContent)
         │                   │                   │
  ┌──────┴──────┐            │                   │
  ▼             ▼            ▼                   ▼
GPT-4o      DeepSeek-R1  Claude 3.5 Sonnet   Gemini 2.0 Flash
Ollama      Groq / Qwen  Claude 3.5 Haiku    Gemini 1.5 Pro
Together    Mistral
```

### The Universal Compatibility Layers:
1. **Layer 1 — Universal OpenAI Protocol (`/v1/chat/completions` & `/v1/responses`):**
   * Covers OpenAI, DeepSeek, Groq, Together AI, Fireworks, Mistral, Perplexity, OpenRouter, and local engines (**Ollama, vLLM, LM Studio, llama.cpp**).
   * PromptLens preserves `"model": original_model` verbatim; it only parses and optimizes `"messages"`.
2. **Layer 2 — Anthropic Messages Protocol (`/v1/messages`):**
   * Covers Claude 3.5 Sonnet, Claude 3 Opus, Claude Code CLI, AWS Bedrock Anthropic, and Vertex AI Anthropic.
3. **Layer 3 — Multi-Provider Gateways (LiteLLM & OpenRouter):**
   * Acts as a transparent proxy or LiteLLM callback, instantly gaining coverage for 100+ upstream providers without individual driver code.

---

## 6. The `wrap` and `unwrap` Concept (Zero-Code Client Integration)

`promptlens wrap` uses official client configuration hooks to redirect outbound traffic through the local proxy, while `promptlens unwrap` cleanly restores factory defaults.

### Integration Target 1: VS Code GitHub Copilot
* **Command:** `promptlens wrap vscode`
* **Mechanism:** Modifies the official VS Code User settings (`%APPDATA%\Code\User\settings.json` on Windows, `~/Library/Application Support/Code/User/settings.json` on macOS):
  ```json
  {
    "github.copilot.advanced": {
      "debug.overrideProxyUrl": "http://127.0.0.1:8000"
    }
  }
  ```
* **Unwrap (`promptlens unwrap vscode`):** Removes only the `overrideProxyUrl` block, preserving all other user settings intact.

### Integration Target 2: Cursor IDE
* **Command:** `promptlens wrap cursor`
* **Mechanism:** Configures Cursor's OpenAI Base URL override to `http://127.0.0.1:8000/v1`.

### Integration Target 3: Claude Code CLI
* **Command:** `promptlens wrap claude`
* **Mechanism:** Sets session environment variable `ANTHROPIC_BASE_URL="http://127.0.0.1:8000"` and executes `claude`.

---

## 7. Critical Engineering Safeguards

### A. Streaming Preservation (Server-Sent Events / SSE)
* AI clients depend on token-by-token streaming (`stream: true`).
* PromptLens optimizes the **input context upfront**, then streams the upstream provider's `text/event-stream` response directly back to the client chunk-by-chunk with zero artificial buffering.

### B. Safe Authentication Passthrough
* PromptLens **never** stores or decrypts client API keys.
* Incoming `Authorization: Bearer sk-...` headers are forwarded directly upstream to OpenAI/Anthropic over TLS.

### C. Fail-Safe Strategy (Fail-Open vs. Fail-Closed)
* **Fail-Closed (Default for Accuracy):** If PromptLens proxy is stopped, requests are blocked with an explicit error: *"PromptLens proxy is not running on 127.0.0.1:8000. Run 'promptlens start' or 'promptlens unwrap'."*
* **Fail-Open (Optional Toggle):** If proxy is offline, client automatically bypasses directly to upstream cloud APIs.

---

## 8. PromptLens Unified CLI Specification

The `promptlens` command-line tool provides full control:

```bash
# Proxy Lifecycle
promptlens start [--port 8000] [--daemon]   # Start local proxy engine
promptlens stop                             # Gracefully terminate proxy
promptlens restart                          # Reload configuration
promptlens status                           # Check /health and token stats

# Application Wrapping
promptlens wrap vscode                      # Point VS Code Copilot to PromptLens
promptlens unwrap vscode                    # Restore original VS Code configuration
promptlens wrap cursor                      # Point Cursor IDE to PromptLens
promptlens unwrap cursor                    # Restore original Cursor configuration
promptlens wrap claude                      # Launch Claude Code through PromptLens

# Observability
promptlens stats                            # Display terminal summary of tokens saved
promptlens vault list                       # List recent uncompressed hashes
promptlens vault retrieve <hash_id>         # Fetch raw payload by SHA-256 ID
```

---

## 9. Dashboard 1-Click Client Connectors (GUI Integration)

For users who prefer visual management, the React Dashboard (`http://localhost:3000`) will provide a dedicated **Integrations** panel:

```
┌────────────────────────────────────────────────────────────────────────┐
│  🔌 PromptLens Client Connectors                                        │
│  Connect your favorite coding tools with zero manual configuration.    │
├────────────────────────────────────────────────────────────────────────┤
│  [VS Code Copilot]                                                     │
│  Status: ● Connected to 127.0.0.1:8000             [ Disconnect ]      │
│                                                                        │
│  [Cursor IDE]                                                          │
│  Status: ○ Disconnected (Ready to connect)         [ Connect ]         │
│                                                                        │
│  [Claude Code CLI]                                                     │
│  Status: ○ Disconnected                            [ Connect ]         │
└────────────────────────────────────────────────────────────────────────┘
```

When the user clicks **[ Connect ]**:
1. Dashboard sends `POST /api/integrations/vscode/wrap`.
2. Backend locates `settings.json`, injects `overrideProxyUrl`, and validates file lock.
3. Backend pings `/health` to verify proxy readiness.
4. Dashboard flips the status badge to glowing green `● Connected`.

---

## 10. Summary Comparison: Headroom vs. PromptLens

| Feature | Headroom | PromptLens |
| :--- | :--- | :--- |
| **Core Architecture** | Local HTTP Reverse Proxy | Local HTTP Reverse Proxy (`127.0.0.1:8000`) |
| **Target Protocols** | OpenAI + Anthropic + Bedrock | OpenAI + Anthropic + Google Gemini |
| **Compression Engine** | SmartCrusher / Kompress | 5-Stage Task-Aware Engine (`v1`–`v5`) + Knapsack |
| **Reversible Storage** | CCR (Content Chunk Retrieval) | SHA-256 Reversible Vault (`retrieve_original`) |
| **Terminal Integration**| `headroom wrap <client>` | `promptlens wrap <client>` |
| **Web Browser Extension**| ❌ None (CLI/SDK only) | ✅ Native Chrome/Brave/Edge (ChatGPT, Claude, Gemini) |
| **Interactive UI** | Basic metrics view | Full Obsidian React Dashboard + Playground + Vault |
| **Budget Control** | Daily USD budget | Knapsack Token Budget Limit (500 to 8k tokens) |
