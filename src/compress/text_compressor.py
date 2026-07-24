import hashlib
from dataclasses import dataclass
from typing import Any

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


def generate_structural_index(lines: list[str]) -> str:
    """
    Parses code or structured text across Python, JS/TS, Rust, Go, and Markdown
    to build a Table of Contents index mapping line ranges to symbols.
    """
    sections = []
    current_symbol = None
    symbol_start = 1

    symbol_prefixes = (
        "class ", "def ", "async def ", "function ", "async function ",
        "struct ", "impl ", "enum ", "trait ", "func ", "type ",
        "export default ", "export function ", "export class ",
        "# ", "## ", "### "
    )

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith(symbol_prefixes):
            if current_symbol:
                sections.append(f"Lines {symbol_start}-{idx-1}: {current_symbol}")
            symbol_parts = stripped.split(":") if ":" in stripped else [stripped]
            raw_sym = symbol_parts[0].replace("{", "").strip()
            current_symbol = " ".join(raw_sym.split())
            symbol_start = idx

    if current_symbol and len(lines) >= symbol_start:
        sections.append(f"Lines {symbol_start}-{len(lines)}: {current_symbol}")

    if not sections:
        return ""

    index_str = "[PromptLens Structural Index]\n" + "\n".join(f"- {sec}" for sec in sections[:10])
    return index_str


def find_error_anchors(lines: list[str], start_line_offset: int = 1) -> list[tuple[int, str]]:
    """
    Scans lines for error and exception keywords and returns pinned anchor lines
    with accurate 1-indexed line numbers.
    """
    anchors = []
    error_keywords = ("error", "exception", "fail", "warning", "fatal", "traceback", "critical")
    for idx, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in error_keywords):
            anchors.append((start_line_offset + idx, line))
            if len(anchors) >= 10:
                break
    return anchors


def deduplicate_logs(lines: list[str]) -> list[str]:
    """
    Collapses consecutive identical or highly similar log lines.
    """
    if not lines:
        return []

    deduped = []
    prev_line = None
    repeat_count = 0

    for line in lines:
        stripped = line.strip()
        if stripped == prev_line:
            repeat_count += 1
        else:
            if repeat_count > 0:
                deduped.append(f"  ... [x{repeat_count + 1} repeated log lines omitted] ...")
            deduped.append(line)
            prev_line = stripped
            repeat_count = 0

    if repeat_count > 0:
        deduped.append(f"  ... [x{repeat_count + 1} repeated log lines omitted] ...")

    return deduped


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



from src.store.retrieval_store import RetrievalStore, get_global_store


def compress_text(
    text: str,
    head_lines: int = 10,
    tail_lines: int = 10,
    min_token_threshold: int = 50,
    store: Any = None,
) -> TextCompressionResult:
    """
    Compresses non-JSON text outputs (logs, stack traces, file reads, diffs).

    Args:
        text: Raw string content to compress.
        head_lines: Number of lines to preserve at the start of text.
        tail_lines: Number of lines to preserve at the end of text.
        min_token_threshold: Minimum tokens required to trigger truncation.
        store: Optional RetrievalStore instance. Defaults to get_global_store().

    Returns:
        TextCompressionResult object containing compressed string and stats.
    """
    if store is None:
        store = get_global_store()
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

    # Step 1: Run log deduplication
    lines = deduplicate_logs(lines)
    min_required_lines = head_lines + tail_lines + 2

    # Check if lines exceed minimum required lines for head-tail truncation
    if len(lines) <= min_required_lines:
        return TextCompressionResult(
            compressed_str="\n".join(lines),
            retrieval_id=retrieval_id,
            original_tokens=original_tokens,
            compressed_tokens=get_token_count("\n".join(lines)),
            is_compressed=len(lines) < len(text.splitlines()),
            compression_ratio=(1.0 - (get_token_count("\n".join(lines)) / original_tokens)) if original_tokens > 0 else 0.0,
        )

    # Step 2: Generate Structural Index ToC
    toc_index = generate_structural_index(lines)

    # Step 3: Find Error Anchors in Middle Lines
    middle_lines = lines[head_lines:-tail_lines]
    anchors = find_error_anchors(middle_lines, start_line_offset=head_lines + 1)
    anchor_block = ""
    if anchors:
        anchor_lines_str = "\n".join(f"  Line {line_num}: {text_line}" for line_num, text_line in anchors)
        anchor_block = f"\n[PromptLens Pinned Middle Errors/Exceptions]\n{anchor_lines_str}"

    # Check for stack trace specific optimization
    if "Traceback (most recent call last):" in text or "FAILURES" in text or "ERRORS" in text:
        compressed_lines = _compress_stack_trace(lines, retrieval_id)
    else:
        # Standard Head-Tail Truncation with ToC and Anchors
        head = lines[:head_lines]
        tail = lines[-tail_lines:]
        omitted = len(lines) - (head_lines + tail_lines)
        marker = (
            f"--- [PROMPT LENS TRUNCATED {omitted} lines (total: {len(lines)}). "
            f"Use retrieve_original('{retrieval_id}') for full text] ---"
        )
        compressed_lines = head + [marker] + tail

    prefix = (toc_index + "\n\n") if toc_index else ""
    suffix = (anchor_block + "\n") if anchor_block else ""

    compressed_str = prefix + "\n".join(compressed_lines) + suffix
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

    if store:
        store.save(text, retrieval_id)

    return TextCompressionResult(
        compressed_str=compressed_str,
        retrieval_id=retrieval_id,
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        is_compressed=True,
        compression_ratio=ratio,
    )
