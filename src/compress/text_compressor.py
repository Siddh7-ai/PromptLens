import hashlib
import re
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


def is_log_or_build_output(lines: list[str]) -> bool:
    """
    Detects if lines represent terminal logs, build logs, stack traces, or test outputs
    where a Structural Index ToC should NOT be generated.
    """
    log_indicators = (
        "npm ", "yarn ", "pnpm ", "pip ", "docker ", "cargo ", "pytest ", "vite ", "webpack ", "tsc ",
        "[ERROR]", "[WARN]", "[INFO]", "[DEBUG]", "[WARNING]", "ERROR:", "WARNING:", "WARN:",
        "Traceback (most recent call last):", "FAILURES", "ERRORS", "Failed to compile",
        "compilation failed", "Exit status", "Exit code", "dist/assets/", "modules transformed"
    )
    matches = 0
    for line in lines[:30]:
        stripped = line.strip()
        # Check explicit log markers or timestamp prefixes
        if any(ind in stripped for ind in log_indicators) or re.match(r'^\s*\[?\d{2,4}[-/:T\s]\d{2}:\d{2}:?\d{2}', stripped):
            matches += 1
        # Code snippet line gutters in compiler error outputs e.g. "27 | userId: string;"
        elif re.match(r'^\s*\d+\s*\|', stripped):
            matches += 1
        # TypeScript error format e.g. "error TS2304:" or "TS2304:"
        elif re.search(r'\b(?:error\s+)?TS\d{4,5}\b', stripped, re.IGNORECASE):
            matches += 1

    return matches >= 2


def generate_structural_index(lines: list[str], max_entries: int = 35) -> str:
    """
    Parses code or structured documentation across Python, JS/TS, Rust, Go, Java, C/C++, SQL,
    and Markdown to generate a Table of Contents. Excludes build logs and unstructured text.
    """
    if is_log_or_build_output(lines):
        return ""

    sections = []
    current_symbol = None
    symbol_start = 1

    symbol_prefixes = (
        "class ", "def ", "async def ", "function ", "async function ",
        "struct ", "impl ", "enum ", "trait ", "func ", "type ", "interface ",
        "export default ", "export function ", "export class ", "export interface ", "export type ",
        "public ", "private ", "protected ", "static ", "void ",
        "SELECT ", "CREATE TABLE ", "INSERT INTO ", "UPDATE ", "DELETE FROM ",
        "## ", "### ", "#### "
    )

    # Generic pattern matching for headers, questions Q1..Q100, Markdown headings (not inline code comments)
    generic_pattern = re.compile(
        r'^(?:#{2,4}\s+|Q\d+[:\s]|SECTION\s+\d+|###?\s+Q)',
        re.IGNORECASE
    )

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip log output lines or compiler error snippet line gutters e.g. "27 | userId: string;"
        if re.match(r'^\s*\d+\s*\|', stripped):
            continue

        # Single '#' only matches if it's a top-level Markdown title, not a code comment
        is_markdown_title = stripped.startswith("# ") and not any(kw in stripped for kw in ("=", "(", ":", "import ", "from "))
        is_match = stripped.startswith(symbol_prefixes) or is_markdown_title or bool(generic_pattern.match(stripped))

        if is_match:
            if current_symbol:
                sections.append(f"Lines {symbol_start}-{idx-1}: {current_symbol}")
            symbol_parts = stripped.split(":") if ":" in stripped else [stripped]
            raw_sym = symbol_parts[0].replace("{", "").strip()
            current_symbol = " ".join(raw_sym.split())[:50]
            symbol_start = idx

    if current_symbol and len(lines) >= symbol_start:
        sections.append(f"Lines {symbol_start}-{len(lines)}: {current_symbol}")

    if not sections:
        return ""

    index_str = "[PromptLens Structural Index]\n" + "\n".join(f"- {sec}" for sec in sections[:max_entries])
    return index_str


def find_error_anchors(lines: list[str], start_line_offset: int = 1) -> list[tuple[int, str]]:
    """
    Scans lines for genuine error and exception keywords and returns pinned anchor lines
    with accurate 1-indexed line numbers. Excludes routine warnings and deprecation logs.
    """
    anchors = []
    error_keywords = (
        "exception", "fatal", "traceback",
        "keyerror", "valueerror", "typeerror", "assertionerror", "runtimeerror",
        "attributeerror", "syntaxerror", "nameerror", "indexerror", "importerror",
        "modulenotfounderror", "referenceerror", "filenotfounderror", "permissionerror"
    )

    for idx, line in enumerate(lines):
        # Strip timestamps e.g. "[14:20:04]" or "14:20:04"
        line_no_ts = re.sub(r'^\s*(?:\[?\d{2,4}[-/:T\s]\d{2}:\d{2}:?\d{2}(?:\.\d+)?Z?\]?\s*|\[?\d{2}:\d{2}:\d{2}\]?\s*)', '', line).strip()

        # Strip common log prefixes (e.g. "npm error", "npm WARN", "[ERROR]", "[WARN]")
        clean_line = re.sub(r'^(?:npm error|npm WARN|yarn error|yarn WARN|\[ERROR\]|\[WARN\]|\[WARNING\]|\[INFO\]|\[DEBUG\]|ERROR:|WARNING:|WARN:)\s*', '', line_no_ts, flags=re.IGNORECASE).strip()
        clean_lower = clean_line.lower()

        # Check if this line is a warning or deprecation line
        is_warning = (
            "deprecationwarning" in clean_lower or
            clean_lower.startswith("warn ") or clean_lower.startswith("warning:") or clean_lower.startswith("warn:") or
            bool(re.search(r'\b(?:warn|warning|deprecation|deprecationwarning)\b', clean_lower))
        )

        # Check if line contains an explicit error signal or code
        has_explicit_error_code = bool(re.search(
            r'\b(?:error\s+)?TS\d{4,5}\b|\bTypeError\b|\bSyntaxError\b|\bKeyError\b|\bValueError\b|\bAssertionError\b|\bRuntimeError\b|\bAttributeError\b|\bNameError\b|\bIndexError\b|\bFailed to compile\b|\bFAILURES\b|\b\[ERROR\]\b|\bnpm error\b|\bERR_\w+\b',
            line,
            re.IGNORECASE
        ))

        # Skip routine deprecation warnings or informational warning lines unless they contain an explicit error code
        if is_warning and not has_explicit_error_code:
            continue

        is_error = (
            any(kw in clean_lower for kw in error_keywords) or
            bool(re.search(r'\b\w+(?:Error|Exception)\b', clean_line, re.IGNORECASE)) or
            bool(re.search(
                r'\btype\s+error\b|\bsyntax\s+error\b|\bcannot\s+find\s+name\b|\bis\s+not\s+assignable\b|\bdoes\s+not\s+exist\s+on\s+type\b|\bcannot\s+find\s+module\b|\bhas\s+no\s+exported\s+member\b|\bfailed\s+to\s+compile\b|\bcompilation\s+failed\b',
                clean_line,
                re.IGNORECASE
            )) or
            bool(re.search(r'\b(?:error\s+)?TS\d{4,5}\b', clean_line, re.IGNORECASE)) or
            bool(re.search(r'\b(?:error\s+TS\d+|FAILED|FAILURES)\b', clean_line, re.IGNORECASE))
        )

        if is_error:
            anchors.append((start_line_offset + idx, line))

    # Prioritize specific error lines over generic header lines if anchors exceed limit (max 6 anchors)
    if len(anchors) > 6:
        specific_anchors = [
            a for a in anchors
            if re.search(r'\b(?:error\s+)?TS\d{4,5}\b|\b\w+(?:Error|Exception)\b|\bcannot\s+find\b|\bis\s+not\s+assignable\b', a[1], re.IGNORECASE)
        ]
        if len(specific_anchors) >= 2:
            anchors = specific_anchors[:6]
        else:
            # Combine generic headers + specific errors up to 6
            anchors = anchors[:6]
    else:
        anchors = anchors[:6]

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


def _compress_stack_trace(lines: list[str], retrieval_id: str, anchor_block: str = "") -> list[str]:
    """
    Compresses Python stack traces or pytest failure outputs by keeping
    the initial traceback header, bottom 3 lines, and pinned error anchors.
    """
    if len(lines) <= 6:
        return lines

    head = lines[:2]
    tail = lines[-3:]
    omitted = len(lines) - 5

    marker = f"--- [PromptLens Truncated {omitted} lines. ID: {retrieval_id}] ---"
    middle = [marker]
    if anchor_block:
        middle.append(anchor_block.strip())
    return head + middle + tail


from src.store.retrieval_store import RetrievalStore, get_global_store


def estimate_duplicate_line_ratio(text: str) -> float:
    """Calculates the ratio of duplicated lines or repetitive prefix lines to total non-empty lines."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return 0.0
    unique_lines = set(lines)
    exact_ratio = (len(lines) - len(unique_lines)) / len(lines)

    # Check prefix duplication (e.g. "npm error ", "[DEBUG]", timestamps)
    prefixes = [line.split()[0] if line.split() else "" for line in lines]
    unique_prefixes = set(p for p in prefixes if p)
    prefix_ratio = (len(lines) - len(unique_prefixes)) / len(lines) if len(lines) > 3 else 0.0

    return max(exact_ratio, prefix_ratio)


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

    # Adaptive threshold & sizing: if duplicate line ratio >= 0.25 (e.g., repeated npm build errors/warnings), lower token threshold & head/tail line counts
    duplicate_ratio = estimate_duplicate_line_ratio(text)
    effective_threshold = min_token_threshold
    effective_head = head_lines
    effective_tail = tail_lines

    if duplicate_ratio >= 0.25:
        effective_threshold = max(30, int(min_token_threshold * 0.4))
        effective_head = min(4, head_lines)
        effective_tail = min(4, tail_lines)

    # Small text below adaptive token threshold
    if original_tokens < effective_threshold:
        return TextCompressionResult(
            compressed_str=text,
            retrieval_id=retrieval_id,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            is_compressed=False,
            compression_ratio=0.0,
        )

    # Normalize double-newline padding from rich web editors (Lexical / ProseMirror)
    clean_text = re.sub(r"(\r?\n\s*){2,}", "\n", text).strip()
    lines = clean_text.splitlines()

    # Step 1: Run log deduplication
    lines = deduplicate_logs(lines)

    # Adaptive head/tail sizing for shorter inputs
    if duplicate_ratio < 0.25 and len(lines) < (head_lines + tail_lines + 5) and len(lines) >= 10:
        effective_head = max(2, len(lines) // 4)
        effective_tail = max(2, len(lines) // 4)

    min_required_lines = effective_head + effective_tail + 1

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

    # Step 2: Generate Structural Index ToC for structured text / code (>= 15 lines)
    toc_index = generate_structural_index(lines) if len(lines) >= 15 else ""

    # Step 3: Find Error Anchors in Middle Lines
    middle_lines = lines[effective_head:-effective_tail]
    anchors = find_error_anchors(middle_lines, start_line_offset=effective_head + 1)
    anchor_block = ""
    if anchors:
        anchor_lines_str = "\n".join(f"  Line {line_num}: {text_line}" for line_num, text_line in anchors)
        anchor_block = f"\n[PromptLens Pinned Middle Errors/Exceptions]\n{anchor_lines_str}"

    # Check for stack trace specific optimization
    if "Traceback (most recent call last):" in text or "FAILURES" in text or "ERRORS" in text:
        compressed_lines = _compress_stack_trace(lines, retrieval_id, anchor_block)
        compressed_str = "\n".join(compressed_lines)
    else:
        # Standard Head-Tail Truncation with ToC and Anchors
        head = lines[:effective_head]
        tail = lines[-effective_tail:]
        omitted = len(lines) - (effective_head + effective_tail)
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
