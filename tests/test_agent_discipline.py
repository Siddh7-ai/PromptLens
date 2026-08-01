import pytest
from src.rules.agent_discipline import load_ruleset, inject_discipline_ruleset, _RULESET_CACHE


def test_load_ruleset_modes():
    """Verify that load_ruleset returns correct content for lite, full, ultra, and empty for off."""
    assert load_ruleset("off") == ""
    assert load_ruleset("OFF") == ""
    assert load_ruleset("invalid_mode") == ""

    lite = load_ruleset("lite")
    assert "Write only the code needed" in lite

    full = load_ruleset("full")
    assert "Prefer editing existing files" in full

    ultra = load_ruleset("ultra")
    assert "Do not restate the plan" in ultra


def test_load_ruleset_caching():
    """Verify rulesets are cached in memory after initial read."""
    _RULESET_CACHE.clear()
    load_ruleset("lite")
    assert "lite" in _RULESET_CACHE


def test_inject_discipline_off_mode_byte_identical():
    """Regression test: Off mode returns payload byte-identical to input."""
    original_payload = {
        "model": "claude-3-5-sonnet-20241022",
        "system": "You are a helpful assistant.",
        "messages": [{"role": "user", "content": "Hello"}]
    }
    import copy
    payload_copy = copy.deepcopy(original_payload)

    result = inject_discipline_ruleset(payload_copy, mode="off")
    assert result == original_payload
    assert result["system"] == "You are a helpful assistant."


def test_inject_discipline_modes():
    """Test system prompt modification for lite, full, and ultra modes."""
    base_payload = {
        "model": "claude-3-5-sonnet-20241022",
        "system": "Base system prompt.",
        "messages": []
    }

    import copy
    lite_res = inject_discipline_ruleset(copy.deepcopy(base_payload), mode="lite")
    assert "Base system prompt." in lite_res["system"]
    assert "[Agent Discipline Ruleset - Mode: LITE]" in lite_res["system"]
    assert "Write only the code needed" in lite_res["system"]

    ultra_res = inject_discipline_ruleset(copy.deepcopy(base_payload), mode="ultra")
    assert "[Agent Discipline Ruleset - Mode: ULTRA]" in ultra_res["system"]
    assert "Do not restate the plan" in ultra_res["system"]


def test_inject_discipline_empty_system():
    """Test injecting discipline ruleset when system field is None or missing."""
    payload = {"model": "claude-3-5-sonnet-20241022", "messages": []}
    res = inject_discipline_ruleset(payload, mode="lite")
    assert "system" in res
    assert "[Agent Discipline Ruleset - Mode: LITE]" in res["system"]


def test_inject_discipline_openai_format():
    """Test injecting discipline ruleset into OpenAI-compatible messages array."""
    openai_payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": "Write a login form."}
        ]
    }
    res = inject_discipline_ruleset(openai_payload, mode="full")
    assert "[Agent Discipline Ruleset - Mode: FULL]" in res["messages"][0]["content"]
    assert "You are a helpful coding assistant." in res["messages"][0]["content"]

    # Test when no system message exists
    no_system_payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Hello"}]
    }
    res2 = inject_discipline_ruleset(no_system_payload, mode="ultra")
    assert res2["messages"][0]["role"] == "system"
    assert "[Agent Discipline Ruleset - Mode: ULTRA]" in res2["messages"][0]["content"]
