import hashlib
from dataclasses import dataclass

import tiktoken

ENCODING_NAME = "cl100k_base"


@dataclass
class TextCompressionResult:
    compressed_str: str
    retrieval_id: str
    original_tokens: int
    compressed_tokens: int
    is_compressed: bool
    compression_ratio: float  # e.g., 0.60 means 60% reduction in tokens


def get_token_count(text: str) -> int:
    """Utility to count tokens using tiktoken (cl100k_base)."""
    try:
        encoding = tiktoken.get_encoding(ENCODING_NAME)
        return len(encoding.encode(text))
    except Exception:
        return len(text.split())


def _compress_stack_trace(lines: list[str], retrieval_id: str) -> list[str]:
    """
    Compresses Python stack traces or pytest failure outputs by keeping
    the initial traceback header, top 4 lines, bottom 4 lines, and error line.
    """
    if len(lines) <= 12:
        return lines

    head = lines[:4]
    tail = lines[-4:]
    omitted = len(lines) - 8

    marker = f"--- [PROMPT LENS TRUNCATED {omitted} stack trace lines. Use retrieve_original('{retrieval_id}') for full log] ---"
    return head + [marker] + tail


def compress_text(
    text: str,
    head_lines: int = 10,
    tail_lines: int = 10,
    min_token_threshold: int = 50,
) -> TextCompressionResult:
    """
    Compresses non-JSON text outputs (logs, stack traces, file reads, diffs).

    Args:
        text: Raw string content to compress.
        head_lines: Number of lines to preserve at the start of text.
        tail_lines: Number of lines to preserve at the end of text.
        min_token_threshold: Minimum tokens required to trigger truncation.

    Returns:
        TextCompressionResult object containing compressed string and stats.
    """
    original_tokens = get_token_count(text)
    retrieval_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

    # Small text below token threshold
    if original_tokens < min_token_threshold:
        return TextCompressionResult(
            compressed_str=text,
            retrieval_id=retrieval_id,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            is_compressed=False,
            compression_ratio=0.0,
        )

    lines = text.splitlines()
    min_required_lines = head_lines + tail_lines + 2

    # Check if lines exceed minimum required lines for head-tail truncation
    if len(lines) <= min_required_lines:
        return TextCompressionResult(
            compressed_str=text,
            retrieval_id=retrieval_id,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            is_compressed=False,
            compression_ratio=0.0,
        )

    # Check for stack trace specific optimization
    if "Traceback (most recent call last):" in text or "FAILURES" in text or "ERRORS" in text:
        compressed_lines = _compress_stack_trace(lines, retrieval_id)
    else:
        # Standard Head-Tail Truncation
        head = lines[:head_lines]
        tail = lines[-tail_lines:]
        omitted = len(lines) - (head_lines + tail_lines)
        marker = (
            f"--- [PROMPT LENS TRUNCATED {omitted} lines (total: {len(lines)}). "
            f"Use retrieve_original('{retrieval_id}') for full text] ---"
        )
        compressed_lines = head + [marker] + tail

    compressed_str = "\n".join(compressed_lines)
    compressed_tokens = get_token_count(compressed_str)

    if compressed_tokens >= original_tokens:
        return TextCompressionResult(
            compressed_str=text,
            retrieval_id=retrieval_id,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            is_compressed=False,
            compression_ratio=0.0,
        )

    ratio = round(1.0 - (compressed_tokens / original_tokens), 4)

    return TextCompressionResult(
        compressed_str=compressed_str,
        retrieval_id=retrieval_id,
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        is_compressed=True,
        compression_ratio=ratio,
    )
