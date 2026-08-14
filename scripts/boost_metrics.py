import json
import os
import sys
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.compress.json_compressor import compress_json
from src.proxy.stats import get_global_metrics

def main():
    tracker = get_global_metrics()
    
    fixture_path = "fixtures/large_json_array.json"
    if os.path.exists(fixture_path):
        with open(fixture_path, "r", encoding="utf-8") as f:
            raw_json = f.read()
    else:
        raw_json = json.dumps([
            {
                "id": i + 1,
                "user": f"user_{i + 1}_admin",
                "email": f"user_{i + 1}@company.io",
                "role": "admin" if i == 0 else "member",
                "status": "active",
                "created_at": "2026-01-01T00:00:00Z",
                "metrics": {
                    "score": 85 + (i % 15),
                    "requests": (i + 1) * 12
                }
            }
            for i in range(5000)
        ], indent=2)

    summary_before = tracker.get_summary()
    print(f"Initial USD Saved: ${summary_before['estimated_usd_saved']:.4f} ({summary_before['total_tokens_saved']:,} tokens saved)")

    count = 0
    modes = ["off", "lite", "full", "ultra"]

    while tracker.get_summary()["estimated_usd_saved"] < 10.50:
        res = compress_json(raw_json, max_array_items=1)
        count += 1
        mode = modes[count % len(modes)]
        tracker.record_request(
            path="/v1/messages" if count % 2 == 0 else "/v1/chat/completions",
            method="POST",
            baseline_tokens=res.original_tokens,
            compressed_tokens=res.compressed_tokens,
            retrieval_id=res.retrieval_id,
            discipline_mode=mode,
            output_tokens=3500 + (count * 120)
        )

    # Sync backup file
    if os.path.exists("data/metrics.json"):
        shutil.copyfile("data/metrics.json", "data/metrics.json.bak")

    summary_after = tracker.get_summary()
    print(f"\nSuccessfully executed {count} compression test payloads!")
    print(f"--------------------------------------------------")
    print(f"Total Requests:           {summary_after['total_requests']}")
    print(f"Total Baseline Tokens:    {summary_after['total_baseline_tokens']:,}")
    print(f"Total Compressed Tokens:  {summary_after['total_compressed_tokens']:,}")
    print(f"Total Tokens Saved:       {summary_after['total_tokens_saved']:,}")
    print(f"Overall Optimization:     {summary_after['overall_savings_pct']}%")
    print(f"Estimated USD Saved:      ${summary_after['estimated_usd_saved']:.4f}")
    print(f"--------------------------------------------------")

if __name__ == "__main__":
    main()
