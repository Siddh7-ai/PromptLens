import os
import json
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, HTMLResponse

from src.compress.json_compressor import compress_json
from src.compress.text_compressor import compress_text
from src.store.retrieval_store import get_global_store
from src.proxy.stats import get_global_metrics
from src.proxy.dashboard_html import DASHBOARD_HTML

retrieval_store = get_global_store()
metrics_tracker = get_global_metrics()

TARGET_BASE_URL = os.getenv("TARGET_BASE_URL", "https://api.anthropic.com").rstrip("/")

app = FastAPI(title="PromptLens Proxy", version="0.1.0")

# Headers that shouldn't be forwarded directly between client and upstream
HOP_BY_HOP_HEADERS = {
    "host",
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-length",
}

RETRIEVE_ORIGINAL_TOOL = {
    "name": "retrieve_original",
    "description": "Retrieve full uncompressed original content for a compressed tool output using its unique hash ID.",
    "input_schema": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "The unique hash ID of the compressed content to retrieve."
            }
        },
        "required": ["id"]
    }
}

MIN_COMPRESS_TOKENS = 150
MIN_COMPRESS_BYTES = 300


def _filter_headers(headers: httpx.Headers | dict) -> dict:
    """Filter out hop-by-hop headers."""
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }


def _compress_tool_content(content: str) -> tuple[str, str | None, float]:
    """
    Compress string or JSON content if it exceeds length thresholds.
    Returns: (new_content, hash_id_if_compressed, compression_ratio)
    """
    if len(content) < MIN_COMPRESS_BYTES:
        return content, None, 0.0

    # Try JSON compression first
    try:
        json_obj = json.loads(content)
        if isinstance(json_obj, (dict, list)):
            result = compress_json(content)
            if result.is_compressed:
                stored_id = retrieval_store.save(content)
                savings_pct = f"{(result.compression_ratio * 100):.1f}%"
                notice = f"\n\n[PromptLens: Content compressed (saved {savings_pct} tokens). Original ID: {stored_id}. Call retrieve_original(id=\"{stored_id}\") if full data is required.]"
                return result.compressed_str + notice, stored_id, result.compression_ratio
    except Exception:
        pass

    # Fallback to Text compression
    result = compress_text(content)
    if result.is_compressed:
        stored_id = retrieval_store.save(content)
        savings_pct = f"{(result.compression_ratio * 100):.1f}%"
        notice = f"\n\n[PromptLens: Content compressed (saved {savings_pct} tokens). Original ID: {stored_id}. Call retrieve_original(id=\"{stored_id}\") if full data is required.]"
        return result.compressed_str + notice, stored_id, result.compression_ratio

    return content, None, 0.0


def process_anthropic_payload(payload: dict) -> dict:
    """
    Inspect and modify Anthropic payload:
    1. Compress tool_result content in user messages and save original to retrieval_store.
    2. Intercept retrieve_original tool call results and substitute full original content.
    3. Inject retrieve_original tool definition into tools list if tools exist AND content was compressed.
    """
    if not isinstance(payload, dict):
        return payload

    has_compressed_items = False
    messages = payload.get("messages")
    if isinstance(messages, list):
        # Map tool_use_id -> tool_name from assistant messages
        tool_use_map = {}
        for msg in messages:
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                content_blocks = msg.get("content")
                if isinstance(content_blocks, list):
                    for block in content_blocks:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            t_id = block.get("id")
                            t_name = block.get("name")
                            t_input = block.get("input", {})
                            if t_id:
                                tool_use_map[t_id] = {"name": t_name, "input": t_input}

        # Process user messages for tool_result blocks
        for msg in messages:
            if isinstance(msg, dict) and msg.get("role") == "user":
                content_blocks = msg.get("content")
                if isinstance(content_blocks, list):
                    for block in content_blocks:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            t_id = block.get("tool_use_id")
                            t_info = tool_use_map.get(t_id, {})

                            # Check if tool_result is for retrieve_original
                            if t_info.get("name") == "retrieve_original":
                                requested_id = t_info.get("input", {}).get("id")
                                if requested_id and retrieval_store.has(requested_id):
                                    block["content"] = retrieval_store.get(requested_id)
                                    metrics_tracker.record_retrieval()
                                    continue

                            # Compress tool result content
                            raw_content = block.get("content")
                            if isinstance(raw_content, str):
                                if retrieval_store.has(raw_content):
                                    block["content"] = retrieval_store.get(raw_content)
                                    metrics_tracker.record_retrieval()
                                    continue

                                new_content, stored_id, _ = _compress_tool_content(raw_content)
                                if stored_id:
                                    block["content"] = new_content
                                    has_compressed_items = True

                            elif isinstance(raw_content, list):
                                new_list = []
                                for sub_block in raw_content:
                                    if isinstance(sub_block, dict) and sub_block.get("type") == "text":
                                        txt = sub_block.get("text", "")
                                        new_txt, stored_id, _ = _compress_tool_content(txt)
                                        if stored_id:
                                            sub_block["text"] = new_txt
                                            has_compressed_items = True
                                    new_list.append(sub_block)
                                block["content"] = new_list

    # Inject retrieve_original tool definition if tools present and compression occurred
    tools = payload.get("tools")
    if isinstance(tools, list) and has_compressed_items:
        if not any(isinstance(t, dict) and t.get("name") == "retrieve_original" for t in tools):
            tools.append(RETRIEVE_ORIGINAL_TOOL)

    return payload



@app.get("/health")
async def health_check():
    """Health check endpoint for proxy monitoring."""
    return {
        "status": "ok",
        "target_url": TARGET_BASE_URL
    }


@app.get("/api/stats")
async def get_stats():
    """JSON API endpoint returning real-time proxy metrics and recent request logs."""
    return metrics_tracker.get_summary()


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Headroom-style Web Dashboard UI."""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_passthrough(request: Request, path: str):
    """
    HTTP passthrough proxy with compression, metrics tracking, and tool injection for Anthropic API.
    """
    target_url = f"{TARGET_BASE_URL}/{path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    body = await request.body()
    request_headers = _filter_headers(request.headers)

    baseline_tokens = len(body.decode("utf-8", errors="ignore").split())
    compressed_tokens = baseline_tokens
    stored_hash_id = None

    # Apply compression & tool injection for /v1/messages
    if path.rstrip("/") == "v1/messages" and body:
        try:
            payload = json.loads(body)
            processed_payload = process_anthropic_payload(payload)
            body = json.dumps(processed_payload).encode("utf-8")

            # Calculate token metrics for stats
            from src.compress.text_compressor import get_token_count
            baseline_tokens = get_token_count(json.dumps(payload))
            compressed_tokens = get_token_count(json.dumps(processed_payload))
        except Exception:
            pass

    metrics_tracker.record_request(
        path=f"/{path}",
        method=request.method,
        baseline_tokens=baseline_tokens,
        compressed_tokens=compressed_tokens,
        retrieval_id=stored_hash_id
    )

    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        upstream_req = client.build_request(
            method=request.method,
            url=target_url,
            headers=request_headers,
            content=body
        )

        upstream_resp = await client.send(upstream_req, stream=True)

        response_headers = _filter_headers(upstream_resp.headers)
        status_code = upstream_resp.status_code

        is_streaming = (
            "text/event-stream" in response_headers.get("content-type", "").lower()
            or "chunked" in response_headers.get("transfer-encoding", "").lower()
        )

        if is_streaming:
            async def generate_chunks():
                try:
                    async for chunk in upstream_resp.aiter_bytes():
                        yield chunk
                finally:
                    await upstream_resp.aclose()

            return StreamingResponse(
                generate_chunks(),
                status_code=status_code,
                headers=response_headers,
                media_type=response_headers.get("content-type")
            )

        response_body = await upstream_resp.aread()
        await upstream_resp.aclose()

        return Response(
            content=response_body,
            status_code=status_code,
            headers=response_headers,
            media_type=response_headers.get("content-type")
        )

