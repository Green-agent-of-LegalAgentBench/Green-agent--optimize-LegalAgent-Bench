from __future__ import annotations

import os
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ---------- Agent Card (A2A) ----------
AGENT_CARD: Dict[str, Any] = {
    "name": "green-agent",
    "description": "LegalAgentBench Green Agent (A2A host)",
    "version": "0.1.0",
    "url": os.getenv("PUBLIC_BASE_URL", "http://localhost:9009"),
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

app = FastAPI(title="Green Agent", version="0.1.0")

_TASK_STORE: Dict[str, Dict[str, Any]] = {}


@app.get("/.well-known/agent-card.json")
async def get_agent_card(request: Request):
    """
    Return agent card with dynamically computed URL.
    Uses request.base_url so other containers can reach us (e.g. http://green-agent:9009).
    """
    endpoint = str(request.base_url).rstrip("/")
    
    # Log the computed endpoint for debugging
    print(f"[agent-card] advertising endpoint = {endpoint}", flush=True)
    
    # Build agent card with dynamic URL
    card = {
        "name": AGENT_CARD["name"],
        "description": AGENT_CARD["description"],
        "version": AGENT_CARD["version"],
        "url": endpoint,  # Dynamic URL instead of hardcoded localhost
        "defaultInputModes": AGENT_CARD["defaultInputModes"],
        "defaultOutputModes": AGENT_CARD["defaultOutputModes"],
        "capabilities": AGENT_CARD["capabilities"],
        "skills": AGENT_CARD["skills"],
    }
    
    return JSONResponse(card)


@app.get("/healthz")
def healthz():
    return {"ok": True, "log_level": os.getenv("LOG_LEVEL", "INFO")}


@app.get("/")
def root():
    return {"ok": True, "service": "green-agent"}


def _jsonrpc_error(req_id: Any, code: int, message: str, data: Optional[Any] = None):
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "error": err})


def _extract_text(params: Dict[str, Any]) -> str:
    msg = (params or {}).get("message") or {}
    parts = msg.get("parts") or []
    texts = []
    for p in parts:
        if isinstance(p, dict) and p.get("kind") == "text" and isinstance(p.get("text"), str):
            texts.append(p["text"])
    return "\n".join(texts).strip()


async def _handle_jsonrpc(request: Request):
    # 有些客户端可能发非 JSON 或空 body，别让服务直接 500
    try:
        payload = await request.json()
    except Exception:
        return _jsonrpc_error(None, -32700, "Parse error: invalid JSON")

    req_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}

    # 兼容一些“探活/能力探测”的 method：直接给个 OK
    if method in ("ping", "health", "capabilities/get"):
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {"ok": True}})

    # ---- message/send ----
    if method == "message/send":
        user_text = _extract_text(params)

        reply_text = (
            "✅ Green Agent received your request.\n\n"
            "Echo:\n"
            f"{user_text}\n\n"
            "(Next: replace echo with real evaluation + auditable results.)"
        )

        task_id = str(uuid.uuid4())
        context_id = str(uuid.uuid4())

        result = {
            "id": task_id,
            "contextId": context_id,
            "status": {"state": "completed"},
            "artifacts": [
                {
                    "artifactId": str(uuid.uuid4()),
                    "name": "result",
                    "parts": [{"kind": "text", "text": reply_text}],
                }
            ],
            "kind": "task",
            "metadata": {},
        }

        _TASK_STORE[task_id] = result
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": result})

    # ---- tasks/get ----
    if method == "tasks/get":
        task_id = (params or {}).get("id")
        if not task_id or task_id not in _TASK_STORE:
            return _jsonrpc_error(req_id, -32004, "Task not found")
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": _TASK_STORE[task_id]})

    return _jsonrpc_error(req_id, -32601, f"Method not found: {method}")


@app.post("/")
async def jsonrpc_root(request: Request):
    return await _handle_jsonrpc(request)


@app.post("/jsonrpc")
async def jsonrpc_alt(request: Request):
    return await _handle_jsonrpc(request)


@app.post("/a2a")
async def jsonrpc_a2a(request: Request):
    return await _handle_jsonrpc(request)


@app.post("/rpc")
async def jsonrpc_rpc(request: Request):
    return await _handle_jsonrpc(request)
