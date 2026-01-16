# src/server.py
from __future__ import annotations

import argparse
import os
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from .executor import run_assessment

APP_NAME = "green-agent"
A2A_VERSION = "0.1"

# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
app: FastAPI = FastAPI(
    title=f"{APP_NAME} (A2A)",
    description="Traffic-Light / HalluGraph Green Agent for AgentBeats",
    version=A2A_VERSION,
)

# -----------------------------------------------------------------------------
# Health check (useful for local + CI)
# -----------------------------------------------------------------------------
@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "service": APP_NAME,
        "a2a_version": A2A_VERSION,
    }


# -----------------------------------------------------------------------------
# Agent Card (A2A discovery endpoint)
# -----------------------------------------------------------------------------
@app.get("/.well-known/agent-card.json")
def agent_card() -> Dict[str, Any]:
    """
    Minimal A2A agent card.

    IMPORTANT:
    - card_url MUST come from runner via --card-url
    - Do NOT hardcode localhost here
    """
    card_url: str = os.environ.get("CARD_URL", "")

    return {
        "name": APP_NAME,
        "description": "Green agent for legal hallucination auditing (Traffic Light)",
        "a2a": {
            "version": A2A_VERSION,
            "endpoint": card_url,
        },
        "endpoints": {
            "assessment_request": (
                f"{card_url}/a2a/assessment_request"
                if card_url
                else "/a2a/assessment_request"
            )
        },
    }


# -----------------------------------------------------------------------------
# A2A entrypoint: assessment_request
# -----------------------------------------------------------------------------
@app.post("/a2a/assessment_request")
async def assessment_request(request: Request) -> JSONResponse:
    """
    A2A-compatible assessment entrypoint.

    Expected payload (per tutorial):
    {
      "participants": { "<role>": "<endpoint_url>" },
      "config": { ... },
      "task_id": "optional"
    }
    """
    try:
        payload: Dict[str, Any] = await request.json()
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error": f"Invalid JSON payload: {e}"},
        )

    result: Dict[str, Any] = await run_assessment(payload)
    return JSONResponse(content=result)


# -----------------------------------------------------------------------------
# CLI entrypoint (AgentBeats runner uses this)
# -----------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Green Agent A2A Server (AgentBeats compatible)"
    )
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9009)
    parser.add_argument(
        "--card-url",
        type=str,
        required=True,
        help="Public URL advertised in agent card (passed by runner)",
    )

    args = parser.parse_args()

    # Runner injects the correct externally-reachable URL
    os.environ["CARD_URL"] = args.card_url

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
