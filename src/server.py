# src/server.py
from __future__ import annotations

import argparse
import os
from typing import Any, Dict

from fastapi import FastAPI, Request
import uvicorn

from .executor import run_assessment

app = FastAPI(title="Green Agent (A2A)")

# -----------------------------
# Agent Card (A2A discovery)
# -----------------------------
@app.get("/.well-known/agent-card.json")
def agent_card() -> Dict[str, Any]:
    card_url = os.environ.get("CARD_URL", "")
    return {
        "name": "green-agent",
        "description": "Legal evaluation green agent (AgentBeats A2A)",
        "a2a": {
            "version": "0.1",
            "endpoint": card_url,
        },
    }

# -----------------------------
# A2A entrypoint
# -----------------------------
@app.post("/a2a/assessment_request")
async def assessment_request(req: Request) -> Dict[str, Any]:
    payload = await req.json()
    return await run_assessment(payload)

# -----------------------------
# Main
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="Green Agent A2A Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9009)
    parser.add_argument("--card-url", required=True)

    args = parser.parse_args()

    # runner 传进来的 card-url 要注入到 card 里
    os.environ["CARD_URL"] = args.card_url

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
    )

if __name__ == "__main__":
    main()
