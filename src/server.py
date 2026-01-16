# src/server.py
from __future__ import annotations

import argparse
import os
from typing import Any, Dict

from fastapi import FastAPI, Request
import uvicorn

from .executor import run_assessment

app = FastAPI()

# --- Minimal "agent card" ---
@app.get("/.well-known/agent-card.json")
def agent_card() -> Dict[str, Any]:
    # card_url 会在 main() 里通过 env 注入，避免全局变量不好测
    card_url = os.environ.get("CARD_URL", "")
    return {
        "name": "green-agent",
        "description": "Green agent (legal eval) A2A server",
        "a2a": {
            "version": "0.1",
            "endpoint": card_url,  # 关键：必须是 runner 传进来的可访问 URL
        },
    }

# --- A2A entrypoint: assessment_request ---
@app.post("/a2a/assessment_request")
async def assessment_request(req: Request) -> Dict[str, Any]:
    payload = await req.json()
    # payload 应该包含 participants/config
    result = await run_assessment(payload)
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=9009)
    p.add_argument("--card-url", required=True)  # runner 必传
    args = p.parse_args()

    os.environ["CARD_URL"] = args.card_url

    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
