import json
import time
import pytest
from src.store.retrieval_store import RetrievalStore, get_global_store
from src.compress.json_compressor import compress_json
from src.compress.text_compressor import compress_text


def test_store_save_and_get():
    store = RetrievalStore(ttl_seconds=3600)
    original_text = "This is a raw uncompressed tool output string."

    retrieval_id = store.save(original_text)
    assert len(retrieval_id) == 12
    assert store.has(retrieval_id) is True
    assert store.get(retrieval_id) == original_text


def test_store_custom_retrieval_id():
    store = RetrievalStore(ttl_seconds=3600)
    original_text = "Sample payload"
    custom_id = "custom_id_12"

    retrieval_id = store.save(original_text, retrieval_id=custom_id)
    assert retrieval_id == custom_id
    assert store.get(custom_id) == original_text


def test_store_ttl_expiration():
    # TTL of 0 seconds so items expire immediately
    store = RetrievalStore(ttl_seconds=0)
    text = "Expired data"

    retrieval_id = store.save(text)
    # Wait a fraction of a second to ensure time has elapsed
    time.sleep(0.01)

    assert store.get(retrieval_id) is None
    assert store.has(retrieval_id) is False


def test_store_cleanup_expired():
    store = RetrievalStore(ttl_seconds=0)
    store.save("Data 1")
    store.save("Data 2")
    time.sleep(0.01)

    purged = store.cleanup_expired()
    assert purged == 2
    assert store.size() == 0


def test_store_integration_with_json_compressor():
    store = RetrievalStore(ttl_seconds=3600)
    raw_json = json.dumps([{"id": i, "name": f"item_{i}_data_value_long"} for i in range(20)])

    result = compress_json(raw_json, max_array_items=2, min_token_threshold=5, store=store)

    assert result.is_compressed is True
    retrieved = store.get(result.retrieval_id)
    assert retrieved == raw_json


def test_store_integration_with_text_compressor():
    store = RetrievalStore(ttl_seconds=3600)
    long_log = "\n".join([f"Log line {i}" for i in range(50)])

    result = compress_text(long_log, head_lines=5, tail_lines=5, min_token_threshold=10, store=store)

    assert result.is_compressed is True
    retrieved = store.get(result.retrieval_id)
    assert retrieved == long_log


def test_store_ttl_uniform_across_all_paths():
    # 0-second TTL store
    store = RetrievalStore(ttl_seconds=0)

    # Path 1: Text compressor
    long_log = "\n".join([f"Log line {i}" for i in range(50)])
    res_text = compress_text(long_log, head_lines=5, tail_lines=5, min_token_threshold=10, store=store)

    # Path 2: JSON array truncation
    raw_json = json.dumps([{"id": i, "name": f"item_{i}_data_payload", "details": "x" * 20} for i in range(50)])
    res_json = compress_json(raw_json, max_array_items=2, min_token_threshold=5, store=store)

    # Path 3: JSON depth truncation
    deep_json = json.dumps({"nested": {"nested": {"nested": {"leaf": "data_" + "x" * 2000}}}})
    res_depth = compress_json(deep_json, min_token_threshold=5, max_depth=2, store=store)

    time.sleep(0.05)

    # All entries created across all 3 paths should be expired and purged
    purged = store.cleanup_expired()
    assert purged >= 3
    assert store.has(res_text.retrieval_id) is False
    assert store.has(res_json.retrieval_id) is False
    assert store.size() == 0

