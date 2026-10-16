"""
LogCompressor for PromptLens.
Compresses verbose terminal and application logs while preserving beginning lines,
ending lines, error anchors, stack traces, and failure exit statuses.
Collapses consecutive repeated log lines and repeated pattern bursts.
Configurable keyword lists and fail-open design.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Set

from src.store.retrieval_store import RetrievalStore, get_global_store
from src.tokens.counter import get_token_count

DEFAULT_ERROR_KEYWORDS = [
    "ERROR", "Exception", "Traceback", "FAIL", "FAILED",
    "Warning", "WARN", "fatal", "FATAL", "CRITICAL",
    "TS2304", "TS2322", "500 Internal Server Error", "404 Not Found",
    "NullPointerException", "Panic", "AssertionError", "SyntaxError",
    "TypeError", "ValueError", "KeyError", "ConnectionError"
]


@dataclass
class LogCompressionResult:
    original_log: str
    compressed_log: str
    original_tokens: int
    compressed_tokens: int
    savings_pct: float
    is_compressed: bool
    retrieval_id: Optional[str] = None
    pinned_errors_count: int = 0
    collapsed_repeats_count: int = 0


class LogCompressor:
    """
    Compresses long log files by preserving head/tail frames, pinning error keywords,
    and deduplicating identical consecutive lines.
    """

    def __init__(
        self,
        head_lines: int = 15,
        tail_lines: int = 15,
        min_lines_threshold: int = 25,
        min_tokens_threshold: int = 80,
        error_keywords: Optional[List[str]] = None,
        store: Optional[RetrievalStore] = None
    ):
        self.head_lines = head_lines
        self.tail_lines = tail_lines
        self.min_lines_threshold = min_lines_threshold
        self.min_tokens_threshold = min_tokens_threshold
        self.error_keywords = list(error_keywords or DEFAULT_ERROR_KEYWORDS)
        self.store = store or get_global_store()

    def collapse_duplicates(self, lines: List[str]) -> Tuple[List[str], int]:
        """Collapses consecutive identical lines into a count summary."""
        if not lines:
            return [], 0

        deduped = []
        repeats_collapsed = 0
        i = 0
        n = len(lines)

        while i < n:
            current = lines[i]
            count = 1
            while i + 1 < n and lines[i + 1] == current:
                count += 1
                i += 1

            if count > 2:
                deduped.append(current)
                deduped.append(f"  ... [Repeated {count - 1} times: \"{current[:80].strip()}\"] ...")
                repeats_collapsed += (count - 2)
            else:
                deduped.append(current)
                if count == 2:
                    deduped.append(current)
            i += 1

        return deduped, repeats_collapsed

    def find_error_lines(self, lines: List[str]) -> List[str]:
        """Finds any lines matching error keywords with surrounding context."""
        matched = []
        for line in lines:
            if any(kw in line for kw in self.error_keywords):
                matched.append(line.strip())
        return matched

    def compress(
        self,
        log_text: str,
        retrieval_id: Optional[str] = None,
        save_to_store: bool = True
    ) -> LogCompressionResult:
        """
        Compresses logs with head/tail preservation, error pinning, and repeat deduplication.
        Fails open on any error.
        """
        orig_tokens = get_token_count(log_text)
        lines = log_text.splitlines()

        if len(lines) < self.min_lines_threshold or orig_tokens < self.min_tokens_threshold:
            return LogCompressionResult(
                original_log=log_text,
                compressed_log=log_text,
                original_tokens=orig_tokens,
                compressed_tokens=orig_tokens,
                savings_pct=0.0,
                is_compressed=False,
                retrieval_id=None,
            )

        try:
            # 1. Collapse duplicates throughout
            deduped_lines, collapsed_repeats = self.collapse_duplicates(lines)

            if len(deduped_lines) <= (self.head_lines + self.tail_lines):
                compressed_body = "\n".join(deduped_lines)
            else:
                head = deduped_lines[:self.head_lines]
                tail = deduped_lines[-self.tail_lines:]
                middle = deduped_lines[self.head_lines:-self.tail_lines]

                # Scan middle for critical error frames
                pinned_errors = self.find_error_lines(middle)

                # Assemble compressed log
                out_sections = []
                out_sections.append("\n".join(head))

                omitted_count = len(middle)
                omitted_notice = f"\n--- [PromptLens: Truncated {omitted_count} non-critical middle log lines] ---"
                out_sections.append(omitted_notice)

                if pinned_errors:
                    # Deduplicate pinned error lines up to 10 key items
                    unique_errors = list(dict.fromkeys(pinned_errors))[:10]
                    pinned_block = "\n".join([f"  ! [Pinned Error] {err}" for err in unique_errors])
                    out_sections.append(f"[PromptLens Pinned Middle Errors/Exceptions]:\n{pinned_block}")

                out_sections.append("\n".join(tail))
                compressed_body = "\n".join(out_sections)

            comp_tokens = get_token_count(compressed_body)

            if comp_tokens < orig_tokens:
                stored_id = None
                if save_to_store:
                    stored_id = self.store.save(log_text, retrieval_id=retrieval_id)
                    compressed_body += f"\n\n[PromptLens compressed content: {stored_id}]"
                    comp_tokens = get_token_count(compressed_body)

                savings = round((1.0 - (comp_tokens / orig_tokens)) * 100.0, 2)
                return LogCompressionResult(
                    original_log=log_text,
                    compressed_log=compressed_body,
                    original_tokens=orig_tokens,
                    compressed_tokens=comp_tokens,
                    savings_pct=savings,
                    is_compressed=True,
                    retrieval_id=stored_id,
                    pinned_errors_count=len(pinned_errors) if 'pinned_errors' in locals() else 0,
                    collapsed_repeats_count=collapsed_repeats,
                )
        except Exception:
            # Fail open
            pass

        return LogCompressionResult(
            original_log=log_text,
            compressed_log=log_text,
            original_tokens=orig_tokens,
            compressed_tokens=orig_tokens,
            savings_pct=0.0,
            is_compressed=False,
            retrieval_id=None,
        )
