# src/server.py
from __future__ import annotations

import argparse
import json
import os
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

from .executor import run_assessment

APP_NAME = "green-agent"
A2A_VERSION = "0.1"

app = FastAPI(title=f"{APP_NAME} (A2A)", version=A2A_VERSION)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "service": APP_NAME, "a2a_version": A2A_VERSION}


@app.get("/.well-known/agent-card.json")
async def agent_card(request: Request) -> Dict[str, Any]:
    """
    Return complete A2A-compliant agent card with dynamically computed URL.
    Uses Host header to get the correct hostname (e.g. green-agent:9009).
    """
    # Get the Host header from the request
    host = request.headers.get("host", "localhost:9009")
    scheme = request.url.scheme or "http"
    endpoint = f"{scheme}://{host}"

    # 额外把我们计算出来的 endpoint 打到日志里（你看 runner 日志就能知道 client 应该连哪）
    print(f"[agent-card] advertising endpoint = {endpoint} (Host: {host})", flush=True)

    return {
        "name": APP_NAME,
        "description": "Green agent (Traffic Light) - A2A compatible benchmark host",
        "version": A2A_VERSION,
        "url": endpoint,
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
        },
        "skills": [
            {
                "id": "evaluate",
                "name": "Evaluate",
                "description": "Run benchmark evaluation and return auditable results.",
                "tags": ["benchmark", "evaluation", "legal"],
                "examples": ["Evaluate a purple agent on the provided A2A scenario."],
                "inputModes": ["text"],
                "outputModes": ["text"],
            }
        ],
    }


def _make_completed_task(req_id: Any, context_id: Optional[str], result_obj: Dict[str, Any]) -> Dict[str, Any]:
    task_id = result_obj.get("task_id") or f"task_{uuid.uuid4().hex}"
    ctx = context_id or task_id

    # Pack result as an artifact (JSON)
    task = {
        "kind": "task",
        "id": task_id,
        "contextId": ctx,
        "status": {"state": "completed"},
        "artifacts": [
            {
                "artifactId": f"artifact_{uuid.uuid4().hex}",
                "name": "assessment_result",
                "parts": [{"kind": "data", "data": result_obj}],
            }
        ],
    }
    return {"jsonrpc": "2.0", "id": req_id, "result": task}


async def _handle_a2a_message(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accept A2A message payload. We try to find assessment payload in:
      params.message.parts[].data  OR params.payload OR params itself.
    """
    msg = params.get("message") or {}
    context_id = msg.get("contextId")

    payload: Optional[Dict[str, Any]] = None
    parts = msg.get("parts") or []
    for p in parts:
        if isinstance(p, dict) and p.get("kind") == "data" and isinstance(p.get("data"), dict):
            payload = p["data"]
            break

    if payload is None:
        payload = params.get("payload")
    if payload is None:
        payload = params if isinstance(params, dict) else {}

    if not isinstance(payload, dict):
        payload = {}

    # Debug: log received payload
    print(f"[executor] Received payload: {json.dumps(payload, indent=2)}", flush=True)

    # Transform participants from array to dict if needed
    participants = payload.get("participants")
    if isinstance(participants, list):
        # Convert from [{"role": "name", "endpoint": "url"}] to {"name": "url"}
        participants_dict = {}
        for p in participants:
            if isinstance(p, dict):
                role = p.get("role") or p.get("name")
                endpoint = p.get("endpoint") or p.get("url")
                if role and endpoint:
                    participants_dict[role] = endpoint
        payload["participants"] = participants_dict
        print(f"[executor] Transformed participants: {participants_dict}", flush=True)

    result_obj = await run_assessment(payload)
    result_obj.setdefault("context_id", context_id)
    return result_obj


async def _jsonrpc_dispatch(body: Dict[str, Any]) -> Dict[str, Any]:
    req_id = body.get("id")
    method = body.get("method")
    params = body.get("params") or {}

    # 关键：agentbeats-client 用 JSON-RPC transport（你日志里就是 jsonrpc.py）
    if method in ("message/send", "message/stream"):
        result_obj = await _handle_a2a_message(params)
        context_id = (params.get("message") or {}).get("contextId")
        return _make_completed_task(req_id, context_id, result_obj)

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


def _sse(obj: Dict[str, Any]) -> str:
    return "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"


# 多挂几个路径，避免 client 期望的 base path 和你不同导致 404
@app.post("/")
@app.post("/a2a")
@app.post("/a2a/{assistant_id}")
async def a2a_jsonrpc(request: Request, assistant_id: Optional[str] = None):
    body = await request.json()

    # 打印 client 实际发到哪个 path（你下次日志里能看到）
    print(f"[jsonrpc] path={request.url.path} method={body.get('method')} id={body.get('id')}", flush=True)

    if body.get("method") == "message/stream":
        async def gen():
            resp = await _jsonrpc_dispatch(body)
            yield _sse(resp)
        return StreamingResponse(gen(), media_type="text/event-stream")

    resp = await _jsonrpc_dispatch(body)
    return JSONResponse(content=resp)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=9009)
    p.add_argument("--card-url", required=False)  # 我们不再依赖它
    args = p.parse_args()

    uvicorn.run(app, host=args.host, port=args.port, log_level="info", access_log=True)


if __name__ == "__main__":
    main()
