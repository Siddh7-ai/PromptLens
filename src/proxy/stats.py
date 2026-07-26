import os
import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any
from src.store.retrieval_store import get_global_store

METRICS_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "metrics.json")
)


@dataclass
class RequestLogItem:
    timestamp: str
    path: str
    method: str
    baseline_tokens: int
    compressed_tokens: int
    savings_pct: float
    retrieval_id: str | None = None


class MetricsTracker:
    """
    Persistent real-time metrics tracker for PromptLens proxy operations.
    Calculates cumulative lifetime token savings, financial savings, and recent request audit trail.
    Persists stats automatically to data/metrics.json so metrics never drop on restart or request pops.
    """

    def __init__(self, storage_path: str | None = METRICS_FILE_PATH):
        self.storage_path = storage_path
        self.total_requests: int = 0
        self.total_baseline_tokens: int = 0
        self.total_compressed_tokens: int = 0
        self.total_retrievals: int = 0
        self.request_logs: List[Dict[str, Any]] = []

        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Loads metrics from disk file if available."""
        if not self.storage_path or not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.total_requests = data.get("total_requests", 0)
                self.total_baseline_tokens = data.get("total_baseline_tokens", 0)
                self.total_compressed_tokens = data.get("total_compressed_tokens", 0)
                self.total_retrievals = data.get("total_retrievals", 0)
                self.request_logs = data.get("request_logs", [])
        except Exception:
            pass

    def _save_to_disk(self) -> None:
        """Saves current metrics snapshot to disk file."""
        if not self.storage_path:
            return
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = {
                "total_requests": self.total_requests,
                "total_baseline_tokens": self.total_baseline_tokens,
                "total_compressed_tokens": self.total_compressed_tokens,
                "total_retrievals": self.total_retrievals,
                "request_logs": self.request_logs[:20]
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def record_request(
        self,
        path: str,
        method: str,
        baseline_tokens: int,
        compressed_tokens: int,
        retrieval_id: str | None = None
    ) -> None:
        """Record metrics for a proxied request."""
        effective_compressed = min(baseline_tokens, compressed_tokens)

        self.total_requests += 1
        self.total_baseline_tokens += baseline_tokens
        self.total_compressed_tokens += effective_compressed

        savings_tokens = max(0, baseline_tokens - effective_compressed)
        savings_pct = (savings_tokens / baseline_tokens * 100.0) if baseline_tokens > 0 else 0.0

        log_entry = {
            "id": len(self.request_logs) + 1,
            "timestamp": time.strftime("%H:%M:%S"),
            "path": path,
            "method": method,
            "baseline_tokens": baseline_tokens,
            "compressed_tokens": compressed_tokens,
            "savings_pct": round(savings_pct, 1),
            "retrieval_id": retrieval_id or "-"
        }
        # Keep last 20 requests in stream table
        self.request_logs.insert(0, log_entry)
        if len(self.request_logs) > 20:
            self.request_logs.pop()

        self._save_to_disk()

    def record_retrieval(self) -> None:
        """Record a successful retrieve_original event."""
        self.total_retrievals += 1
        self._save_to_disk()

    def get_summary(self) -> Dict[str, Any]:
        """Returns consolidated cumulative lifetime metrics summary."""
        tokens_saved = max(0, self.total_baseline_tokens - self.total_compressed_tokens)
        overall_savings_pct = (
            (tokens_saved / self.total_baseline_tokens * 100.0)
            if self.total_baseline_tokens > 0
            else 0.0
        )
        usd_saved = (tokens_saved / 1_000_000.0) * 3.00

        return {
            "total_requests": self.total_requests,
            "total_baseline_tokens": self.total_baseline_tokens,
            "total_compressed_tokens": self.total_compressed_tokens,
            "total_tokens_saved": tokens_saved,
            "overall_savings_pct": round(overall_savings_pct, 1),
            "estimated_usd_saved": round(usd_saved, 4),
            "total_retrievals": self.total_retrievals,
            "active_vault_items": get_global_store().count(),
            "recent_requests": self.request_logs[:20]
        }

    def reset(self) -> None:
        """Resets all metrics to zero and clears disk file."""
        self.total_requests = 0
        self.total_baseline_tokens = 0
        self.total_compressed_tokens = 0
        self.total_retrievals = 0
        self.request_logs.clear()
        if self.storage_path and os.path.exists(self.storage_path):
            try:
                os.remove(self.storage_path)
            except Exception:
                pass


# Shared Global Metrics Tracker Instance
_GLOBAL_METRICS: MetricsTracker | None = None


def get_global_metrics() -> MetricsTracker:
    """Returns global MetricsTracker singleton."""
    global _GLOBAL_METRICS
    if _GLOBAL_METRICS is None:
        _GLOBAL_METRICS = MetricsTracker()
    return _GLOBAL_METRICS
