import json
import os
import pytest
from src.compress.json_compressor import compress_json, get_token_count

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))


def test_compress_large_json_array():
    large_json_path = os.path.join(FIXTURES_DIR, "large_json_array.json")
    with open(large_json_path, "r", encoding="utf-8") as f:
        raw_json = f.read()

    result = compress_json(raw_json, max_array_items=3)

    assert result.is_compressed is True
    assert result.original_tokens > 100000
    # Should reduce tokens by over 90% for large arrays
    assert result.compressed_tokens < 1000
    assert result.compression_ratio > 0.90
    assert len(result.retrieval_id) == 12

    # Verify compressed JSON structure
    compressed_data = json.loads(result.compressed_str)
    assert isinstance(compressed_data, list)
    # 3 kept items + 1 truncation marker
    assert len(compressed_data) == 4
    assert compressed_data[-1].get("_promptlens_truncated") is True
    assert compressed_data[-1].get("retrieval_id") == result.retrieval_id


def test_compress_curl_api_response():
    curl_json_path = os.path.join(FIXTURES_DIR, "curl_api_response.json")
    with open(curl_json_path, "r", encoding="utf-8") as f:
        raw_json = f.read()

    result = compress_json(raw_json, max_array_items=3, min_token_threshold=50)

    # curl_api_response contains an array of items, so it should compress
    assert result.original_tokens > 100
    assert result.compressed_tokens < result.original_tokens
    assert len(result.retrieval_id) == 12


def test_invalid_json_handling():
    invalid_json = "This is not a JSON { object: true, "
    result = compress_json(invalid_json)

    assert result.is_compressed is False
    assert result.compressed_str == invalid_json
    assert result.compression_ratio == 0.0


def test_small_json_under_threshold():
    small_json = '{"status": "ok", "code": 200}'
    result = compress_json(small_json, min_token_threshold=500)

    # Below token threshold, should return minified version without truncation
    assert result.compressed_str == '{"status":"ok","code":200}'
    assert len(result.retrieval_id) == 12
