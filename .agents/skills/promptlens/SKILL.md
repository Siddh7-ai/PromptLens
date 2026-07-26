---
name: promptlens-optimization
description: Optimizes AI agent context window usage by compressing large tool outputs, stack traces, JSON arrays, build logs, and file dumps while preserving reversible SHA-256 vault retrieval.
---

# PromptLens Context Optimization Skill for Antigravity

This skill enables Antigravity to compress large outputs (stack traces, JSON API responses, compiler logs, and file reads) before processing or presenting them, saving **50% to 98% token costs** while maintaining 100% reversible retrieval via the Vault Store.

## Quick Start Guidelines for Antigravity

When executing operations that generate massive outputs (e.g. running pytest, inspecting build logs, reading large JSON files, or viewing long code files):

1. **Threshold Inspection**:
   - If output length exceeds **300 bytes** (~100 tokens), pass the string through PromptLens compression.

2. **Using the Compression Helper**:
   Execute the local Python compressor or query the local proxy (`http://localhost:8000`):
   ```python
   from src.compress.text_compressor import compress_text
   from src.compress.json_compressor import compress_json
   from src.store.retrieval_store import get_global_store

   store = get_global_store()
   vault_id = store.save(raw_output)
   compressed_res = compress_text(raw_output) # or compress_json(raw_output)
   ```

3. **Reversible Vault Retrieval**:
   If specific lines, stack frame details, or uncompressed JSON items are needed later, query the Vault:
   ```python
   raw_snippet = store.get(vault_id, query="line_or_symbol", context_lines=2)
   ```

4. **Live Dashboard & Audit Stream**:
   Whenever requests pass through the PromptLens Proxy Server (`http://localhost:8000/v1`), real-time stats and vault items automatically sync to the Headroom React Dashboard at `http://localhost:3000`.
