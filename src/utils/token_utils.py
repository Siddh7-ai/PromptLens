import tiktoken
from typing import Optional

ENCODING_NAME = "cl100k_base"
_ENCODING: Optional[tiktoken.Encoding] = None


def _get_encoding() -> Optional[tiktoken.Encoding]:
    global _ENCODING
    if _ENCODING is None:
        try:
            _ENCODING = tiktoken.get_encoding(ENCODING_NAME)
        except Exception:
            pass
    return _ENCODING


def get_token_count(text: str) -> int:
    """
    High-performance utility to count tokens using cached tiktoken (cl100k_base).
    Safely handles special tokens (<|endoftext|>, etc.) without throwing ValueError.
    """
    if not text:
        return 0
    enc = _get_encoding()
    if enc is not None:
        try:
            return len(enc.encode(text, disallowed_special=()))
        except Exception:
            pass
    # Fallback approximation: 4 chars per token average for English / code
    return max(1, len(text.split()))
