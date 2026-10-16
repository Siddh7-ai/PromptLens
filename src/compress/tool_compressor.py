"""
ToolOutputCompressor for PromptLens.
Compresses developer tool outputs (git diffs, terminal commands, database query tables,
compiler outputs, file trees, search/grep results) while preserving exit status,
identifiers, file paths, and failure messages.
"""
import re
from dataclasses import dataclass
from typing import List, Optional

from src.store.retrieval_store import RetrievalStore, get_global_store
from src.tokens.counter import get_token_count


@dataclass
class ToolCompressionResult:
    original_output: str
    compressed_output: str
    original_tokens: int
    compressed_tokens: int
    savings_pct: float
    is_compressed: bool
    retrieval_id: Optional[str] = None
    tool_type: str = "generic"


class ToolOutputCompressor:
    """Specialized compressor for terminal and developer tool outputs."""

    def __init__(
        self,
        min_lines_threshold: int = 20,
        min_tokens_threshold: int = 80,
        store: Optional[RetrievalStore] = None
    ):
        self.min_lines_threshold = min_lines_threshold
        self.min_tokens_threshold = min_tokens_threshold
        self.store = store or get_global_store()

    def detect_tool_type(self, output: str) -> str:
        """Determines category of tool output."""
        if "diff --git" in output or "@@ -" in output or output.startswith("--- a/"):
            return "git_diff"
        if re.search(r"^\|\s*[\w\s_]+\s*\|\s*[\w\s_]+\s*\|", output, re.MULTILINE):
            return "db_table"
        if "npm ERR!" in output or "yarn error" in output or "pip install" in output:
            return "package_manager"
        if "Total tests:" in output or "passed" in output and "failed" in output:
            return "test_runner"
        return "terminal"

    def _compress_git_diff(self, lines: List[str]) -> List[str]:
        """Compresses long git diffs by keeping file headers, hunk declarations, and diff hunks while limiting context lines."""
        out = []
        unchanged_count = 0
        for line in lines:
            if line.startswith(("diff --git", "index ", "--- ", "+++ ", "@@ ")):
                if unchanged_count > 3:
                    out.append(f"  ... [{unchanged_count} unchanged context lines omitted] ...")
                    unchanged_count = 0
                out.append(line)
            elif line.startswith(("+", "-")):
                if unchanged_count > 3:
                    out.append(f"  ... [{unchanged_count} unchanged context lines omitted] ...")
                    unchanged_count = 0
                out.append(line)
            else:
                unchanged_count += 1
                if unchanged_count <= 2:
                    out.append(line)

        if unchanged_count > 3:
            out.append(f"  ... [{unchanged_count} unchanged context lines omitted] ...")
        return out

    def _compress_db_table(self, lines: List[str]) -> List[str]:
        """Compresses large tabular database outputs to header + sample rows + total count."""
        if len(lines) <= 15:
            return lines

        header_lines = lines[:3]
        footer_lines = lines[-2:]
        sample_rows = lines[3:8]
        omitted = len(lines) - len(header_lines) - len(footer_lines) - len(sample_rows)

        out = list(header_lines)
        out.extend(sample_rows)
        out.append(f"| ... [{omitted} tabular data rows omitted for brevity] ... |")
        out.extend(footer_lines)
        return out

    def compress(
        self,
        output_text: str,
        retrieval_id: Optional[str] = None,
        save_to_store: bool = True
    ) -> ToolCompressionResult:
        """Compresses tool outputs preserving command status and key identifiers."""
        orig_tokens = get_token_count(output_text)
        lines = output_text.splitlines()

        if len(lines) < self.min_lines_threshold or orig_tokens < self.min_tokens_threshold:
            return ToolCompressionResult(
                original_output=output_text,
                compressed_output=output_text,
                original_tokens=orig_tokens,
                compressed_tokens=orig_tokens,
                savings_pct=0.0,
                is_compressed=False,
                retrieval_id=None,
                tool_type="generic"
            )

        try:
            tool_type = self.detect_tool_type(output_text)
            if tool_type == "git_diff":
                processed_lines = self._compress_git_diff(lines)
            elif tool_type == "db_table":
                processed_lines = self._compress_db_table(lines)
            else:
                # Generic terminal output: keep first 10, scan for errors, keep last 10
                head = lines[:10]
                tail = lines[-10:]
                middle = lines[10:-10]
                error_lines = [l for l in middle if any(k in l for k in ["Error", "error", "FAIL", "fail", "fatal", "Exit code"])]
                processed_lines = list(head)
                processed_lines.append(f"\n--- [PromptLens: Truncated {len(middle)} terminal lines] ---")
                if error_lines:
                    processed_lines.extend(error_lines[:6])
                processed_lines.extend(tail)

            compressed_body = "\n".join(processed_lines)
            comp_tokens = get_token_count(compressed_body)

            if comp_tokens < orig_tokens:
                stored_id = None
                if save_to_store:
                    stored_id = self.store.save(output_text, retrieval_id=retrieval_id)
                    compressed_body += f"\n\n[PromptLens compressed content: {stored_id}]"
                    comp_tokens = get_token_count(compressed_body)

                savings = round((1.0 - (comp_tokens / orig_tokens)) * 100.0, 2)
                return ToolCompressionResult(
                    original_output=output_text,
                    compressed_output=compressed_body,
                    original_tokens=orig_tokens,
                    compressed_tokens=comp_tokens,
                    savings_pct=savings,
                    is_compressed=True,
                    retrieval_id=stored_id,
                    tool_type=tool_type
                )
        except Exception:
            # Fail open
            pass

        return ToolCompressionResult(
            original_output=output_text,
            compressed_output=output_text,
            original_tokens=orig_tokens,
            compressed_tokens=orig_tokens,
            savings_pct=0.0,
            is_compressed=False,
            retrieval_id=None,
            tool_type="generic"
        )
