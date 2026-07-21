import os
import pytest
from src.compress.text_compressor import compress_text, get_token_count

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))


def test_compress_long_file_read():
    filepath = os.path.join(FIXTURES_DIR, "long_file_read.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = compress_text(content, head_lines=5, tail_lines=5)

    assert result.is_compressed is True
    assert result.compressed_tokens < result.original_tokens
    assert result.compression_ratio > 0.30
    assert len(result.retrieval_id) == 12
    assert "PROMPT LENS TRUNCATED" in result.compressed_str


def test_compress_python_stack_trace():
    filepath = os.path.join(FIXTURES_DIR, "python_stack_trace.log")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = compress_text(content)

    assert result.is_compressed is True
    assert result.compressed_tokens < result.original_tokens
    assert "stack trace lines" in result.compressed_str or "PROMPT LENS TRUNCATED" in result.compressed_str
    assert len(result.retrieval_id) == 12


def test_compress_db_query_output():
    filepath = os.path.join(FIXTURES_DIR, "db_query_output.txt")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = compress_text(content, head_lines=5, tail_lines=5)

    assert result.is_compressed is True
    assert result.compressed_tokens < result.original_tokens
    assert len(result.retrieval_id) == 12


def test_compress_git_diff():
    filepath = os.path.join(FIXTURES_DIR, "git_diff.patch")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = compress_text(content, head_lines=5, tail_lines=5)

    assert result.is_compressed is True
    assert result.compressed_tokens < result.original_tokens


def test_small_text_under_threshold():
    small_text = "Line 1\nLine 2\nLine 3"
    result = compress_text(small_text, min_token_threshold=100)

    assert result.is_compressed is False
    assert result.compressed_str == small_text
    assert result.compression_ratio == 0.0
