"""
Grep & File Search Result Compressor for PromptLens.
Compacts large grep, ripgrep, and file-search outputs:
- Groups hits by file path
- Preserves matching line numbers and snippets
- Omits long streaks of non-matching context
"""
import re
from dataclasses import dataclass
from src.utils.token_utils import get_token_count


@dataclass
class SearchCompressionResult:
    compressed_str: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    is_compressed: bool
    total_matches: int = 0
    file_count: int = 0


# Common grep/ripgrep output line patterns:
# filepath:linenum:linecontent or filepath-linenum-linecontent
_GREP_LINE_REGEX = re.compile(r"^([a-zA-Z0-9_\-./\\]+?)[:\-]([0-9]+)[:\-](.*)$")


def is_search_or_grep_output(text: str) -> bool:
    """Detect if content is primarily grep / ripgrep / file search results."""
    lines = text.strip().splitlines()
    if len(lines) < 5:
        return False

    grep_matches = 0
    for line in lines[:30]:
        if _GREP_LINE_REGEX.match(line.strip()):
            grep_matches += 1

    return (grep_matches / min(len(lines), 30)) >= 0.4


def compress_search_results(
    content: str,
    max_matches_per_file: int = 15,
    max_total_matches: int = 60,
    min_token_threshold: int = 80
) -> SearchCompressionResult:
    """
    Compresses grep/search results by grouping by file and capping excessive matches.
    """
    orig_tokens = get_token_count(content)
    lines = content.splitlines()

    if orig_tokens < min_token_threshold or len(lines) <= 10:
        return SearchCompressionResult(
            compressed_str=content,
            original_tokens=orig_tokens,
            compressed_tokens=orig_tokens,
            compression_ratio=0.0,
            is_compressed=False,
            total_matches=len(lines),
            file_count=1
        )

    files_map: dict[str, list[tuple[int, str]]] = {}
    unmatched_lines: list[str] = []
    total_matches = 0

    for line in lines:
        match = _GREP_LINE_REGEX.match(line.strip())
        if match:
            fpath, lnum_str, text = match.groups()
            lnum = int(lnum_str)
            if fpath not in files_map:
                files_map[fpath] = []
            files_map[fpath].append((lnum, text))
            total_matches += 1
        else:
            if line.strip():
                unmatched_lines.append(line)

    if not files_map:
        return SearchCompressionResult(
            compressed_str=content,
            original_tokens=orig_tokens,
            compressed_tokens=orig_tokens,
            compression_ratio=0.0,
            is_compressed=False,
            total_matches=0,
            file_count=0
        )

    output_blocks: list[str] = []
    output_blocks.append(f"[PromptLens Search Results: {total_matches} matches across {len(files_map)} files]")

    emitted_matches = 0
    for fpath, matches in files_map.items():
        if emitted_matches >= max_total_matches:
            remaining_files = len(files_map) - len(output_blocks) + 1
            output_blocks.append(f"\n... [{remaining_files} more matching files omitted] ...")
            break

        output_blocks.append(f"\n📄 {fpath} ({len(matches)} matches):")
        
        shown_matches = matches[:max_matches_per_file]
        for lnum, text in shown_matches:
            output_blocks.append(f"  L{lnum}: {text.strip()}")
            emitted_matches += 1

        if len(matches) > max_matches_per_file:
            omitted = len(matches) - max_matches_per_file
            output_blocks.append(f"  ... [+{omitted} more matches in this file omitted] ...")

    compressed_str = "\n".join(output_blocks)
    compressed_tokens = get_token_count(compressed_str)

    if compressed_tokens < orig_tokens:
        ratio = round(1.0 - (compressed_tokens / orig_tokens), 4)
        return SearchCompressionResult(
            compressed_str=compressed_str,
            original_tokens=orig_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=ratio,
            is_compressed=True,
            total_matches=total_matches,
            file_count=len(files_map)
        )

    return SearchCompressionResult(
        compressed_str=content,
        original_tokens=orig_tokens,
        compressed_tokens=orig_tokens,
        compression_ratio=0.0,
        is_compressed=False,
        total_matches=total_matches,
        file_count=len(files_map)
    )
