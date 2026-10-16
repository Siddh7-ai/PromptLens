"""
Unit tests for TextCompressor.
Covers: short text, long text, repeated paragraphs, important instructions, headings.
"""
import pytest
from src.compress.text_compressor import TextCompressor
from src.store.retrieval_store import RetrievalStore


@pytest.fixture
def store():
    return RetrievalStore(ttl_seconds=3600)


@pytest.fixture
def text_compressor(store):
    return TextCompressor(min_tokens_threshold=40, store=store)


def test_short_text_passes_intact(text_compressor):
    short_prose = "PromptLens context optimization platform. Compresses logs and code."
    res = text_compressor.compress(short_prose)
    assert not res.is_compressed
    assert res.compressed_str == short_prose


def test_repeated_paragraphs_deduplicated(text_compressor):
    repeated_para = "This is a boilerplate disclaimer paragraph that explains compliance policies and security standards."
    paras = [
        "# Architectural Guidelines",
        "PromptLens follows a clean layered proxy architecture.",
    ] + [repeated_para for _ in range(15)] + [
        "## Final Deployment Instructions",
        "Deploy the container using docker-compose up."
    ]
    raw_text = "\n\n".join(paras)
    res = text_compressor.compress(raw_text)

    assert res.is_compressed
    assert res.compression_ratio > 0
    # Headings preserved
    assert "# Architectural Guidelines" in res.compressed_str
    assert "## Final Deployment Instructions" in res.compressed_str
    # Repetition collapsed
    assert res.compressed_str.count(repeated_para) <= 2


def test_important_instructions_and_rules_preserved(text_compressor, store):
    paras = [
        "# System Architecture Specification",
        "The proxy runs on port 8000 and intercepts requests.",
        "Some background filler paragraph about general web history and ancient proxy servers.",
        "Another filler paragraph about various internet protocols from the 1990s.",
        "Yet another filler paragraph about hardware switches and routers.",
        "### Critical Deployment Requirements",
        "- MUST configure TARGET_BASE_URL before launching.",
        "- NEVER run root user in production containers.",
        "- ALWAYS verify that SSL certificates are valid.",
        "Historical note about legacy operating systems and defunct browsers.",
        "More background text about obsolete server operating systems.",
        "## Conclusion",
        "The system is now ready for verification."
    ]
    raw_text = "\n\n".join(paras)
    res = text_compressor.compress(raw_text)

    assert res.is_compressed
    assert "### Critical Deployment Requirements" in res.compressed_str
    assert "- MUST configure TARGET_BASE_URL" in res.compressed_str
    assert "- NEVER run root user" in res.compressed_str
    assert "- ALWAYS verify that SSL" in res.compressed_str
    assert "## Conclusion" in res.compressed_str

    # Verify retrieval
    retrieved = store.get(res.retrieval_id)
    assert retrieved == raw_text
