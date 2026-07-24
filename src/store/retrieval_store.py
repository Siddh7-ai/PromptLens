import hashlib
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class StoreItem:
    content: str
    created_at: float
    retrieval_id: str
    structural_map: Optional[dict] = None


class RetrievalStore:
    """
    Hash-keyed, TTL-based memory store for uncompressed original data with
    cached AST structural indexing, targeted line-range slicing, regex search,
    and context window extraction.
    """

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._store: Dict[str, StoreItem] = {}

    def _build_ast_structural_map(self, content: str) -> dict:
        """
        Parses content to generate a structural map of symbols and line bounds.
        """
        lines = content.splitlines()
        symbols = []
        symbol_prefixes = (
            "class ", "def ", "async def ", "function ", "async function ",
            "struct ", "impl ", "enum ", "trait ", "func ", "type ",
            "export default ", "export function ", "export class ",
            "# ", "## ", "### "
        )

        current_name = None
        symbol_start = 1

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith(symbol_prefixes):
                if current_name:
                    symbols.append({
                        "symbol": current_name,
                        "start_line": symbol_start,
                        "end_line": idx - 1,
                    })
                parts = stripped.split(":") if ":" in stripped else [stripped]
                raw_sym = parts[0].replace("{", "").strip()
                current_name = " ".join(raw_sym.split())
                symbol_start = idx

        if current_name and len(lines) >= symbol_start:
            symbols.append({
                "symbol": current_name,
                "start_line": symbol_start,
                "end_line": len(lines),
            })

        return {
            "total_lines": len(lines),
            "total_chars": len(content),
            "symbols": symbols,
        }

    def save(
        self,
        content: str,
        retrieval_id: Optional[str] = None,
        structural_map: Optional[dict] = None,
    ) -> str:
        """
        Saves original content to the store and returns a unique retrieval_id.
        Optionally pre-computes and caches the structural map.
        """
        if not retrieval_id:
            retrieval_id = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]

        if structural_map is None:
            structural_map = self._build_ast_structural_map(content)

        item = StoreItem(
            content=content,
            created_at=time.time(),
            retrieval_id=retrieval_id,
            structural_map=structural_map,
        )
        self._store[retrieval_id] = item
        return retrieval_id

    def list_items(self) -> list:
        """Returns metadata list of all active non-expired vault payloads."""
        self.cleanup_expired()
        items = []
        for retrieval_id, item in self._store.items():
            content = item.content
            items.append({
                "retrieval_id": retrieval_id,
                "created_at": item.created_at,
                "size_bytes": len(content.encode("utf-8")),
                "preview": content[:150] + ("..." if len(content) > 150 else ""),
                "full_content": content,
                "structural_map": item.structural_map,
            })
        items.sort(key=lambda x: x["created_at"], reverse=True)
        return items

    def get_structural_map(self, retrieval_id: str) -> Optional[dict]:
        """
        Returns the cached structural map in <0.1ms if item exists.
        """
        item = self._store.get(retrieval_id)
        if not item or (time.time() - item.created_at > self.ttl_seconds):
            return None
        if item.structural_map is None:
            item.structural_map = self._build_ast_structural_map(item.content)
        return item.structural_map

    def get(
        self,
        retrieval_id: str,
        query: Optional[str] = None,
        line_range: Optional[List[int]] = None,
        use_regex: bool = False,
        context_lines: int = 0,
    ) -> Optional[str]:
        """
        Retrieves original content or targeted line/query snippets by retrieval_id.

        Args:
            retrieval_id: The hash key of the stored payload.
            query: Substring or Regex query string to filter lines.
            line_range: 2-element list [start_line, end_line] (1-indexed).
            use_regex: If True, treats query as a regex pattern. Safe fallback if pattern fails.
            context_lines: Number of surrounding lines to include around query matches.
        """
        item = self._store.get(retrieval_id)
        if not item:
            return None

        # Check TTL
        if time.time() - item.created_at > self.ttl_seconds:
            del self._store[retrieval_id]
            return None

        raw_content = item.content

        # Full content retrieval if no query or range specified
        if not query and not line_range:
            return raw_content

        lines = raw_content.splitlines()
        total_lines = len(lines)
        matched_indices = set()

        # Handle line_range [start_line, end_line] (1-indexed)
        if line_range and len(line_range) >= 2:
            start_line = max(1, line_range[0])
            end_line = min(total_lines, line_range[1])
            for line_idx in range(start_line - 1, end_line):
                matched_indices.add(line_idx)

        # Handle query (substring or regex search)
        if query:
            pattern = None
            if use_regex:
                try:
                    pattern = re.compile(query, re.IGNORECASE)
                except re.error:
                    # Fallback safely to literal escaped regex search
                    pattern = re.compile(re.escape(query), re.IGNORECASE)
            else:
                pattern = re.compile(re.escape(query), re.IGNORECASE)

            query_matches = []
            for idx, line in enumerate(lines):
                if pattern.search(line):
                    query_matches.append(idx)

            if not query_matches and not matched_indices:
                return f"[PromptLens: No lines matched query '{query}' in retrieval payload '{retrieval_id}']"

            for match_idx in query_matches:
                window_start = max(0, match_idx - context_lines)
                window_end = min(total_lines - 1, match_idx + context_lines)
                for idx in range(window_start, window_end + 1):
                    matched_indices.add(idx)

        if not matched_indices:
            return raw_content

        sorted_indices = sorted(list(matched_indices))

        # Build formatted snippet output with line numbers and omission markers
        snippet_lines = []
        min_line = sorted_indices[0] + 1
        max_line = sorted_indices[-1] + 1

        prev_idx = None
        for idx in sorted_indices:
            if prev_idx is not None and idx > prev_idx + 1:
                omitted_count = idx - prev_idx - 1
                snippet_lines.append(f"  ... [{omitted_count} lines omitted (lines {prev_idx+2}-{idx})] ...")
            snippet_lines.append(f"{idx+1:4d} | {lines[idx]}")
            prev_idx = idx

        header = f"[PromptLens Snippet for '{retrieval_id}' (Lines {min_line}-{max_line} of {total_lines})]"
        return header + "\n" + "\n".join(snippet_lines)

    def has(self, retrieval_id: str) -> bool:
        """Checks if a non-expired key exists in the store."""
        return self.get(retrieval_id) is not None

    def cleanup_expired(self) -> int:
        """Purges all expired items from the store. Returns count of purged items."""
        now = time.time()
        expired_keys = [
            key
            for key, item in self._store.items()
            if now - item.created_at > self.ttl_seconds
        ]
        for key in expired_keys:
            del self._store[key]
        return len(expired_keys)

    def size(self) -> int:
        """Returns total active items in store."""
        self.cleanup_expired()
        return len(self._store)

    def clear(self) -> None:
        """Clears all stored items."""
        self._store.clear()


# Shared Global Singleton Instance
_GLOBAL_STORE: Optional[RetrievalStore] = None


def get_global_store(ttl_seconds: int = 3600) -> RetrievalStore:
    """Returns the shared global RetrievalStore instance."""
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None:
        _GLOBAL_STORE = RetrievalStore(ttl_seconds=ttl_seconds)
    return _GLOBAL_STORE
