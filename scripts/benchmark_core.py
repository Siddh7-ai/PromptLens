"""
PromptLens Core Context Compression Benchmark Script.
Evaluates the core compression pipeline across 5 standard developer scenarios:
1. Large codebase context
2. Large terminal logs
3. Large JSON API response
4. Long conversation history
5. Mixed developer context

Measures:
- Original tokens
- Compressed tokens
- Tokens saved
- Savings %
- Compression latency (ms)
- Retrieval latency (ms)
"""
import json
import os
import time
from typing import Dict, Any, List

from src.compress.code_compressor import CodeCompressor
from src.compress.json_compressor import JSONCompressor
from src.compress.log_compressor import LogCompressor
from src.compress.text_compressor import TextCompressor
from src.proxy.openai import OpenAIHandler
from src.store.retrieval_store import RetrievalStore
from src.tokens.counter import TokenCounter


def load_fixture(rel_path: str) -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full = os.path.join(base, rel_path)
    if os.path.exists(full):
        with open(full, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def run_benchmark() -> List[Dict[str, Any]]:
    store = RetrievalStore(ttl_seconds=3600)
    counter = TokenCounter()
    code_compressor = CodeCompressor(store=store)
    json_compressor = JSONCompressor(store=store)
    log_compressor = LogCompressor(store=store)
    text_compressor = TextCompressor(store=store)
    openai_handler = OpenAIHandler(store=store, token_counter=counter)

    # 1. Large codebase context
    code_fixture = load_fixture("fixtures/long_file_read.py")
    if not code_fixture:
        code_fixture = "class Engine:\n" + ("    def compute(self, x): return x * 2\n" * 150)

    # 2. Large terminal logs
    log_fixture = load_fixture("fixtures/python_stack_trace.log")
    if not log_fixture:
        log_fixture = "2026-07-20 10:00:00 INFO Polling...\n" * 100 + "Traceback (most recent call last):\n  File 'app.py'\nKeyError: 'id'\n"

    # 3. Large JSON API response
    json_fixture = load_fixture("fixtures/large_json_array.json")
    if not json_fixture:
        json_fixture = json.dumps([{"id": i, "name": f"user_{i}", "active": True} for i in range(1000)])

    # 4. Long conversation history
    long_conversation_msgs = [
        {"role": "system", "content": "You are a coding assistant."}
    ]
    for i in range(25):
        long_conversation_msgs.append({"role": "user", "content": f"Turn {i}: How do I optimize query {i} in the database?"})
        long_conversation_msgs.append({"role": "assistant", "content": f"Response {i}: Use an index on column_{i}."})
    long_conversation_msgs.append({"role": "user", "content": "What was the recommendation for query 0?"})

    # 5. Mixed developer context
    mixed_msgs = [
        {"role": "system", "content": "You are a senior debugging assistant."},
        {"role": "user", "content": f"Here is the service code:\n```python\n{code_fixture[:2000]}\n```"},
        {"role": "assistant", "content": "Code loaded."},
        {"role": "user", "content": f"And here is the error trace from pytest:\n{log_fixture[:2500]}"},
        {"role": "assistant", "content": "Log received."},
        {"role": "user", "content": "Fix the failing test in test_service.py"}
    ]

    scenarios = [
        ("1. Large Codebase Context", "code", code_fixture),
        ("2. Large Terminal Logs", "log", log_fixture),
        ("3. Large JSON API Response", "json", json_fixture),
        ("4. Long Conversation", "chat_history", {"model": "gpt-4o", "messages": long_conversation_msgs}),
        ("5. Mixed Developer Context", "mixed", {"model": "gpt-4o", "messages": mixed_msgs}),
    ]

    results = []

    print("\n" + "=" * 95)
    print("                      PROMPTLENS CORE COMPRESSION BENCHMARK")
    print("=" * 95)
    print(f"{'Scenario':<28} | {'Orig Tok':<9} | {'Comp Tok':<9} | {'Saved':<8} | {'Savings %':<9} | {'Comp (ms)':<9} | {'Retr (ms)':<9}")
    print("-" * 95)

    for name, stype, data in scenarios:
        t0 = time.perf_counter()
        retrieval_id = None
        orig_tokens = 0
        comp_tokens = 0

        if stype == "code":
            orig_tokens = counter.count_tokens(data)
            res = code_compressor.compress(data)
            comp_tokens = res.compressed_tokens
            retrieval_id = res.retrieval_id
        elif stype == "log":
            orig_tokens = counter.count_tokens(data)
            res = log_compressor.compress(data)
            comp_tokens = res.compressed_tokens
            retrieval_id = res.retrieval_id
        elif stype == "json":
            orig_tokens = counter.count_tokens(data)
            res = json_compressor.compress(data)
            comp_tokens = res.compressed_tokens
            retrieval_id = res.retrieval_id
        else:
            # Multi-turn payload through OpenAI handler
            orig_tokens = counter.count_tokens(str(data))
            processed, rep = openai_handler.process(data)
            comp_tokens = rep.compressed_tokens
            retrieval_id = rep.retrieval_ids[0] if rep.retrieval_ids else None

        t1 = time.perf_counter()
        comp_latency_ms = round((t1 - t0) * 1000, 2)

        # Measure retrieval latency
        t2 = time.perf_counter()
        if retrieval_id:
            _ = store.get(retrieval_id)
        t3 = time.perf_counter()
        retr_latency_ms = round((t3 - t2) * 1000, 3)

        tokens_saved = max(0, orig_tokens - comp_tokens)
        savings_pct = round((tokens_saved / orig_tokens) * 100.0, 1) if orig_tokens > 0 else 0.0

        rec = {
            "scenario": name,
            "original_tokens": orig_tokens,
            "compressed_tokens": comp_tokens,
            "tokens_saved": tokens_saved,
            "savings_pct": savings_pct,
            "compression_latency_ms": comp_latency_ms,
            "retrieval_latency_ms": retr_latency_ms,
        }
        results.append(rec)

        print(f"{name:<28} | {orig_tokens:>9,} | {comp_tokens:>9,} | {tokens_saved:>8,} | {savings_pct:>8.1f}% | {comp_latency_ms:>9.2f} | {retr_latency_ms:>9.3f}")

    print("=" * 95)
    total_orig = sum(r["original_tokens"] for r in results)
    total_comp = sum(r["compressed_tokens"] for r in results)
    total_saved = sum(r["tokens_saved"] for r in results)
    overall_pct = round((total_saved / total_orig) * 100.0, 1) if total_orig > 0 else 0.0
    print(f"{'OVERALL TOTALS':<28} | {total_orig:>9,} | {total_comp:>9,} | {total_saved:>8,} | {overall_pct:>8.1f}% |")
    print("=" * 95 + "\n")

    return results


if __name__ == "__main__":
    run_benchmark()
