# src/executor.py
from __future__ import annotations

from typing import Any, Dict

# 你可以在这里调用你现有的模块
# from .traffic_light_eval import ...
# from .green_rag_engine import ...

async def run_assessment(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    payload 期望结构：
    {
      "participants": { "<role>": "<endpoint_url>" },
      "config": { ... }
    }
    """
    participants = payload.get("participants", {})
    config = payload.get("config", {})

    # TODO: 这里先返回一个最小可用结果，确保链路通
    # 后续再把你现有的 legal eval / traffic light scoring 接进来
    return {
        "ok": True,
        "received": {
            "participants": participants,
            "config_keys": list(config.keys()) if isinstance(config, dict) else None,
        },
        "results": {
            "score": 0,
            "notes": "stub executor - wire up your eval logic here",
        },
    }
