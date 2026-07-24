import time
from dataclasses import dataclass, field
from typing import List, Dict, Any


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
    Real-time metrics tracker for PromptLens proxy operations.
    Calculates token savings, estimated financial savings, and maintains request logs.
    """

    def __init__(self):
        self.total_requests: int = 0
        self.total_baseline_tokens: int = 0
        self.total_compressed_tokens: int = 0
        self.total_retrievals: int = 0
        self.request_logs: List[Dict[str, Any]] = []

    def record_request(
        self,
        path: str,
        method: str,
        baseline_tokens: int,
        compressed_tokens: int,
        retrieval_id: str | None = None
    ) -> None:
        """Record metrics for a proxied request."""
        self.total_requests += 1
        self.total_baseline_tokens += baseline_tokens
        self.total_compressed_tokens += compressed_tokens

        savings_tokens = max(0, baseline_tokens - compressed_tokens)
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
        # Keep last 50 requests
        self.request_logs.insert(0, log_entry)
        if len(self.request_logs) > 50:
            self.request_logs.pop()

    def record_retrieval(self) -> None:
        """Record a successful retrieve_original event."""
        self.total_retrievals += 1


    def get_summary(self) -> Dict[str, Any]:
        """Returns consolidated metrics summary."""
        tokens_saved = max(0, self.total_baseline_tokens - self.total_compressed_tokens)
        overall_savings_pct = (
            (tokens_saved / self.total_baseline_tokens * 100.0)
            if self.total_baseline_tokens > 0
            else 0.0
        )

        # Estimated USD savings based on $3.00 per 1 million input tokens (Claude 3.5 Sonnet standard rate)
        usd_saved = (tokens_saved / 1_000_000.0) * 3.00

        return {
            "total_requests": self.total_requests,
            "total_baseline_tokens": self.total_baseline_tokens,
            "total_compressed_tokens": self.total_compressed_tokens,
            "total_tokens_saved": tokens_saved,
            "overall_savings_pct": round(overall_savings_pct, 1),
            "estimated_usd_saved": round(usd_saved, 4),
            "total_retrievals": self.total_retrievals,
            "recent_requests": self.request_logs
        }

    def reset(self) -> None:
        """Resets all metrics to zero."""
        self.total_requests = 0
        self.total_baseline_tokens = 0
        self.total_compressed_tokens = 0
        self.total_retrievals = 0
        self.request_logs.clear()


# Shared Global Metrics Tracker Instance
_GLOBAL_METRICS: MetricsTracker | None = None


def get_global_metrics() -> MetricsTracker:
    """Returns global MetricsTracker singleton."""
    global _GLOBAL_METRICS
    if _GLOBAL_METRICS is None:
        _GLOBAL_METRICS = MetricsTracker()
    return _GLOBAL_METRICS
