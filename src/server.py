# src/server.py
from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from typing import Any, Dict, Optional
from urllib.parse import urlparse, urlunparse

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

from .executor import run_assessment

APP_NAME = "green-agent"
A2A_VERSION = "0.1"

app: FastAPI = FastAPI(title=f"{APP_NAME} (A2A)", version=A2A_VERSION)


def _normalize_base_url(card_url: str, request: Optional[Request], default_host: str, port: int) -> str:
    """
    Ensure the advertised A2A endpoint is reachable from other containers.

    If runner passes localhost/127.0.0.1/0.0.0.0, replace hostname with default_host (e.g. green-agent).
    If card_url is empty, fall back to request.base_url.
    """
    if not card_url:
        if request is not None:
            # e.g. http://green-agent:9009/
            base = str(request.base_url)
        else:
            base = f"http://{default_host}:{port}/"
    else:
        base = card_url if card_url.endswith("/") else card_url + "/"

    u = urlparse(base)
    host = (u.hostname or "").lower()

    if host in ("localhost", "127.0.0.1", "0.0.0.0", ""):
        # swap to docker service name
        netloc = f"{default_host}:{u.port or port}"
        u = u._replace(netloc=netloc)

    # strip trailing slash
    fixed = urlunparse(u).rstrip("/")
    return fixed


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "service": APP_NAME, "a2a_version": A2A_VERSION}


@app.get("/.well-known/agent-card.json")
async def agent_card(request: Request) -> Dict[str, Any]:
    # Runner passes this; might be localhost which is WRONG inside docker network
    card_url = os.environ.get("CARD_URL", "")
    port = int(os.environ.get("PORT", "9009"))

    # IMPORTANT: in compose the service name is usually "green-agent"
    service_host = os.environ.get("SERVICE_HOST", "green-agent")

    endpoint = _normalize_base_url(card_url, request, service_host, port)

    return {
        "name": APP_NAME,
        "description": "Green agent for legal hallucination auditing (Traffic Light)",
        "a2a": {
            "version": A2A_VERSION,
            # This is the JSON-RPC base endpoint other agents will POST to:
            "endpoint": endpoint,
        },
    }


def _make_task_from_result(req_id: Any, context_id: Optional[str], result_obj: Dict[str, Any]) -> Dict[str, Any]:
    task_id = result_obj.get("task_id") or f"task_{uuid.uuid4().hex}"
    artifacts = []

    # Pack everything into a single JSON artifact to keep MVP stable
    artifacts.append(
        {
            "artifactId": f"artifact_{uuid.uuid4().hex}",
            "name": "assessment_result",
            "parts": [
                {"kind": "data", "data": result_obj},
            ],
        }
    )

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "kind": "task",
            "id": task_id,
            "contextId": context_id or task_id,
            "status": {"state": "completed"},
            "artifacts": artifacts,
        },
    }


async def _handle_message(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract assessment payload from A2A message parts.
    We accept either:
      - parts contains {"kind":"data","data": {...payload...}}
      - params itself contains payload-like fields (fallback)
    """
    msg = params.get("message") or {}
    context_id = msg.get("contextId")

    payload: Optional[Dict[str, Any]] = None
    parts = msg.get("parts") or []
    for p in parts:
        if isinstance(p, dict) and p.get("kind") == "data" and isinstance(p.get("data"), dict):
            payload = p["data"]
            break

    # fallback if client sends direct
    if payload is None:
        payload = params.get("payload")
    if payload is None and isinstance(params, dict):
        # last resort: accept params as payload
        payload = params

    if not isinstance(payload, dict):
        payload = {}

    # run the actual assessment
    result_obj = await run_assessment(payload)
    result_obj.setdefault("context_id", context_id)
    return result_obj


async def _jsonrpc_dispatch(body: Dict[str, Any]) -> Any:
    req_id = body.get("id")
    method = body.get("method")
    params = body.get("params") or {}

    if method in ("message/send", "message/stream"):
        result_obj = await _handle_message(params)
        context_id = (params.get("message") or {}).get("contextId")
        return _make_task_from_result(req_id, context_id, result_obj)

    # Minimal support for tasks/get
    if method == "tasks/get":
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "tasks/get not implemented"}}

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


def _sse_event(obj: Dict[str, Any]) -> str:
    return "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"


@app.post("/")
@app.post("/a2a")
@app.post("/a2a/{assistant_id}")
async def a2a_jsonrpc(request: Request, assistant_id: Optional[str] = None):
    """
    A2A JSON-RPC endpoint. agentbeats-client uses JSON-RPC transport.
    For message/stream we return SSE.
    """
    try:
        body: Dict[str, Any] = await request.json()
    except Exception as e:
        return JSONResponse(status_code=400, content={"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}})

    method = body.get("method")
    if method == "message/stream":
        async def gen():
            # We emit exactly one completed task envelope as SSE (MVP)
            resp = await _jsonrpc_dispatch(body)
            yield _sse_event(resp)

        return StreamingResponse(gen(), media_type="text/event-stream")

    resp = await _jsonrpc_dispatch(body)
    return JSONResponse(content=resp)


def main() -> None:
    parser = argparse.ArgumentParser(description="Green Agent A2A Server (AgentBeats compatible)")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9009)
    parser.add_argument("--card-url", type=str, required=True)
    args = parser.parse_args()

    os.environ["CARD_URL"] = args.card_url
    os.environ["PORT"] = str(args.port)

    uvicorn.run(app, host=args.host, port=args.port, log_level="info", access_log=True)


if __name__ == "__main__":
    main()
