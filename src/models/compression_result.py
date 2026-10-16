"""
Core Models and Data Structures for PromptLens Context Compression Pipeline.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ContentType(str, Enum):
    TEXT = "TEXT"
    CODE = "CODE"
    JSON = "JSON"
    LOG = "LOG"
    TOOL_OUTPUT = "TOOL_OUTPUT"
    UNKNOWN = "UNKNOWN"


class ContentAction(str, Enum):
    PRESERVE = "PRESERVE"
    COMPRESS = "COMPRESS"
    SKIP = "SKIP"


@dataclass
class PriorityConfig:
    """Configurable priority scores for content classification."""
    user_prompt: int = 100
    system_instruction: int = 100
    error_information: int = 95
    current_code: int = 90
    tool_result: int = 70
    relevant_history: int = 70
    old_conversation: int = 50
    repeated_logs: int = 20
    redundant_content: int = 10


DEFAULT_PRIORITIES = PriorityConfig()


@dataclass
class CompressionItem:
    """Represents a classified chunk of content within a prompt/request."""
    original_content: str
    compressed_content: str
    content_type: ContentType
    action: ContentAction
    priority: int
    original_tokens: int
    compressed_tokens: int
    tokens_saved: int
    retrieval_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def savings_pct(self) -> float:
        if self.original_tokens <= 0:
            return 0.0
        return round((self.tokens_saved / self.original_tokens) * 100.0, 2)


@dataclass
class CompressionReport:
    """
    Standardized compression report detailing token savings, processing metrics,
    breakdowns by content type, and debug before/after summaries.
    """
    original_tokens: int
    compressed_tokens: int
    tokens_saved: int
    compression_ratio: float
    savings_percentage: float
    items_processed: int
    items_compressed: int
    items_preserved: int
    items_skipped: int
    compression_time_ms: float
    breakdown_by_type: Dict[str, Dict[str, int]] = field(default_factory=dict)
    retrieval_ids: List[str] = field(default_factory=list)

    def format_debug_summary(self) -> str:
        """Generates before/after debug mode text output."""
        lines = [
            "=== ORIGINAL ===",
            f"{self.original_tokens:,} tokens",
            "",
            "=== COMPRESSED ===",
            f"{self.compressed_tokens:,} tokens",
            "",
            "=== SAVINGS ===",
            f"{self.tokens_saved:,} tokens",
            f"{self.savings_percentage:.1f}%",
            "",
            "=== BREAKDOWN ==="
        ]
        for ctype, stats in self.breakdown_by_type.items():
            orig = stats.get("original", 0)
            comp = stats.get("compressed", 0)
            lines.append(f"{ctype.capitalize():<12}: {orig:>7,} → {comp:>7,}")
        return "\n".join(lines)


@dataclass
class CompressionResult:
    """Final output of the compression pipeline for an AI request."""
    compressed_payload: Any
    report: CompressionReport
    is_compressed: bool
    retrieval_ids: List[str] = field(default_factory=list)
