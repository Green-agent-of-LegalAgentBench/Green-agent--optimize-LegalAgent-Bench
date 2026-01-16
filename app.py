from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.responses import JSONResponse


def _default_url() -> str:
    # In docker-compose, other containers reach us via service name.
    # AgentBeats requests: http://green-agent:9009/.well-known/agent-card.json
    return os.getenv("AGENT_URL") or os.getenv("AGENT_HOST") or "http://green-agent:9009"


def _fallback_agent_card() -> Dict[str, Any]:
    """
    Minimal A2A AgentCard compatible with the validator used by agentbeats-client.

    Requirements observed from errors:
      - capabilities: MUST be a dict/object (not list)
      - defaultInputModes: required list
      - defaultOutputModes: required list
      - skills: required list; each skill requires tags (and commonly id/name/modes)
    """
    return {
        "name": "green-agent",
        "description": "LegalAgentBench Green Agent (A2A host)",
        "url": _default_url(),
        "version": "0.1.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "skills": [
            {
                "id": "evaluate",
                "name": "Evaluate",
                "description": "Run benchmark evaluation and return auditable results.",
                "examples": ["Evaluate a purple agent on the provided A2A scenario."],
                "inputModes": ["text"],
                "outputModes": ["text"],
                "tags": ["evaluation", "benchmark", "legal"],
            }
        ],
    }


def _ensure_capabilities_dict(card: Dict[str, Any]) -> None:
    caps = card.get("capabilities")

    # If missing → set default
    if caps is None:
        card["capabilities"] = _fallback_agent_card()["capabilities"]
        return

    # If already dict → ensure keys exist
    if isinstance(caps, dict):
        caps.setdefault("streaming", False)
        caps.setdefault("pushNotifications", False)
        caps.setdefault("stateTransitionHistory", False)
        card["capabilities"] = caps
        return

    # If list/other type → coerce to defaults
    card["capabilities"] = _fallback_agent_card()["capabilities"]


def _ensure_modes(card: Dict[str, Any]) -> None:
    if not isinstance(card.get("defaultInputModes"), list) or not card["defaultInputModes"]:
        card["defaultInputModes"] = ["text"]
    if not isinstance(card.get("defaultOutputModes"), list) or not card["defaultOutputModes"]:
        card["defaultOutputModes"] = ["text"]


def _ensure_skills(card: Dict[str, Any]) -> None:
    skills = card.get("skills")

    if not isinstance(skills, list) or not skills:
        card["skills"] = _fallback_agent_card()["skills"]
        return

    fixed = []
    for i, s in enumerate(skills):
        if not isinstance(s, dict):
            continue

        s2 = dict(s)
        s2.setdefault("id", f"skill-{i}")
        s2.setdefault("name", s2["id"])
        s2.setdefault("description", "")

        # Some validators expect modes on each skill
        s2.setdefault("inputModes", card.get("defaultInputModes", ["text"]))
        s2.setdefault("outputModes", card.get("defaultOutputModes", ["text"]))

        # Required by your validator error
        s2.setdefault("tags", ["evaluation"])

        fixed.append(s2)

    if not fixed:
        fixed = _fallback_agent_card()["skills"]

    card["skills"] = fixed


def _normalize_card(card: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(card) if isinstance(card, dict) else {}

    out.setdefault("name", "green-agent")
    out.setdefault("description", "LegalAgentBench Green Agent (A2A host)")
    out.setdefault("version", "0.1.0")
    out.setdefault("url", _default_url())

    _ensure_capabilities_dict(out)
    _ensure_modes(out)
    _ensure_skills(out)

    return out


def _load_agent_card() -> Dict[str, Any]:
    """
    Priority:
      1) agents.py: AGENT_CARD (dict)
      2) agents.py: get_agent_card() -> dict
      3) fallback minimal valid A2A AgentCard
    Always normalize to satisfy validators.
    """
    try:
        import agents  # agents.py at repo root

        if hasattr(agents, "AGENT_CARD") and isinstance(getattr(agents, "AGENT_CARD"), dict):
            return _normalize_card(getattr(agents, "AGENT_CARD"))

        if hasattr(agents, "get_agent_card") and callable(getattr(agents, "get_agent_card")):
            card = agents.get_agent_card()
            if isinstance(card, dict):
                return _normalize_card(card)

    except Exception:
        # Keep server alive even if agents import fails
        pass

    return _fallback_agent_card()


app = FastAPI(title="Green Agent", version="0.1.0")


@app.get("/.well-known/agent-card.json")
def agent_card():
    return JSONResponse(_load_agent_card())


@app.get("/healthz")
def healthz():
    return {"ok": True, "log_level": os.getenv("LOG_LEVEL", "INFO")}
