import hashlib
import json
from dataclasses import dataclass
from typing import Any

import tiktoken

ENCODING_NAME = "cl100k_base"


@dataclass
class JSONCompressionResult:
    compressed_str: str
    retrieval_id: str
    original_tokens: int
    compressed_tokens: int
    is_compressed: bool
    compression_ratio: float  # e.g., 0.80 means 80% reduction in tokens


def get_token_count(text: str) -> int:
    """Utility to count tokens using tiktoken (cl100k_base)."""
    try:
        encoding = tiktoken.get_encoding(ENCODING_NAME)
        return len(encoding.encode(text))
    except Exception:
        return len(text.split())


def _compress_node(node: Any, retrieval_id: str, max_array_items: int = 3) -> Any:
    """
    Recursively compresses JSON nodes by truncating arrays larger than max_array_items
    and appending a truncation notice with a retrieval key.
    """
    if isinstance(node, list):
        if len(node) > max_array_items:
            compressed_list = [
                _compress_node(item, retrieval_id, max_array_items)
                for item in node[:max_array_items]
            ]
            omitted = len(node) - max_array_items
            marker = {
                "_promptlens_truncated": True,
                "omitted_items": omitted,
                "total_items": len(node),
                "retrieval_id": retrieval_id,
                "notice": f"Truncated {omitted} items. Use retrieve_original('{retrieval_id}') to view full list.",
            }
            compressed_list.append(marker)
            return compressed_list
        else:
            return [_compress_node(item, retrieval_id, max_array_items) for item in node]
    elif isinstance(node, dict):
        return {
            k: _compress_node(v, retrieval_id, max_array_items)
            for k, v in node.items()
        }
    else:
        return node


def compress_json(
    json_str: str,
    max_array_items: int = 3,
    min_token_threshold: int = 50,
) -> JSONCompressionResult:
    """
    Compresses a JSON string using rule-based array truncation and whitespace minification.

    Args:
        json_str: The raw JSON string to compress.
        max_array_items: Maximum items to retain in arrays before truncating.
        min_token_threshold: Minimum tokens required to trigger structural compression.

    Returns:
        JSONCompressionResult object with compressed string and token metrics.
    """
    original_tokens = get_token_count(json_str)
    retrieval_id = hashlib.sha256(json_str.encode("utf-8")).hexdigest()[:12]

    # Handle invalid JSON gracefully
    try:
        data = json.loads(json_str)
    except Exception:
        return JSONCompressionResult(
            compressed_str=json_str,
            retrieval_id=retrieval_id,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            is_compressed=False,
            compression_ratio=0.0,
        )

    # Handle small JSON under threshold
    if original_tokens < min_token_threshold:
        minified_str = json.dumps(data, separators=(",", ":"))
        minified_tokens = get_token_count(minified_str)
        return JSONCompressionResult(
            compressed_str=minified_str,
            retrieval_id=retrieval_id,
            original_tokens=original_tokens,
            compressed_tokens=minified_tokens,
            is_compressed=minified_tokens < original_tokens,
            compression_ratio=(1.0 - (minified_tokens / original_tokens)) if original_tokens > 0 else 0.0,
        )

    # Structural compression
    compressed_data = _compress_node(data, retrieval_id, max_array_items=max_array_items)
    compressed_str = json.dumps(compressed_data, separators=(",", ":"))
    compressed_tokens = get_token_count(compressed_str)

    # Fallback if compressed size isn't smaller
    if compressed_tokens >= original_tokens:
        minified_str = json.dumps(data, separators=(",", ":"))
        minified_tokens = get_token_count(minified_str)
        return JSONCompressionResult(
            compressed_str=minified_str,
            retrieval_id=retrieval_id,
            original_tokens=original_tokens,
            compressed_tokens=minified_tokens,
            is_compressed=False,
            compression_ratio=0.0,
        )

    ratio = round(1.0 - (compressed_tokens / original_tokens), 4)

    return JSONCompressionResult(
        compressed_str=compressed_str,
        retrieval_id=retrieval_id,
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        is_compressed=True,
        compression_ratio=ratio,
    )
