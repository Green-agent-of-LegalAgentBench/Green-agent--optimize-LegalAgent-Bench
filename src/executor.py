# src/executor.py
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


# -----------------------------
# A2A-ish message helpers (no SDK required)
# -----------------------------
@dataclass
class TaskUpdate:
    task_id: str
    type: str  # "log" | "progress" | "warning"
    message: str
    data: Optional[Dict[str, Any]]
    ts: float


def _now() -> float:
    return time.time()


def _make_task_id() -> str:
    return f"task_{uuid.uuid4().hex}"


def _artifact(name: str, data: Any, mime: str = "application/json") -> Dict[str, Any]:
    return {"name": name, "mime_type": mime, "data": data}


# -----------------------------
# Traffic Light adapter (YOUR IMPLEMENTATION)
# -----------------------------
def _score_with_traffic_light(item: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Uses your src/traffic_light_eval.py TrafficLightAuditor.

    Returns normalized record:
    {
      "traffic_light": "GREEN|YELLOW|RED",
      "success_score": 0..1,
      "process_score": 0..1,
      "citation_score": 0..1,
      "safety_score": 0..1,
      "notes": str,
      "raw_audit": {...},
      "triples": [...] (optional),
      "query": str,
      "agent_response": str
    }
    """
    # ---- 1) Extract fields robustly (dataset schema may vary) ----
    query = (
        item.get("query")
        or item.get("question")
        or item.get("prompt")
        or item.get("input")
        or ""
    )

    agent_response = (
        item.get("agent_response")
        or item.get("response")
        or item.get("answer")
        or item.get("output")
        or ""
    )

    # ground truth docs might be list[str] or str or under other keys
    gt = (
        item.get("ground_truth_docs")
        or item.get("ground_truth")
        or item.get("references")
        or item.get("docs")
        or item.get("context")
        or []
    )

    if isinstance(gt, str):
        ground_truth_docs = [gt]
    elif isinstance(gt, list):
        # stringify non-str entries just in case
        ground_truth_docs = [x if isinstance(x, str) else json.dumps(x, ensure_ascii=False) for x in gt]
    elif isinstance(gt, dict):
        ground_truth_docs = [json.dumps(gt, ensure_ascii=False)]
    else:
        ground_truth_docs = [str(gt)]

    # Optional: model name override
    model_name = config.get("audit_model") or config.get("model_name") or "gemini-pro"
    enable_triples = bool(config.get("enable_triples", False))

    # ---- 2) Call your auditor ----
    from .traffic_light_eval import TrafficLightAuditor  # this matches your file/class

    auditor = TrafficLightAuditor(model_name=model_name)

    raw = auditor.evaluate_signal(
        query=query,
        agent_response=agent_response,
        ground_truth_docs=ground_truth_docs,
    )

    # raw expected: {"signal": "GREEN/YELLOW/RED", "reason": "...", "score": 0-1}
    signal = (raw.get("signal") or "RED").upper()
    if signal not in ("GREEN", "YELLOW", "RED"):
        signal = "YELLOW"

    score = raw.get("score", 0)
    try:
        success_score = float(score)
    except Exception:
        success_score = 0.0

    reason = raw.get("reason", "")

    # ---- 3) Derive auxiliary scores (heuristic, but stable) ----
    # process_score: green>yellow>red
    process_score = {"GREEN": 1.0, "YELLOW": 0.6, "RED": 0.0}[signal]

    # citation_score: if YELLOW often indicates missing/vague support => lower
    citation_score = {"GREEN": 1.0, "YELLOW": 0.3, "RED": 0.0}[signal]

    # safety_score: default 1.0 (can add rules later)
    safety_score = 1.0

    triples = None
    if enable_triples:
        # Your extract_triples returns LLM(...) result; may be JSON string.
        t = auditor.extract_triples(agent_response)
        try:
            triples = json.loads(t) if isinstance(t, str) else t
        except Exception:
            triples = t  # keep raw for audit

    out: Dict[str, Any] = {
        "traffic_light": signal,
        "success_score": max(0.0, min(1.0, success_score)),
        "process_score": process_score,
        "citation_score": citation_score,
        "safety_score": safety_score,
        "notes": reason,
        "raw_audit": raw,
        "query": query,
        "agent_response": agent_response,
    }
    if enable_triples:
        out["triples"] = triples

    return out


# -----------------------------
# Dataset loading
# -----------------------------
def _iter_dataset(dataset_path: str, max_items: Optional[int]) -> Iterable[Dict[str, Any]]:
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"dataset not found: {dataset_path}")

    if dataset_path.endswith(".jsonl"):
        with open(dataset_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if max_items is not None and i >= max_items:
                    break
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)
    else:
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
            data = data["items"]

        if not isinstance(data, list):
            raise ValueError("dataset json must be a list, or a dict with key 'items' as list")

        for i, item in enumerate(data):
            if max_items is not None and i >= max_items:
                break
            if isinstance(item, dict):
                yield item


# -----------------------------
# Core assessment runner
# -----------------------------
async def run_assessment(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aligns with tutorial:
    {
      "participants": { "<role>": "<endpoint_url>" },
      "config": { ... }
    }
    """
    task_id = payload.get("task_id") or _make_task_id()
    participants = payload.get("participants")
    config = payload.get("config") or {}

    if not isinstance(participants, dict) or not participants:
        return {"task_id": task_id, "status": "error", "error": "participants must be a non-empty dict"}

    dataset_path = config.get("dataset_path", "data/dataset.json")
    max_items = config.get("max_items", 50)
    emit_updates = bool(config.get("emit_updates", True))

    updates: List[Dict[str, Any]] = []

    def emit(t: str, msg: str, data: Optional[Dict[str, Any]] = None):
        if not emit_updates:
            return
        updates.append(TaskUpdate(task_id, t, msg, data, _now()).__dict__)

    emit("log", "assessment_started", {"participants": list(participants.keys())})
    emit("log", "loading_dataset", {"dataset_path": dataset_path, "max_items": max_items})

    per_item: List[Dict[str, Any]] = []
    counts = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    sums = {"success": 0.0, "process": 0.0, "citation": 0.0, "safety": 0.0}

    try:
        for idx, item in enumerate(_iter_dataset(dataset_path, max_items)):
            emit("progress", "scoring_item", {"index": idx})

            scored = _score_with_traffic_light(item, config)
            scored["index"] = idx
            per_item.append(scored)

            tl = scored["traffic_light"]
            counts[tl] = counts.get(tl, 0) + 1
            sums["success"] += float(scored.get("success_score", 0.0))
            sums["process"] += float(scored.get("process_score", 0.0))
            sums["citation"] += float(scored.get("citation_score", 0.0))
            sums["safety"] += float(scored.get("safety_score", 0.0))

        n = max(len(per_item), 1)
        summary = {
            "n": len(per_item),
            "avg_success": sums["success"] / n,
            "avg_process": sums["process"] / n,
            "avg_citation": sums["citation"] / n,
            "avg_safety": sums["safety"] / n,
            "traffic_light_counts": counts,
        }

        emit("log", "assessment_complete", summary)

        artifacts = [
            _artifact("summary.json", summary),
            _artifact("per_item.json", per_item),
            _artifact("task_updates.json", updates),
        ]

        return {
            "task_id": task_id,
            "status": "ok",
            "results": summary,
            "artifacts": artifacts,
            "updates": updates,
        }

    except Exception as e:
        emit("warning", "assessment_failed", {"error": str(e)})
        return {
            "task_id": task_id,
            "status": "error",
            "error": str(e),
            "updates": updates,
            "artifacts": [
                _artifact("task_updates.json", updates),
                _artifact("error.json", {"error": str(e)}),
            ],
        }
