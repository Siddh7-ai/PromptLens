"""
Content Router for PromptLens.
Inspects payload blocks, identifies content type, and dispatches to specialized compressors
with fail-open error handling and configurable optimization thresholds.
"""
import enum
import json
import re
from dataclasses import dataclass
from typing import Optional, Any

from src.compress.json_compressor import compress_json, JSONCompressionResult
from src.compress.search_compressor import compress_search_results, is_search_or_grep_output
from src.compress.text_compressor import compress_text, TextCompressionResult
from src.store.retrieval_store import get_global_store
from src.utils.token_utils import get_token_count


class ContentType(str, enum.Enum):
    JSON = "json"
    CODE = "code"
    LOGS = "logs"
    SEARCH = "search"
    DIFF = "diff"
    TEXT = "text"


@dataclass
class RouterResult:
    content_type: ContentType
    original_content: str
    compressed_content: str
    original_tokens: int
    compressed_tokens: int
    savings_pct: float
    is_compressed: bool
    retrieval_id: Optional[str] = None


# Code indicators
_CODE_KEYWORDS = (
    "import ", "from ", "def ", "class ", "function ", "const ", "let ", "var ",
    "async def ", "public ", "private ", "protected ", "return ", "#include", "package ", "func "
)

# Diff indicators
_DIFF_PATTERNS = ("diff --git", "--- a/", "+++ b/", "@@ -", "Index: ")

# Log indicators
_LOG_KEYWORDS = (
    "Traceback (most recent call last):", "FAILURES", "ERRORS", "=== FAILURES ===",
    "[ERROR]", "[WARN]", "[INFO]", "[DEBUG]", "Exception in thread", "Error:", "NullPointerException"
)


class ContentRouter:
    """
    Intelligent Content Router that detects content type and dispatches to
    specialized compressors while preserving small/non-redundant content.
    """

    def __init__(
        self,
        min_bytes_threshold: int = 250,
        min_tokens_threshold: int = 80,
        retention_ttl_seconds: int = 1800
    ):
        self.min_bytes_threshold = min_bytes_threshold
        self.min_tokens_threshold = min_tokens_threshold
        self.retrieval_store = get_global_store(ttl_seconds=retention_ttl_seconds)

    def detect_content_type(self, content: str) -> ContentType:
        """Determines the primary content type of the given text block."""
        stripped = content.strip()

        # 1. Check for JSON
        if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, (dict, list)):
                    return ContentType.JSON
            except Exception:
                pass

        # 2. Check for Git Diff / Patches
        if any(pattern in stripped for pattern in _DIFF_PATTERNS):
            return ContentType.DIFF

        # 3. Check for Search / Grep results
        if is_search_or_grep_output(stripped):
            return ContentType.SEARCH

        # 4. Check for Logs / Stack Traces
        if any(kw in stripped for kw in _LOG_KEYWORDS) or "pytest" in stripped.lower():
            return ContentType.LOGS

        # 5. Check for Code
        lines = stripped.splitlines()
        code_matches = sum(1 for line in lines[:30] if line.strip().startswith(_CODE_KEYWORDS))
        if code_matches >= 3 or ("```" in stripped and len(lines) > 5):
            return ContentType.CODE

        return ContentType.TEXT

    def is_worth_optimizing(self, content: str) -> bool:
        """
        Determines if payload is large enough and sufficiently complex to optimize.
        Passes through small/trivial content without compressor overhead.
        """
        if not content or len(content.strip()) < self.min_bytes_threshold:
            return False

        token_count = get_token_count(content)
        if token_count < self.min_tokens_threshold:
            return False

        # Don't optimize already compressed blocks
        if "[PromptLens: Content compressed" in content or "--- [PROMPT LENS TRUNCATED" in content:
            return False

        return True

    def route_and_compress(
        self,
        content: str,
        content_type: Optional[ContentType] = None,
        head_lines: int = 10,
        tail_lines: int = 10,
        max_json_array: int = 1,
        save_to_ccr: bool = True
    ) -> RouterResult:
        """
        Routes content to the appropriate specialized compressor with fail-open safety.
        """
        orig_tokens = get_token_count(content)

        # Threshold check: pass-through if content is small or not worth optimizing
        if not self.is_worth_optimizing(content):
            return RouterResult(
                content_type=content_type or ContentType.TEXT,
                original_content=content,
                compressed_content=content,
                original_tokens=orig_tokens,
                compressed_tokens=orig_tokens,
                savings_pct=0.0,
                is_compressed=False,
                retrieval_id=None
            )

        if content_type is None:
            content_type = self.detect_content_type(content)

        try:
            # 1. JSON Routing
            if content_type == ContentType.JSON:
                json_res = compress_json(
                    content,
                    max_array_items=max_json_array,
                    min_token_threshold=self.min_tokens_threshold,
                    store=self.retrieval_store if save_to_ccr else None
                )
                if json_res.is_compressed and json_res.compressed_tokens < orig_tokens:
                    stored_id = json_res.retrieval_id if save_to_ccr else None
                    savings_pct_str = f"{(json_res.compression_ratio * 100):.1f}%"
                    notice = f"\n\n[PromptLens: JSON content compressed ({savings_pct_str} saved). Original ID: {stored_id}. Use retrieve_original(id=\"{stored_id}\")]" if stored_id else ""
                    candidate = json_res.compressed_str + notice
                    c_tokens = get_token_count(candidate)
                    if c_tokens < orig_tokens:
                        savings = round((1.0 - (c_tokens / orig_tokens)) * 100, 2)
                        return RouterResult(
                            content_type=ContentType.JSON,
                            original_content=content,
                            compressed_content=candidate,
                            original_tokens=orig_tokens,
                            compressed_tokens=c_tokens,
                            savings_pct=savings,
                            is_compressed=True,
                            retrieval_id=stored_id
                        )

            # 2. Search / Grep Routing
            elif content_type == ContentType.SEARCH:
                search_res = compress_search_results(content, min_token_threshold=self.min_tokens_threshold)
                if search_res.is_compressed and search_res.compressed_tokens < orig_tokens:
                    stored_id = self.retrieval_store.save(content) if save_to_ccr else None
                    notice = f"\n\n[PromptLens: Search results compressed (saved {round(search_res.compression_ratio * 100, 1)}%). Original ID: {stored_id}. Use retrieve_original(id=\"{stored_id}\")]" if stored_id else ""
                    candidate = search_res.compressed_str + notice
                    c_tokens = get_token_count(candidate)
                    if c_tokens < orig_tokens:
                        savings = round((1.0 - (c_tokens / orig_tokens)) * 100, 2)
                        return RouterResult(
                            content_type=ContentType.SEARCH,
                            original_content=content,
                            compressed_content=candidate,
                            original_tokens=orig_tokens,
                            compressed_tokens=c_tokens,
                            savings_pct=savings,
                            is_compressed=True,
                            retrieval_id=stored_id
                        )

            # 3. Logs, Code, Diff, or Plain Text Routing via TextCompressor
            text_res = compress_text(
                content,
                head_lines=head_lines,
                tail_lines=tail_lines,
                min_token_threshold=self.min_tokens_threshold
            )
            if text_res.is_compressed and text_res.compressed_tokens < orig_tokens:
                stored_id = self.retrieval_store.save(content) if save_to_ccr else None
                savings_pct_str = f"{(text_res.compression_ratio * 100):.1f}%"
                notice = f"\n\n[PromptLens: Content compressed ({savings_pct_str} saved). Original ID: {stored_id}. Use retrieve_original(id=\"{stored_id}\")]" if stored_id else ""
                candidate = text_res.compressed_str + notice
                c_tokens = get_token_count(candidate)
                if c_tokens < orig_tokens:
                    savings = round((1.0 - (c_tokens / orig_tokens)) * 100, 2)
                    return RouterResult(
                        content_type=content_type,
                        original_content=content,
                        compressed_content=candidate,
                        original_tokens=orig_tokens,
                        compressed_tokens=c_tokens,
                        savings_pct=savings,
                        is_compressed=True,
                        retrieval_id=stored_id
                    )

        except Exception:
            # Fail-open guarantee: on any parsing or compression exception, return original text untouched
            pass

        return RouterResult(
            content_type=content_type,
            original_content=content,
            compressed_content=content,
            original_tokens=orig_tokens,
            compressed_tokens=orig_tokens,
            savings_pct=0.0,
            is_compressed=False,
            retrieval_id=None
        )


_GLOBAL_ROUTER: Optional[ContentRouter] = None


def get_global_router(
    min_bytes_threshold: int = 250,
    min_tokens_threshold: int = 80,
    retention_ttl_seconds: int = 1800
) -> ContentRouter:
    """Singleton getter for the global ContentRouter."""
    global _GLOBAL_ROUTER
    if _GLOBAL_ROUTER is None:
        _GLOBAL_ROUTER = ContentRouter(
            min_bytes_threshold=min_bytes_threshold,
            min_tokens_threshold=min_tokens_threshold,
            retention_ttl_seconds=retention_ttl_seconds
        )
    return _GLOBAL_ROUTER
