"""
Unit tests for ToolOutputCompressor.
Covers: git diffs, terminal outputs, DB query tables, test outputs, status preservation.
"""
import pytest
from src.compress.tool_compressor import ToolOutputCompressor
from src.store.retrieval_store import RetrievalStore


@pytest.fixture
def store():
    return RetrievalStore(ttl_seconds=3600)


@pytest.fixture
def tool_compressor(store):
    return ToolOutputCompressor(min_lines_threshold=15, min_tokens_threshold=40, store=store)


def test_git_diff_compression(tool_compressor):
    diff_lines = [
        "diff --git a/src/core.py b/src/core.py",
        "index 123456..789abc 100644",
        "--- a/src/core.py",
        "+++ b/src/core.py",
        "@@ -10,25 +10,25 @@ class Engine:",
    ] + [f"    line_{i} unchanged context code" for i in range(25)] + [
        "+   new_optimized_feature_call()",
        "-   old_deprecated_feature_call()",
    ] + [f"    line_{i} unchanged context code" for i in range(25, 50)]
    raw_diff = "\n".join(diff_lines)

    res = tool_compressor.compress(raw_diff)
    assert res.is_compressed
    assert res.tool_type == "git_diff"
    assert "diff --git a/src/core.py" in res.compressed_output
    assert "+   new_optimized_feature_call()" in res.compressed_output
    assert "-   old_deprecated_feature_call()" in res.compressed_output
    assert "unchanged context lines omitted" in res.compressed_output


def test_db_table_compression(tool_compressor):
    header = [
        "+----+------------+-------------------+",
        "| id | name       | email             |",
        "+----+------------+-------------------+",
    ]
    rows = [f"| {i:>2} | user_{i:<5} | user_{i}@domain.io |" for i in range(1, 60)]
    footer = [
        "+----+------------+-------------------+",
        "60 rows in set (0.02 sec)"
    ]
    raw_table = "\n".join(header + rows + footer)

    res = tool_compressor.compress(raw_table)
    assert res.is_compressed
    assert res.tool_type == "db_table"
    assert "| id | name" in res.compressed_output
    assert "tabular data rows omitted" in res.compressed_output
    assert "60 rows in set" in res.compressed_output
