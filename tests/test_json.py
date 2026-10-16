"""
Unit tests for JSONCompressor.
Covers: small JSON, large JSON, nested JSON, large arrays, invalid JSON, JSON containing errors/status.
"""
import json
import pytest
from src.compress.json_compressor import JSONCompressor
from src.store.retrieval_store import RetrievalStore


@pytest.fixture
def store():
    return RetrievalStore(ttl_seconds=3600)


@pytest.fixture
def json_compressor(store):
    return JSONCompressor(max_array_items=2, min_token_threshold=40, store=store)


def test_small_json_under_threshold(json_compressor):
    small_obj = {"status": "ok", "count": 2}
    small_json = json.dumps(small_obj)
    res = json_compressor.compress(small_json)
    parsed = json.loads(res.compressed_str)
    assert parsed["status"] == "ok"
    assert "_promptlens_truncated" not in res.compressed_str



def test_large_json_array_sampling_and_summary(json_compressor, store):
    large_list = [
        {"id": i, "name": f"user_{i}", "email": f"u{i}@test.com", "status": "active"}
        for i in range(500)
    ]
    raw_json = json.dumps(large_list)
    res = json_compressor.compress(raw_json)

    assert res.is_compressed
    assert res.compression_ratio > 0.5
    parsed = json.loads(res.compressed_str)
    # Check that summary marker exists
    marker = parsed[-1]
    assert marker["_promptlens_truncated"] is True
    assert marker["total_items"] == 500
    assert "unique_keys" in marker["_promptlens_summary"]

    # Verify original retrievable from store
    retrieved = store.get(res.retrieval_id)
    assert retrieved == raw_json


def test_nested_json_preservation(json_compressor):
    nested = {
        "metadata": {
            "version": "1.0.0",
            "environment": "production",
            "cluster": "us-east-1"
        },
        "records": [
            {"sensor_id": f"s_{i}", "val": i * 3.14}
            for i in range(100)
        ],
        "status": "success",
        "total": 100
    }
    raw_json = json.dumps(nested)
    res = json_compressor.compress(raw_json)

    assert res.is_compressed
    parsed = json.loads(res.compressed_str)
    assert parsed["metadata"]["environment"] == "production"
    assert parsed["status"] == "success"
    assert parsed["total"] == 100


def test_json_error_fields_preserved(json_compressor):
    error_payload = {
        "error": {
            "code": 403,
            "message": "AccessDenied: Insufficient IAM permissions for resource arn:aws:s3:::bucket-01",
            "details": [f"attempt_{i}" for i in range(50)]
        },
        "status": "failed",
        "timestamp": 1775000000
    }
    raw_json = json.dumps(error_payload)
    res = json_compressor.compress(raw_json)

    parsed = json.loads(res.compressed_str)
    assert parsed["status"] == "failed"
    assert parsed["error"]["code"] == 403
    assert "Insufficient IAM" in parsed["error"]["message"]


def test_invalid_json_fails_open(json_compressor):
    broken_json = "{'status': 'missing_quotes', broken_array: [1, 2, "
    res = json_compressor.compress(broken_json)
    assert not res.is_compressed
    assert res.compressed_str == broken_json
