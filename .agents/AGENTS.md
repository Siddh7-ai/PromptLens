# Project Custom Rules & Architecture Guidelines

## Smooth Scrolling & Layout Architecture Rule

1. **Window-Level Compositor Scrolling:**
   - Always attach primary page scrolling to `html` / `body` / window level (`min-h-screen`).
   - NEVER lock main page content inside an inner `h-screen overflow-y-auto` container div.
   - Inner `h-screen overflow-y-auto` divs bypass native browser window compositing and cause touchpad two-finger micro-stuttering and GPU lag.

2. **Sidebar Layout Pattern (Matching Headroom Docs 1:1):**
   - Keep the sidebar fixed/sticky using `sticky top-0 h-screen overflow-y-auto shrink-0`.
   - Allow the main content container (`flex-1 min-w-0 min-h-screen`) to flow naturally in the window document scroll context.

3. **CSS Smooth Scroll & Accessibility:**
   - Set `html { scroll-behavior: smooth; }` in CSS with accessibility fallback:
     ```css
     @media (prefers-reduced-motion: reduce) {
       html { scroll-behavior: auto; }
     }
     ```
   - NEVER apply `scroll-behavior: smooth !important` to the wildcard `*` selector, as it forces layout recalculations on every sub-element.

## PromptLens Context Optimization Rule

1. **Automatic Output Compression:**
   - Whenever executing commands or fetching file contents that produce large outputs (>300 bytes / >100 tokens), pass the content through `src.compress.text_compressor` or `src.compress.json_compressor`.
   - Save the raw uncompressed output to `src.store.retrieval_store.get_global_store()` under a SHA-256 hash ID.

2. **Reversible Vault Retrieval:**
   - Use `retrieve_original(id)` with targeted line ranges or regex queries to fetch missing details on-demand without re-processing full raw payloads.

3. **Live Proxy & Dashboard Synchronization:**
   - Route external HTTP client requests through `http://localhost:8000/v1` to monitor real-time token reduction and inspect vault payloads on `http://localhost:3000`.
