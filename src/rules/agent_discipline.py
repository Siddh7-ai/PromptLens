import os
from typing import Dict, Any

RULES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rules"))

_RULESET_CACHE: Dict[str, str] = {}


def load_ruleset(mode: str) -> str:
    """
    Loads and caches the discipline ruleset text for a given mode ('lite', 'full', 'ultra').
    Returns an empty string if mode is 'off' or file does not exist.
    """
    clean_mode = str(mode or "").strip().lower()
    if clean_mode in ("off", ""):
        return ""

    if clean_mode in _RULESET_CACHE:
        return _RULESET_CACHE[clean_mode]

    file_path = os.path.join(RULES_DIR, f"{clean_mode}.md")
    if not os.path.exists(file_path):
        return ""

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            _RULESET_CACHE[clean_mode] = content
            return content
    except Exception:
        return ""


def inject_discipline_ruleset(payload: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """
    Injects the discipline ruleset prompt nudge into the Anthropic system prompt field.
    Returns the payload unmodified if mode is 'off' or ruleset is empty.
    """
    if not isinstance(payload, dict) or not mode:
        return payload

    clean_mode = str(mode).strip().lower()
    if clean_mode == "off":
        return payload

    ruleset_text = load_ruleset(clean_mode)
    if not ruleset_text:
        return payload

    discipline_notice = f"\n\n[Agent Discipline Ruleset - Mode: {clean_mode.upper()}]\n{ruleset_text}"

    existing_system = payload.get("system")

    if existing_system is None:
        payload["system"] = discipline_notice.strip()
    elif isinstance(existing_system, str):
        payload["system"] = f"{existing_system}{discipline_notice}".strip()
    elif isinstance(existing_system, list):
        # Anthropic supports array of content blocks in system field
        new_block = {"type": "text", "text": discipline_notice.strip()}
        payload["system"] = existing_system + [new_block]

    return payload
