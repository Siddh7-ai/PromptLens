"""
ContentRouter for PromptLens.
Deterministically detects content type (TEXT, CODE, JSON, LOG, TOOL_OUTPUT, UNKNOWN)
and assigns action (PRESERVE, COMPRESS, SKIP) and priority scores without LLM dependencies.
"""
import json
import re
from typing import Optional, Tuple

from src.models.compression_result import (
    ContentType,
    ContentAction,
    PriorityConfig,
    DEFAULT_PRIORITIES,
)
from src.tokens.counter import get_token_count

# Code indicators
_CODE_KEYWORDS = (
    "import ", "from ", "def ", "class ", "function ", "const ", "let ", "var ",
    "async def ", "public ", "private ", "protected ", "return ", "#include",
    "package ", "func ", "interface ", "struct ", "@Override", "std::"
)

# Diff / tool indicators
_DIFF_PATTERNS = ("diff --git", "--- a/", "+++ b/", "@@ -", "Index: ")

# Log indicators
_LOG_KEYWORDS = (
    "Traceback (most recent call last):", "FAILURES", "ERRORS", "=== FAILURES ===",
    "[ERROR]", "[WARN]", "[INFO]", "[DEBUG]", "Exception in thread", "Error:",
    "NullPointerException", "npm ERR!", "TypeError:", "ValueError:", "AssertionError:"
)


class ContentRouter:
    """
    Fast, deterministic router identifying content types and deciding optimization actions.
    """

    def __init__(
        self,
        min_tokens_threshold: int = 50,
        priorities: Optional[PriorityConfig] = None
    ):
        self.min_tokens_threshold = min_tokens_threshold
        self.priorities = priorities or DEFAULT_PRIORITIES

    def detect(self, content: str) -> ContentType:
        """
        Fast deterministic detection of content type:
        JSON, CODE, LOG, TOOL_OUTPUT, TEXT, UNKNOWN.
        """
        if not content or not content.strip():
            return ContentType.UNKNOWN

        stripped = content.strip()

        # 1. JSON: begins with { or [ and valid json
        if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, (dict, list)):
                    return ContentType.JSON
            except Exception:
                pass

        # 2. Tool output / Diffs
        if any(p in stripped for p in _DIFF_PATTERNS):
            return ContentType.TOOL_OUTPUT

        # 3. Terminal Logs & Stack Traces
        if any(kw in stripped for kw in _LOG_KEYWORDS) or "pytest" in stripped.lower():
            return ContentType.LOG

        # 4. Code detection across Python, JS, TS, Java, C++
        lines = stripped.splitlines()
        code_matches = sum(1 for line in lines[:30] if any(line.strip().startswith(kw) for kw in _CODE_KEYWORDS))
        if code_matches >= 2 or ("```" in stripped and len(lines) > 5):
            return ContentType.CODE

        # 5. Tool output fallback for table/grep
        if stripped.startswith("|") and stripped.endswith("|"):
            return ContentType.TOOL_OUTPUT

        # 6. Default to standard Text prose
        return ContentType.TEXT

    def classify_action(
        self,
        content: str,
        role: str = "user",
        is_latest_user_prompt: bool = False,
        is_system_instruction: bool = False,
        content_type: Optional[ContentType] = None
    ) -> Tuple[ContentAction, int]:
        """
        Classifies content into PRESERVE, COMPRESS, or SKIP, and assigns a priority score.
        Never compresses current user prompt or system instructions.
        """
        if not content or not content.strip():
            return ContentAction.SKIP, 0

        tokens = get_token_count(content)

        # 1. User Prompt Protection (SACRED)
        if is_latest_user_prompt or role == "user_prompt":
            return ContentAction.PRESERVE, self.priorities.user_prompt

        # 2. Critical System Instructions
        if is_system_instruction or role == "system":
            return ContentAction.PRESERVE, self.priorities.system_instruction

        # 3. Skip small or already compressed content
        if tokens < self.min_tokens_threshold or "[PromptLens compressed content:" in content:
            return ContentAction.SKIP, self.priorities.relevant_history

        # 4. Tool outputs and logs
        detected_type = content_type or self.detect(content)
        if detected_type == ContentType.LOG:
            # Check if log has errors
            has_error = any(kw in content for kw in ["ERROR", "Exception", "FAIL", "Traceback", "fatal"])
            prio = self.priorities.error_information if has_error else self.priorities.repeated_logs
            return ContentAction.COMPRESS, prio

        if detected_type == ContentType.TOOL_OUTPUT:
            return ContentAction.COMPRESS, self.priorities.tool_result

        if detected_type == ContentType.JSON:
            return ContentAction.COMPRESS, self.priorities.tool_result

        if detected_type == ContentType.CODE:
            return ContentAction.COMPRESS, self.priorities.current_code

        # Conversational history
        if role in ("assistant", "user"):
            return ContentAction.COMPRESS, self.priorities.old_conversation

        return ContentAction.COMPRESS, self.priorities.redundant_content
