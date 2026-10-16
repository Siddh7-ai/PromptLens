"""
Unit tests for PromptLens ContentRouter and specialized sub-compressors.
"""
import json
import pytest
from src.compress.content_router import ContentRouter, ContentType, get_global_router
from src.compress.search_compressor import compress_search_results, is_search_or_grep_output


def test_detect_json():
    router = ContentRouter()
    json_data = json.dumps([{"id": i, "name": f"item_{i}", "active": True} for i in range(20)])
    assert router.detect_content_type(json_data) == ContentType.JSON


def test_detect_logs():
    router = ContentRouter()
    log_data = """Traceback (most recent call last):
  File "app.py", line 42, in <module>
    main()
  File "app.py", line 12, in main
    raise ValueError("Invalid configuration")
ValueError: Invalid configuration
=== FAILURES ===
"""
    assert router.detect_content_type(log_data) == ContentType.LOGS


def test_detect_search_grep():
    router = ContentRouter()
    grep_data = """src/proxy/server.py:21:from src.compress.json_compressor import compress_json
src/proxy/server.py:22:from src.compress.text_compressor import compress_text
src/proxy/server.py:73:    "description": "Retrieve full uncompressed original"
src/proxy/server.py:103:MIN_COMPRESS_TOKENS = 150
src/proxy/server.py:116:def _compress_tool_content(content: str) -> tuple[str, str | None, float]:
src/proxy/server.py:142:        result = compress_text(
"""
    assert is_search_or_grep_output(grep_data) is True
    assert router.detect_content_type(grep_data) == ContentType.SEARCH


def test_detect_code():
    router = ContentRouter()
    code_data = """import os
import sys
from dataclasses import dataclass

class UserService:
    def __init__(self, db_conn):
        self.db = db_conn

    def get_user_by_id(self, user_id: int):
        return self.db.query("SELECT * FROM users WHERE id = %s", (user_id,))
"""
    assert router.detect_content_type(code_data) == ContentType.CODE


def test_detect_diff():
    router = ContentRouter()
    diff_data = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -10,4 +10,4 @@
-def old_func():
+def new_func():
"""
    assert router.detect_content_type(diff_data) == ContentType.DIFF


def test_small_content_passes_through_intact():
    router = ContentRouter(min_bytes_threshold=250, min_tokens_threshold=80)
    small_prompt = "Fix the login bug in auth_service.py"
    
    assert router.is_worth_optimizing(small_prompt) is False
    res = router.route_and_compress(small_prompt)
    assert res.is_compressed is False
    assert res.compressed_content == small_prompt
    assert res.savings_pct == 0.0


def test_json_compression_routing():
    router = ContentRouter(min_bytes_threshold=100, min_tokens_threshold=30)
    json_data = json.dumps([{"id": i, "user": f"user_{i}", "email": f"user{i}@corp.com", "role": "engineer"} for i in range(40)])
    
    res = router.route_and_compress(json_data)
    assert res.is_compressed is True
    assert res.content_type == ContentType.JSON
    assert res.savings_pct > 30.0
    assert res.retrieval_id is not None
    assert "PromptLens: JSON content compressed" in res.compressed_content


def test_search_compression_routing():
    router = ContentRouter(min_bytes_threshold=100, min_tokens_threshold=30)
    grep_lines = []
    for i in range(1, 35):
        grep_lines.append(f"src/handlers/auth.py:{i*5}:def auth_handler_{i}(req, res):")
    grep_content = "\n".join(grep_lines)

    res = router.route_and_compress(grep_content)
    assert res.is_compressed is True
    assert res.content_type == ContentType.SEARCH
    assert res.savings_pct > 0.0
    assert res.retrieval_id is not None
    assert "PromptLens Search Results" in res.compressed_content


def test_fail_open_safety():
    router = ContentRouter(min_bytes_threshold=50, min_tokens_threshold=10)
    # Corrupt string that claims to be JSON but fails
    malformed = "{" + ("a" * 300)
    res = router.route_and_compress(malformed)
    # Must never throw; returns clean result
    assert isinstance(res.compressed_content, str)
