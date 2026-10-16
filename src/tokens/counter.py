"""
Token Counter module for PromptLens.
Calculates accurate token metrics using tiktoken (cl100k_base) with safe fallback estimation.
"""
from typing import Dict, Any
import tiktoken

ENCODING_NAME = "cl100k_base"


class TokenCounter:
    """Accurately counts tokens and calculates compression savings metrics."""

    def __init__(self, encoding_name: str = ENCODING_NAME):
        self.encoding_name = encoding_name
        self._encoding = None

    def _get_encoding(self):
        if self._encoding is None:
            try:
                self._encoding = tiktoken.get_encoding(self.encoding_name)
            except Exception:
                self._encoding = None
        return self._encoding

    def count_tokens(self, text: str) -> int:
        """Counts tokens using tiktoken cl100k_base. Falls back to whitespace estimation if unavailable."""
        if not text:
            return 0
        enc = self._get_encoding()
        if enc is not None:
            try:
                return len(enc.encode(text))
            except Exception:
                pass
        # Fallback estimation (~4 chars per token for English/code)
        return max(1, len(text.split()))

    def calculate_savings(self, original_tokens: int, compressed_tokens: int) -> Dict[str, Any]:
        """Calculates standard token savings metrics."""
        tokens_saved = max(0, original_tokens - compressed_tokens)
        if original_tokens <= 0:
            return {
                "original_tokens": 0,
                "compressed_tokens": compressed_tokens,
                "tokens_saved": 0,
                "compression_ratio": 1.0,
                "savings_percentage": 0.0,
            }

        compression_ratio = round(compressed_tokens / original_tokens, 4)
        savings_percentage = round((tokens_saved / original_tokens) * 100.0, 2)

        return {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "tokens_saved": tokens_saved,
            "compression_ratio": compression_ratio,
            "savings_percentage": savings_percentage,
        }


# Global instance
_DEFAULT_COUNTER = TokenCounter()


def get_token_count(text: str) -> int:
    """Convenience functional interface for counting tokens."""
    return _DEFAULT_COUNTER.count_tokens(text)


def calculate_savings(original_tokens: int, compressed_tokens: int) -> Dict[str, Any]:
    """Convenience functional interface for calculating savings metrics."""
    return _DEFAULT_COUNTER.calculate_savings(original_tokens, compressed_tokens)
