from __future__ import annotations

import os
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ---------- Agent Card (A2A) ----------
# 注意：capabilities 必须是 dict；skills[*].tags 必须存在
AGENT_CARD: Dict[str, Any] = {
    "name": "green-agent",
    "description": "LegalAgentBench Green Agent (A2A host)",
    "version": "0.1.0",
    # 重要：这里给一个可访问的 base url（AgentBeats 容器内访问不靠这个字段，但 schema 要求有）
    "url": os.getenv("PUBLIC_BASE_URL", "http://localhost:9009"),
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
    "capabilities": {
        # 先不做 streaming，避免客户端走 stream 分支
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


# ---------- FastAPI ----------
app = FastAPI(title="Green Agent", version="0.1.0")


@app.get("/.well-known/agent-card.json")
def get_agent_card():
    return JSONResponse(AGENT_CARD)


@app.get("/healthz")
def healthz():
    return {"ok": True, "log_level": os.getenv("LOG_LEVEL", "INFO")}


@app.get("/")
def root():
    # 防止有人 GET / 看到 404
    return {"ok": True, "service": "green-agent"}


# ---------- Minimal A2A JSON-RPC ----------
# AgentBeats / a2a client 会 POST 到 http://host:port/ (根路径)
# 常见 method: message/send, tasks/get
_TASK_STORE: Dict[str, Dict[str, Any]] = {}


def _jsonrpc_error(req_id: Any, code: int, message: str, data: Optional[Any] = None):
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "error": err})


def _extract_text(params: Dict[str, Any]) -> str:
    """
    A2A message parts: [{"kind":"text","text":"..."}]
    """
    msg = (params or {}).get("message") or {}
    parts = msg.get("parts") or []
    texts = []
    for p in parts:
        if isinstance(p, dict) and p.get("kind") == "text" and isinstance(p.get("text"), str):
            texts.append(p["text"])
    return "\n".join(texts).strip()


@app.post("/")
async def a2a_jsonrpc(request: Request):
    payload = await request.json()
    req_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}

    # ---- message/send ----
    if method == "message/send":
        user_text = _extract_text(params)

        # 先用“回显”方式跑通 pipeline：你后续把这里替换成真正 evaluate 流程即可
        # 比如：解析 scenario -> 调用 purple agent -> 打分 -> 生成 results.json
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

    # ---- unknown method ----
    return _jsonrpc_error(req_id, -32601, f"Method not found: {method}")
