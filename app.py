from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse


def _fallback_agent_card() -> dict:
    """
    Minimal AgentBeats-compatible agent card.

    The agentbeats-client validates this JSON with Pydantic; at minimum it expects:
      - url (top-level)
      - skills (top-level list; each item needs at least 'name')
      - capabilities (list; if provided, items need at least 'name')
    """
    # In containers, localhost is fine for self-reference (AgentBeats talks to the container via service healthcheck).
    # If you want to override, set AGENT_URL (or AGENT_HOST) in env.
    url = os.getenv("AGENT_URL") or os.getenv("AGENT_HOST") or "http://localhost:9009"

    return {
        "name": "green-agent",
        "description": "LegalAgentBench Green Agent (A2A host)",
        "version": "0.1.0",
        "url": url,
        "skills": [
            {
                "name": "evaluate",
                "description": "Run benchmark evaluation and return auditable results.",
            }
        ],
        "capabilities": [
            {
                "name": "a2a",
                "description": "Agent-to-Agent compatible host.",
            }
        ],
    }


def _normalize_card(card: dict) -> dict:
    """
    Ensure required fields exist even if agents.py provides an incomplete card.
    """
    url = os.getenv("AGENT_URL") or os.getenv("AGENT_HOST") or "http://localhost:9009"

    out = dict(card) if isinstance(card, dict) else {}

    # Required top-level fields
    out.setdefault("name", "green-agent")
    out.setdefault("description", "LegalAgentBench Green Agent (A2A host)")
    out.setdefault("version", "0.1.0")
    out.setdefault("url", url)

    # Required skills list
    skills = out.get("skills")
    if not isinstance(skills, list) or len(skills) == 0:
        out["skills"] = _fallback_agent_card()["skills"]
    else:
        # Ensure each skill has at least a name
        fixed_skills = []
        for i, s in enumerate(skills):
            if isinstance(s, dict):
                s2 = dict(s)
                s2.setdefault("name", f"skill_{i}")
                fixed_skills.append(s2)
        if not fixed_skills:
            fixed_skills = _fallback_agent_card()["skills"]
        out["skills"] = fixed_skills

    # Capabilities: if present, make sure items have 'name'
    caps = out.get("capabilities")
    if caps is None:
        # Provide a minimal capability to satisfy stricter schemas (safe default)
        out["capabilities"] = _fallback_agent_card()["capabilities"]
    elif isinstance(caps, list):
        fixed_caps = []
        for i, c in enumerate(caps):
            if isinstance(c, dict):
                c2 = dict(c)
                c2.setdefault("name", f"capability_{i}")
                fixed_caps.append(c2)
        out["capabilities"] = fixed_caps
    else:
        out["capabilities"] = _fallback_agent_card()["capabilities"]

    return out


def _load_agent_card() -> dict:
    """
    Returns an agent-card dict for:
      GET /.well-known/agent-card.json

    Priority:
      1) If agents.py exposes a dict named AGENT_CARD, use it
      2) Else if agents.py exposes get_agent_card(), use it
      3) Else fallback minimal valid card

    In all cases we normalize to include required fields.
    """
    try:
        import agents  # agents.py in repo root

        if hasattr(agents, "AGENT_CARD") and isinstance(getattr(agents, "AGENT_CARD"), dict):
            return _normalize_card(getattr(agents, "AGENT_CARD"))

        if hasattr(agents, "get_agent_card") and callable(getattr(agents, "get_agent_card")):
            card = agents.get_agent_card()
            if isinstance(card, dict):
                return _normalize_card(card)

    except Exception:
        # Keep server alive even if import fails
        pass

    return _fallback_agent_card()


app = FastAPI(title="Green Agent", version="0.1.0")


@app.get("/.well-known/agent-card.json")
def agent_card():
    return JSONResponse(_load_agent_card())


@app.get("/healthz")
def healthz():
    return {"ok": True, "log_level": os.getenv("LOG_LEVEL", "INFO")}
