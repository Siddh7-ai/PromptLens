"""
Anthropic Request Parser and Compression Handler for PromptLens.
Handles POST /v1/messages payloads, preserving sacred user prompts and system instructions,
compressing large tool_result blocks, and injecting retrieve_original tool definitions with fail-open safety.
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
    CompressionReport,
)
from src.store.retrieval_store import RetrievalStore, get_global_store
from src.tokens.counter import TokenCounter

logger = logging.getLogger("promptlens.anthropic")

ANTHROPIC_RETRIEVE_TOOL = {
    "name": "retrieve_original",
    "description": "Retrieve full uncompressed original content or targeted line snippets using line ranges, regex/substring queries, and context windows.",
    "input_schema": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "The unique hash ID of the compressed content to retrieve (e.g. pl_8f92a1)."
            },
            "query": {
                "type": "string",
                "description": "Optional search term or regex pattern to filter matching lines."
            },
            "use_regex": {
                "type": "boolean",
                "description": "Whether to treat query as a regex pattern. Defaults to false."
            },
            "line_range": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Optional 2-element array [start_line, end_line] (1-indexed)."
            },
            "context_lines": {
                "type": "integer",
                "description": "Number of surrounding context lines to include around query matches. Defaults to 0."
            }
        },
        "required": ["id"]
    }
}


class AnthropicHandler:
    """Processes Anthropic /v1/messages requests with selective tool result and context compression."""

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
        """Compresses content chunk based on type."""
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
        Processes Anthropic messages payload.
        Fails open: returns original payload if any error occurs.
        """
        t0 = time.perf_counter()
        raw_copy = copy.deepcopy(payload)

        try:
            messages = payload.get("messages", [])
            if not isinstance(messages, list) or not messages:
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

            # Find latest user prompt index
            latest_user_idx = -1
            for idx in range(len(messages) - 1, -1, -1):
                msg = messages[idx]
                if isinstance(msg, dict) and msg.get("role") == "user":
                    latest_user_idx = idx
                    break

            items_processed = 0
            items_compressed = 0
            items_preserved = 0
            items_skipped = 0
            retrieval_ids: List[str] = []
            breakdown_by_type: Dict[str, Dict[str, int]] = {}

            total_orig_tokens = 0
            total_comp_tokens = 0

            # Count system tokens if present
            if "system" in payload and isinstance(payload["system"], str):
                sys_tokens = self.counter.count_tokens(payload["system"])
                total_orig_tokens += sys_tokens
                total_comp_tokens += sys_tokens
                items_preserved += 1

            for msg_idx, msg in enumerate(messages):
                if not isinstance(msg, dict):
                    continue

                role = msg.get("role", "")
                content = msg.get("content")

                # String content
                if isinstance(content, str):
                    items_processed += 1
                    c_tokens = self.counter.count_tokens(content)
                    total_orig_tokens += c_tokens

                    is_latest_user = (msg_idx == latest_user_idx)
                    action, prio = self.router.classify_action(
                        content, role=role, is_latest_user_prompt=is_latest_user
                    )

                    if action == ContentAction.PRESERVE:
                        items_preserved += 1
                        total_comp_tokens += c_tokens
                    elif action == ContentAction.SKIP:
                        items_skipped += 1
                        total_comp_tokens += c_tokens
                    else:
                        ctype = self.router.detect(content)
                        comp_text, rid = self._compress_chunk(content, ctype)
                        new_tokens = self.counter.count_tokens(comp_text)
                        if new_tokens < c_tokens and rid:
                            msg["content"] = comp_text
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

                # List of content blocks (e.g. tool_use, tool_result, text blocks)
                elif isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        items_processed += 1
                        b_type = block.get("type")

                        if b_type == "tool_result":
                            b_content = block.get("content")
                            if isinstance(b_content, str):
                                c_tokens = self.counter.count_tokens(b_content)
                                total_orig_tokens += c_tokens

                                ctype = self.router.detect(b_content)
                                comp_text, rid = self._compress_chunk(b_content, ctype)
                                new_tokens = self.counter.count_tokens(comp_text)

                                if new_tokens < c_tokens and rid:
                                    block["content"] = comp_text
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
                            else:
                                items_skipped += 1
                        elif b_type == "text":
                            txt = block.get("text", "")
                            c_tokens = self.counter.count_tokens(txt)
                            total_orig_tokens += c_tokens
                            if msg_idx == latest_user_idx:
                                items_preserved += 1
                                total_comp_tokens += c_tokens
                            else:
                                ctype = self.router.detect(txt)
                                comp_text, rid = self._compress_chunk(txt, ctype)
                                new_tokens = self.counter.count_tokens(comp_text)
                                if new_tokens < c_tokens and rid:
                                    block["text"] = comp_text
                                    items_compressed += 1
                                    retrieval_ids.append(rid)
                                    total_comp_tokens += new_tokens
                                else:
                                    items_skipped += 1
                                    total_comp_tokens += c_tokens
                        else:
                            items_preserved += 1

            # Inject retrieve_original tool into payload["tools"] if present and compression occurred
            if items_compressed > 0 and "tools" in payload and isinstance(payload["tools"], list):
                tools = payload["tools"]
                if not any(t.get("name") == "retrieve_original" for t in tools if isinstance(t, dict)):
                    tools.append(ANTHROPIC_RETRIEVE_TOOL)

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
            logger.error(f"[Fail-Open] Error processing Anthropic payload: {err}", exc_info=True)
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
