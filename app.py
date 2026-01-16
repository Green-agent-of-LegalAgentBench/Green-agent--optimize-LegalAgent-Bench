from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# If you have a canonical agent definition in agents.py, we try to load it.
# This keeps the server compatible even if the agent object name differs.
def _load_agent_card() -> dict:
    """
    Returns an agent-card dict for:
      GET /.well-known/agent-card.json

    Priority:
      1) If agents.py exposes a dict named AGENT_CARD, use it
      2) Else, return a minimal valid card
    """
    try:
        import agents  # agents.py in repo root

        # Option A: you already define a card dict
        if hasattr(agents, "AGENT_CARD") and isinstance(getattr(agents, "AGENT_CARD"), dict):
            return getattr(agents, "AGENT_CARD")

        # Option B: if you have a function to build card
        if hasattr(agents, "get_agent_card") and callable(getattr(agents, "get_agent_card")):
            card = agents.get_agent_card()
            if isinstance(card, dict):
                return card
    except Exception:
        # Keep server alive even if import fails
        pass

    # Fallback minimal card (enough for healthcheck + basic discovery)
    return {
        "name": "green-agent",
        "description": "LegalAgentBench Green Agent (A2A host)",
        "version": "0.1.0",
        "capabilities": [],
    }


app = FastAPI(title="Green Agent", version="0.1.0")


@app.get("/.well-known/agent-card.json")
def agent_card():
    return JSONResponse(_load_agent_card())


@app.get("/healthz")
def healthz():
    return {"ok": True, "log_level": os.getenv("LOG_LEVEL", "INFO")}
