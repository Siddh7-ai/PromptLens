"""
OpenAI Request Parser and Compression Handler for PromptLens.
Handles POST /v1/chat/completions payloads, protecting sacred user prompt and system messages,
routing tool responses and large context chunks to specialized compressors, with fail-open safety.
"""
import copy
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from src.compress.code_compressor import CodeCompressor
from src.compress.json_compressor import JSONCompressor
from src.compress.log_compressor import LogCompressor
from src.compress.router import ContentRouter
from src.compress.text_compressor import TextCompressor
from src.compress.tool_compressor import ToolOutputCompressor
from src.models.compression_result import (
    ContentAction,
    ContentType,
    CompressionItem,
    CompressionReport,
    DEFAULT_PRIORITIES,
)
from src.store.retrieval_store import RetrievalStore, get_global_store
from src.tokens.counter import TokenCounter

logger = logging.getLogger("promptlens.openai")

OPENAI_RETRIEVE_TOOL = {
    "type": "function",
    "function": {
        "name": "retrieve_original",
        "description": "Fetch exact uncompressed content by PromptLens retrieval ID or line range.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "The retrieval ID hash (e.g. pl_8f92a1)"},
                "line_range": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Optional [start_line, end_line] (1-indexed)"
                },
                "query": {"type": "string", "description": "Optional search string or regex"}
            },
            "required": ["id"]
        }
    }
}


class OpenAIHandler:
    """Processes OpenAI /v1/chat/completions requests with selective compression."""

    def __init__(
        self,
        store: Optional[RetrievalStore] = None,
        token_counter: Optional[TokenCounter] = None,
        min_tokens_threshold: int = 60,
    ):
        self.store = store or get_global_store()
        self.counter = token_counter or TokenCounter()
        self.router = ContentRouter(min_tokens_threshold=min_tokens_threshold)
        self.code_compressor = CodeCompressor(store=self.store)
        self.json_compressor = JSONCompressor(store=self.store)
        self.log_compressor = LogCompressor(store=self.store)
        self.text_compressor = TextCompressor(store=self.store)
        self.tool_compressor = ToolOutputCompressor(store=self.store)

    def _compress_chunk(self, content: str, content_type: ContentType) -> Tuple[str, Optional[str]]:
        """Compresses content based on detected content type."""
        if content_type == ContentType.JSON:
            res = self.json_compressor.compress(content)
            if res.is_compressed:
                notice = f"\n\n[PromptLens compressed content: {res.retrieval_id}]"
                return res.compressed_str + notice, res.retrieval_id
        elif content_type == ContentType.CODE:
            res = self.code_compressor.compress(content)
            if res.is_compressed:
                return res.compressed_code, res.retrieval_id
        elif content_type == ContentType.LOG:
            res = self.log_compressor.compress(content)
            if res.is_compressed:
                return res.compressed_log, res.retrieval_id
        elif content_type == ContentType.TOOL_OUTPUT:
            res = self.tool_compressor.compress(content)
            if res.is_compressed:
                return res.compressed_output, res.retrieval_id
        else:
            res = self.text_compressor.compress(content)
            if res.is_compressed:
                return res.compressed_str, res.retrieval_id
        return content, None

    def process(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], CompressionReport]:
        """
        Processes OpenAI chat completions payload.
        Fails open: returns original payload if any error occurs.
        """
        t0 = time.perf_counter()
        raw_copy = copy.deepcopy(payload)

        try:
            messages = payload.get("messages", [])
            if not isinstance(messages, list) or not messages:
                # Nothing to process
                orig_tokens = self.counter.count_tokens(str(payload))
                report = CompressionReport(
                    original_tokens=orig_tokens,
                    compressed_tokens=orig_tokens,
                    tokens_saved=0,
                    compression_ratio=1.0,
                    savings_percentage=0.0,
                    items_processed=0,
                    items_compressed=0,
                    items_preserved=0,
                    items_skipped=0,
                    compression_time_ms=0.0,
                )
                return payload, report

            # Find index of latest user prompt to protect it strictly
            latest_user_idx = -1
            for idx in range(len(messages) - 1, -1, -1):
                msg = messages[idx]
                if isinstance(msg, dict) and msg.get("role") == "user":
                    latest_user_idx = idx
                    break

            items_processed = len(messages)
            items_compressed = 0
            items_preserved = 0
            items_skipped = 0
            retrieval_ids: List[str] = []
            breakdown_by_type: Dict[str, Dict[str, int]] = {}

            total_orig_tokens = 0
            total_comp_tokens = 0

            for idx, msg in enumerate(messages):
                if not isinstance(msg, dict):
                    continue

                role = msg.get("role", "")
                content = msg.get("content", "")

                if not isinstance(content, str):
                    items_skipped += 1
                    continue

                c_tokens = self.counter.count_tokens(content)
                total_orig_tokens += c_tokens

                # RULE 1: User prompt is SACRED (latest user prompt is PRESERVED 100%)
                is_latest_user = (idx == latest_user_idx)
                is_system = (role == "system")

                action, priority = self.router.classify_action(
                    content,
                    role=role,
                    is_latest_user_prompt=is_latest_user,
                    is_system_instruction=is_system
                )

                if action == ContentAction.PRESERVE:
                    items_preserved += 1
                    total_comp_tokens += c_tokens
                    continue

                if action == ContentAction.SKIP:
                    items_skipped += 1
                    total_comp_tokens += c_tokens
                    continue

                # ContentAction.COMPRESS
                ctype = self.router.detect(content)
                compressed_content, rid = self._compress_chunk(content, ctype)
                new_tokens = self.counter.count_tokens(compressed_content)

                if new_tokens < c_tokens and rid:
                    msg["content"] = compressed_content
                    items_compressed += 1
                    retrieval_ids.append(rid)
                    total_comp_tokens += new_tokens

                    cname = ctype.value.lower()
                    if cname not in breakdown_by_type:
                        breakdown_by_type[cname] = {"original": 0, "compressed": 0}
                    breakdown_by_type[cname]["original"] += c_tokens
                    breakdown_by_type[cname]["compressed"] += new_tokens
                else:
                    items_skipped += 1
                    total_comp_tokens += c_tokens

            # Inject retrieve_original tool if tools are present and compression occurred
            if items_compressed > 0 and "tools" in payload and isinstance(payload["tools"], list):
                tools = payload["tools"]
                if not any(t.get("function", {}).get("name") == "retrieve_original" for t in tools if isinstance(t, dict)):
                    tools.append(OPENAI_RETRIEVE_TOOL)

            t1 = time.perf_counter()
            elapsed_ms = round((t1 - t0) * 1000, 2)
            savings = self.counter.calculate_savings(total_orig_tokens, total_comp_tokens)

            report = CompressionReport(
                original_tokens=total_orig_tokens,
                compressed_tokens=total_comp_tokens,
                tokens_saved=savings["tokens_saved"],
                compression_ratio=savings["compression_ratio"],
                savings_percentage=savings["savings_percentage"],
                items_processed=items_processed,
                items_compressed=items_compressed,
                items_preserved=items_preserved,
                items_skipped=items_skipped,
                compression_time_ms=elapsed_ms,
                breakdown_by_type=breakdown_by_type,
                retrieval_ids=retrieval_ids,
            )
            return payload, report

        except Exception as err:
            logger.error(f"[Fail-Open] Error processing OpenAI payload: {err}", exc_info=True)
            # Fail-open guarantee: return unmolested original payload
            orig_tokens = self.counter.count_tokens(str(raw_copy))
            report = CompressionReport(
                original_tokens=orig_tokens,
                compressed_tokens=orig_tokens,
                tokens_saved=0,
                compression_ratio=1.0,
                savings_percentage=0.0,
                items_processed=0,
                items_compressed=0,
                items_preserved=0,
                items_skipped=0,
                compression_time_ms=round((time.perf_counter() - t0) * 1000, 2),
            )
            return raw_copy, report
