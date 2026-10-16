import hashlib
import json
import logging
import os
import re
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger("promptlens.store")


@dataclass
class StoreItem:
    content: str
    created_at: float
    retrieval_id: str
    last_accessed: float
    structural_map: Optional[dict] = None


def validate_id(id_str: str) -> bool:
    """Validates that a retrieval ID is safe and conforms to standard formats."""
    if not id_str or not isinstance(id_str, str):
        return False
    # Alphanumeric with underscore or hyphen, 4 to 64 chars
    return bool(re.match(r"^[a-zA-Z0-9_\-]{4,64}$", id_str))


class RetrievalStore:
    """
    Production-grade dual-tier (in-memory LRU cache + transactional SQLite persistence) store
    for uncompressed original data. Provides fast local recovery without re-executing tools,
    cached AST structural indexing, targeted line-range slicing, regex search, and context windows.
    Survives server restarts and multi-worker process scaling with WAL journal mode.
    """

    def __init__(
        self,
        ttl_seconds: int = 1800,
        max_items: int = 500,
        db_path: Optional[str] = None
    ):
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._store: Dict[str, StoreItem] = {}
        self._lock = threading.RLock()
        self.db_path = db_path
        self.backend_type = "sqlite" if self.db_path else "memory"

        if self.db_path:
            self._init_sqlite()

    def _init_sqlite(self) -> None:
        """Initializes the SQLite database with WAL mode and schema."""
        try:
            if self.db_path != ":memory:":
                db_dir = os.path.dirname(self.db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)

            with self._get_connection() as conn:
                if self.db_path != ":memory:":
                    conn.execute("PRAGMA journal_mode=WAL;")
                    conn.execute("PRAGMA synchronous=NORMAL;")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS vault_items (
                        retrieval_id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        last_accessed REAL NOT NULL,
                        structural_map TEXT
                    );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_vault_created ON vault_items(created_at);")
        except Exception as e:
            logger.warning(f"Failed to initialize SQLite vault at {self.db_path}: {e}. Falling back to memory.")
            self.db_path = None
            self.backend_type = "memory"

    @contextmanager
    def _get_connection(self):
        """Creates a thread-safe connection to SQLite with automatic commit and close."""
        if not self.db_path:
            raise RuntimeError("SQLite database path is not configured.")
        conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _build_ast_structural_map(self, content: str) -> dict:
        """Parses content to generate a structural map of symbols and line bounds."""
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

    def _resolve_item(self, retrieval_id: str) -> Optional[StoreItem]:
        """Resolves an item checking memory first, then SQLite, with prefix normalization."""
        if not retrieval_id:
            return None

        with self._lock:
            # 1. Fast path: check in-memory LRU cache
            item = self._store.get(retrieval_id)
            if item is None:
                if retrieval_id.startswith("pl_"):
                    item = self._store.get(retrieval_id[3:])
                else:
                    item = self._store.get(f"pl_{retrieval_id}")

            if item is not None:
                # Check TTL
                if time.time() - item.created_at > self.ttl_seconds:
                    self._store.pop(item.retrieval_id, None)
                    self._store.pop(retrieval_id, None)
                    if self.db_path:
                        try:
                            with self._get_connection() as conn:
                                conn.execute("DELETE FROM vault_items WHERE retrieval_id = ?", (item.retrieval_id,))
                        except Exception:
                            pass
                    return None
                return item

            # 2. Disk path: check SQLite persistent store if configured
            if self.db_path:
                candidates = [retrieval_id]
                if retrieval_id.startswith("pl_"):
                    candidates.append(retrieval_id[3:])
                else:
                    candidates.append(f"pl_{retrieval_id}")

                try:
                    with self._get_connection() as conn:
                        for cand in candidates:
                            row = conn.execute(
                                "SELECT retrieval_id, content, created_at, last_accessed, structural_map FROM vault_items WHERE retrieval_id = ?",
                                (cand,)
                            ).fetchone()
                            if row:
                                now = time.time()
                                if now - row["created_at"] > self.ttl_seconds:
                                    conn.execute("DELETE FROM vault_items WHERE retrieval_id = ?", (cand,))
                                    continue

                                structural_map = None
                                if row["structural_map"]:
                                    try:
                                        structural_map = json.loads(row["structural_map"])
                                    except Exception:
                                        pass

                                item = StoreItem(
                                    content=row["content"],
                                    created_at=row["created_at"],
                                    last_accessed=now,
                                    retrieval_id=row["retrieval_id"],
                                    structural_map=structural_map
                                )
                                # Populate into in-memory cache
                                self._store[row["retrieval_id"]] = item
                                return item
                except Exception as e:
                    logger.error(f"Error reading from SQLite vault for {retrieval_id}: {e}")

        return None

    def save(
        self,
        content: str,
        retrieval_id: Optional[str] = None,
        structural_map: Optional[dict] = None,
    ) -> str:
        """
        Saves original content to the in-memory cache and transactional SQLite store (if enabled).
        Returns unique retrieval_id.
        """
        if not retrieval_id:
            retrieval_id = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]

        if structural_map is None:
            structural_map = self._build_ast_structural_map(content)

        now = time.time()
        item = StoreItem(
            content=content,
            created_at=now,
            last_accessed=now,
            retrieval_id=retrieval_id,
            structural_map=structural_map,
        )

        with self._lock:
            # LRU eviction if memory cache is full
            if len(self._store) >= self.max_items and retrieval_id not in self._store:
                self.cleanup_expired()
                if len(self._store) >= self.max_items and retrieval_id not in self._store:
                    oldest_key = min(self._store.keys(), key=lambda k: self._store[k].last_accessed)
                    del self._store[oldest_key]
                    if self.db_path:
                        try:
                            with self._get_connection() as conn:
                                conn.execute("DELETE FROM vault_items WHERE retrieval_id = ?", (oldest_key,))
                        except Exception:
                            pass

            self._store[retrieval_id] = item

            # Persist to SQLite if configured
            if self.db_path:
                try:
                    s_map_json = json.dumps(structural_map) if structural_map else None
                    with self._get_connection() as conn:
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO vault_items
                            (retrieval_id, content, created_at, last_accessed, structural_map)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (retrieval_id, content, now, now, s_map_json)
                        )
                except Exception as e:
                    logger.error(f"Failed to persist vault item {retrieval_id} to SQLite: {e}")

        return retrieval_id

    def list_items(self) -> list:
        """Returns metadata list of all active non-expired payloads."""
        self.cleanup_expired()
        items = []

        with self._lock:
            if self.db_path:
                try:
                    cutoff = time.time() - self.ttl_seconds
                    with self._get_connection() as conn:
                        rows = conn.execute(
                            """
                            SELECT retrieval_id, content, created_at, last_accessed, structural_map
                            FROM vault_items
                            WHERE created_at >= ?
                            ORDER BY created_at DESC
                            LIMIT ?
                            """,
                            (cutoff, self.max_items)
                        ).fetchall()
                        for r in rows:
                            content = r["content"]
                            s_map = None
                            if r["structural_map"]:
                                try:
                                    s_map = json.loads(r["structural_map"])
                                except Exception:
                                    pass
                            items.append({
                                "retrieval_id": r["retrieval_id"],
                                "created_at": r["created_at"],
                                "last_accessed": r["last_accessed"],
                                "size_bytes": len(content.encode("utf-8")),
                                "preview": content[:150] + ("..." if len(content) > 150 else ""),
                                "full_content": content,
                                "structural_map": s_map,
                            })
                    return items
                except Exception as e:
                    logger.error(f"Failed to list SQLite vault items: {e}")

            # Memory items
            for retrieval_id, item in self._store.items():
                content = item.content
                items.append({
                    "retrieval_id": retrieval_id,
                    "created_at": item.created_at,
                    "last_accessed": item.last_accessed,
                    "size_bytes": len(content.encode("utf-8")),
                    "preview": content[:150] + ("..." if len(content) > 150 else ""),
                    "full_content": content,
                    "structural_map": item.structural_map,
                })
            items.sort(key=lambda x: x["created_at"], reverse=True)
            return items

    def count(self) -> int:
        """Returns total active non-expired item count in cache / store."""
        self.cleanup_expired()
        with self._lock:
            if self.db_path:
                try:
                    cutoff = time.time() - self.ttl_seconds
                    with self._get_connection() as conn:
                        row = conn.execute(
                            "SELECT COUNT(*) as cnt FROM vault_items WHERE created_at >= ?",
                            (cutoff,)
                        ).fetchone()
                        if row:
                            return row["cnt"]
                except Exception as e:
                    logger.error(f"Failed to count SQLite items: {e}")
            return len(self._store)

    def get_structural_map(self, retrieval_id: str) -> Optional[dict]:
        """Returns the cached structural map if item exists."""
        item = self._resolve_item(retrieval_id)
        if not item or (time.time() - item.created_at > self.ttl_seconds):
            return None
        item.last_accessed = time.time()
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
        Retrieves original content or targeted line/query snippets locally by retrieval_id.
        """
        item = self._resolve_item(retrieval_id)
        if not item:
            return None

        # Check TTL
        if time.time() - item.created_at > self.ttl_seconds:
            with self._lock:
                self._store.pop(item.retrieval_id, None)
                self._store.pop(retrieval_id, None)
                if self.db_path:
                    try:
                        with self._get_connection() as conn:
                            conn.execute("DELETE FROM vault_items WHERE retrieval_id = ?", (item.retrieval_id,))
                    except Exception:
                        pass
            return None

        item.last_accessed = time.time()
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
            if use_regex:
                try:
                    pattern = re.compile(query, re.IGNORECASE)
                except re.error:
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

    def retrieve_original(
        self,
        retrieval_id: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        query: Optional[str] = None,
        use_regex: bool = False,
        context_lines: int = 0
    ) -> Optional[str]:
        """Convenience wrapper for get() with start_line and end_line parameters."""
        line_range = None
        if start_line is not None or end_line is not None:
            s = start_line if start_line is not None else 1
            e = end_line if end_line is not None else 999999
            line_range = [s, e]
        return self.get(
            retrieval_id=retrieval_id,
            query=query,
            line_range=line_range,
            use_regex=use_regex,
            context_lines=context_lines
        )

    def has(self, retrieval_id: str) -> bool:
        """Checks if a non-expired key exists in the store."""
        return self.get(retrieval_id) is not None

    def delete(self, retrieval_id: str) -> bool:
        """Deletes a specific payload from memory and persistent store."""
        with self._lock:
            found = False
            if retrieval_id in self._store:
                del self._store[retrieval_id]
                found = True

            if self.db_path:
                try:
                    with self._get_connection() as conn:
                        cursor = conn.execute("DELETE FROM vault_items WHERE retrieval_id = ?", (retrieval_id,))
                        if cursor.rowcount > 0:
                            found = True
                except Exception as e:
                    logger.error(f"Failed to delete item from SQLite: {e}")

            return found

    def cleanup_expired(self) -> int:
        """Purges all expired items from memory and SQLite. Returns count of purged items."""
        now = time.time()
        with self._lock:
            expired_keys = [
                key
                for key, item in list(self._store.items())
                if now - item.created_at > self.ttl_seconds
            ]
            for key in expired_keys:
                del self._store[key]

            if self.db_path:
                try:
                    cutoff = now - self.ttl_seconds
                    with self._get_connection() as conn:
                        conn.execute("DELETE FROM vault_items WHERE created_at < ?", (cutoff,))
                except Exception as e:
                    logger.error(f"Failed to cleanup expired items in SQLite: {e}")

            return len(expired_keys)

    def size(self) -> int:
        """Returns total active items in memory cache (or total in store)."""
        self.cleanup_expired()
        return len(self._store)

    def clear(self) -> None:
        """Clears all stored items from memory and SQLite."""
        with self._lock:
            self._store.clear()
            if self.db_path:
                try:
                    with self._get_connection() as conn:
                        conn.execute("DELETE FROM vault_items")
                except Exception as e:
                    logger.error(f"Failed to clear SQLite vault: {e}")


# Shared Global Singleton Instance
_GLOBAL_STORE: Optional[RetrievalStore] = None


def get_global_store(ttl_seconds: int = 1800, db_path: Optional[str] = None) -> RetrievalStore:
    """Returns the shared global RetrievalStore instance with 30-min default TTL and persistent SQLite backing."""
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None:
        if db_path is None:
            backend = os.getenv("PROMPTLENS_VAULT_BACKEND", "sqlite").lower()
            if backend != "memory":
                db_path = os.getenv("PROMPTLENS_VAULT_DB", os.path.join("data", "vault.db"))
        _GLOBAL_STORE = RetrievalStore(ttl_seconds=ttl_seconds, db_path=db_path)
    return _GLOBAL_STORE
