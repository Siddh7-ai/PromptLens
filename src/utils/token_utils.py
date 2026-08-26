import tiktoken

ENCODING_NAME = "cl100k_base"


def get_token_count(text: str) -> int:
    """Utility to count tokens using tiktoken (cl100k_base)."""
    if not text:
        return 0
    try:
        encoding = tiktoken.get_encoding(ENCODING_NAME)
        return len(encoding.encode(text))
    except Exception:
        return len(text.split())
