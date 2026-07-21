import hashlib
import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class StoreItem:
    content: str
    created_at: float
    retrieval_id: str


class RetrievalStore:
    """
    Hash-keyed, TTL-based memory store for uncompressed original data.
    """

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._store: Dict[str, StoreItem] = {}

    def save(self, content: str, retrieval_id: Optional[str] = None) -> str:
        """
        Saves original content to the store and returns a unique retrieval_id.
        """
        if not retrieval_id:
            retrieval_id = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]

        item = StoreItem(
            content=content,
            created_at=time.time(),
            retrieval_id=retrieval_id,
        )
        self._store[retrieval_id] = item
        return retrieval_id

    def get(self, retrieval_id: str) -> Optional[str]:
        """
        Retrieves original content by retrieval_id if not expired.
        """
        item = self._store.get(retrieval_id)
        if not item:
            return None

        # Check TTL
        if time.time() - item.created_at > self.ttl_seconds:
            del self._store[retrieval_id]
            return None

        return item.content

    def has(self, retrieval_id: str) -> bool:
        """Checks if a non-expired key exists in the store."""
        return self.get(retrieval_id) is not None

    def cleanup_expired(self) -> int:
        """Purges all expired items from the store. Returns count of purged items."""
        now = time.time()
        expired_keys = [
            key
            for key, item in self._store.items()
            if now - item.created_at > self.ttl_seconds
        ]
        for key in expired_keys:
            del self._store[key]
        return len(expired_keys)

    def size(self) -> int:
        """Returns total active items in store."""
        self.cleanup_expired()
        return len(self._store)

    def clear(self) -> None:
        """Clears all stored items."""
        self._store.clear()


# Shared Global Singleton Instance
_GLOBAL_STORE: Optional[RetrievalStore] = None


def get_global_store(ttl_seconds: int = 3600) -> RetrievalStore:
    """Returns the shared global RetrievalStore instance."""
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None:
        _GLOBAL_STORE = RetrievalStore(ttl_seconds=ttl_seconds)
    return _GLOBAL_STORE
