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


def _generate_array_skimming_summary(items: list) -> dict:
    """
    Generates structural key and value range summary for truncated JSON arrays using
    adaptive stride sampling for large payloads to ensure high speed and low token overhead.
    """
    if not items or not isinstance(items[0], dict):
        return {}

    total_items = len(items)
    # Adaptive stride sampling: inspect up to 100 items max
    if total_items <= 100:
        sampled_items = items
    else:
        # Sample first 30, last 30, and uniform step sampling from the middle 40
        head = items[:30]
        tail = items[-30:]
        middle_candidates = items[30:-30]
        step = max(1, len(middle_candidates) // 40)
        middle_sample = middle_candidates[::step][:40]
        sampled_items = head + middle_sample + tail

    all_keys = set()
    key_values: dict[str, list] = {}

    for item in sampled_items:
        if isinstance(item, dict):
            for k, v in item.items():
                all_keys.add(k)
                if k not in key_values:
                    key_values[k] = []
                key_values[k].append(v)

    numeric_ranges = {}
    distinct_enums = {}

    for k, vals in key_values.items():
        # Check numeric min/max
        num_vals = [v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if len(num_vals) > 0:
            numeric_ranges[k] = {"min": min(num_vals), "max": max(num_vals)}

        # Check enum values
        str_vals = set(v for v in vals if isinstance(v, str))
        if 0 < len(str_vals) <= 5:
            distinct_enums[k] = sorted(list(str_vals))

    summary = {
        "unique_keys": sorted(list(all_keys)),
        "sampled_items_count": len(sampled_items),
        "total_items": total_items,
    }
    if numeric_ranges:
        summary["numeric_ranges"] = numeric_ranges
    if distinct_enums:
        summary["distinct_enum_values"] = distinct_enums

    return summary


def _compress_node(
    node: Any,
    retrieval_id: str,
    max_array_items: int = 3,
    depth: int = 0,
    max_depth: int = 15,
    store: Any = None,
) -> Any:
    """
    Recursively compresses JSON nodes by truncating arrays larger than max_array_items
    and truncating branches exceeding max_depth with a retrievable vault ID.
    """
    if depth >= max_depth:
        node_str = json.dumps(node, sort_keys=True) if isinstance(node, (dict, list)) else str(node)
        vault_id = hashlib.sha256(node_str.encode("utf-8")).hexdigest()[:12]
        if store:
            store.save(node_str, vault_id)
        return {
            "_promptlens_truncated_depth": True,
            "_type": type(node).__name__,
            "_retrieval_id": vault_id,
            "notice": f"Branch exceeded max depth ({max_depth}). Use retrieve_original('{vault_id}') to view sub-tree.",
        }

    if isinstance(node, list):
        if len(node) > max_array_items:
            compressed_list = [
                _compress_node(item, retrieval_id, max_array_items, depth + 1, max_depth, store)
                for item in node[:max_array_items]
            ]
            omitted = len(node) - max_array_items
            skimming = _generate_array_skimming_summary(node)
            marker = {
                "_promptlens_truncated": True,
                "omitted_items": omitted,
                "total_items": len(node),
                "retrieval_id": retrieval_id,
                "_promptlens_summary": skimming,
                "summary": skimming,
                "notice": f"Truncated {omitted} items. Use retrieve_original('{retrieval_id}') to view full list.",
            }
            compressed_list.append(marker)
            return compressed_list
        else:
            return [
                _compress_node(item, retrieval_id, max_array_items, depth + 1, max_depth, store)
                for item in node
            ]

    elif isinstance(node, dict):
        return {
            k: _compress_node(v, retrieval_id, max_array_items, depth + 1, max_depth, store)
            for k, v in node.items()
        }
    else:
        return node


from src.store.retrieval_store import RetrievalStore, get_global_store


def compress_json(
    json_str: str,
    max_array_items: int = 3,
    min_token_threshold: int = 50,
    store: Any = None,
    max_depth: int = 15,
) -> JSONCompressionResult:
    """
    Compresses a JSON string using rule-based array truncation and whitespace minification.

    Args:
        json_str: The raw JSON string to compress.
        max_array_items: Maximum items to retain in arrays before truncating.
        min_token_threshold: Minimum tokens required to trigger structural compression.
        store: Optional RetrievalStore instance. Defaults to get_global_store().
        max_depth: Maximum recursion depth before branch truncation.

    Returns:
        JSONCompressionResult object with compressed string and token metrics.
    """
    if store is None:
        store = get_global_store()
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
    compressed_data = _compress_node(
        data, retrieval_id, max_array_items=max_array_items, depth=0, max_depth=max_depth, store=store
    )
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

    if store:
        store.save(json_str, retrieval_id)

    return JSONCompressionResult(
        compressed_str=compressed_str,
        retrieval_id=retrieval_id,
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        is_compressed=True,
        compression_ratio=ratio,
    )

