# scripts/run_audit_resume.py

from __future__ import annotations

import requests
import os
import sys

# 关键：把项目根目录加入 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
import json
import time
from typing import Any, Dict, List, Optional, Set

from tqdm import tqdm

from src.green_rag_engine import GreenRAGEngine
from src.traffic_light_eval import TrafficLightAuditor
# scripts/run_audit_resume.py
def _unwrap_raw_audit(obj, max_depth=10):
    depth = 0
    cur = obj
    while depth < max_depth and isinstance(cur, dict) and isinstance(cur.get("raw_audit"), dict):
        cur = cur["raw_audit"]
        depth += 1
    return cur

def _sanitize_record(rec: dict) -> dict:
    ra = rec.get("raw_audit")
    inner = _unwrap_raw_audit(ra)
    if isinstance(inner, dict) and "raw_audit" in inner:
        inner = dict(inner)
        inner.pop("raw_audit", None)
    rec["raw_audit"] = inner
    if isinstance(rec.get("raw_audit"), dict):
        for k in ("answer", "fact", "verified_context", "id"):
            rec["raw_audit"].pop(k, None)
    return rec

def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # 🔒 FINAL SAFETY NET: flatten raw_audit before writing
    obj = _sanitize_record(obj)

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")



def read_done_ids(jsonl_path: str) -> Set[str]:
    done: Set[str] = set()
    if not os.path.exists(jsonl_path):
        return done
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                _id = str(obj.get("id", ""))
                if _id:
                    done.add(_id)
            except Exception:
                continue
    return done


def normalize_item(item: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """
    尽量兼容 dataset 的不同字段名。
    你可以之后按你的真实 schema 再精简。
    """
    # 给每条数据一个稳定 id（优先用数据里自带的 id）
    _id = item.get("id") or item.get("qid") or item.get("uuid") or f"idx_{idx}"
    _id = str(_id)

    # 常见字段名兜底
    fact = (
        item.get("original_fact")
        or item.get("question")
        or item.get("query")
        or item.get("prompt")
        or ""
    )

    answer = (
        item.get("answer")
        or item.get("response")
        or item.get("model_answer")
        or item.get("output")
        or ""
    )

    return {
        "id": _id,
        "fact": fact,
        "answer": answer,
        "raw": item,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="data/dataset.json")
    parser.add_argument("--out_jsonl", default="output/audit_results.jsonl")
    parser.add_argument("--report", default="output/final_audit_report.json")
    parser.add_argument("--limit", type=int, default=0, help="0 means all")
    parser.add_argument("--start", type=int, default=0, help="start index in dataset")
    parser.add_argument("--sleep", type=float, default=0.0, help="sleep seconds per item")
    parser.add_argument("--retries", type=int, default=2, help="retries per item on API error")
    args = parser.parse_args()

    # 1. 【新增】从环境变量获取 Purple Agent 的地址
    # AgentBeats 运行容器时，通常会把对方的地址通过环境变量传进来
    # 如果本地测试，可以默认填 http://localhost:8080/chat (取决于 Purple Agent 端口)
    purple_url = os.getenv("PURPLE_AGENT_URL") 
    if not purple_url:
        print("Warning: PURPLE_AGENT_URL not set. Make sure to set it via -e or assume local.")

    dataset = load_json(args.dataset)
    

    # dataset 可能是 dict 包一层，也可能直接是 list
    if isinstance(dataset, dict):
        # 常见 key：data / items / samples
        for k in ["data", "items", "samples", "dataset"]:
            if k in dataset and isinstance(dataset[k], list):
                dataset = dataset[k]
                break

    if not isinstance(dataset, list):
        raise RuntimeError(f"dataset format unexpected: {type(dataset)}")

    total_n = len(dataset)
    start = max(0, args.start)
    end = total_n if args.limit <= 0 else min(total_n, start + args.limit)

    done_ids = read_done_ids(args.out_jsonl)

    rag = GreenRAGEngine()
    auditor = TrafficLightAuditor()  # 会优先读取环境变量 JUDGE_MODEL

    stats = {
        "total": 0,
        "skipped_done": 0,
        "green": 0,
        "yellow": 0,
        "red": 0,
        "errors": 0,
        "avg_score_sum": 0.0,
        "avg_score_count": 0,
        "model": os.getenv("JUDGE_MODEL", ""),
        "dataset": args.dataset,
        "out_jsonl": args.out_jsonl,
        "start": start,
        "end": end,
    }

    pbar = tqdm(range(start, end), total=(end - start))
    for idx in pbar:
        item = dataset[idx]
        if not isinstance(item, dict):
            item = {"value": item}

        norm = normalize_item(item, idx)
        _id = norm["id"]

        if _id in done_ids:
            stats["skipped_done"] += 1
            continue

        fact = str(norm["fact"])
        # answer = str(norm["answer"])
        # 新代码（实时调用 Purple Agent）：
        answer = ""
        fetch_error = None
        
        # 只有在设置了 URL 时才去请求，否则 fallback 到文件里的答案（方便本地调试）
        if purple_url:
            try:
                # 构造请求体：这取决于你的 Purple Agent 期望什么格式
                # 常见格式 1: {"query": "问题..."}
                # 常见格式 2: {"messages": [{"role": "user", "content": "问题..."}]}
                payload = {"query": fact} 
                
                # 发送 POST 请求
                resp = requests.post(purple_url, json=payload, timeout=60)
                resp.raise_for_status()
                
                # 解析返回结果：同样取决于 Purple Agent 返回什么格式
                resp_json = resp.json()
                answer = resp_json.get("answer") or resp_json.get("response") or resp_json.get("output") or str(resp_json)
                
            except Exception as e:
                fetch_error = f"PurpleAgentCallError: {str(e)}"
                print(f"\n[Error] Failed to call Purple Agent for id={_id}: {e}")
        else:
            # 如果没配 URL，兼容旧模式，读文件里的答案
            answer = str(norm["answer"])

        # 如果请求失败或没拿到答案，记录错误并跳过后续打分
        if fetch_error or not answer:
            stats["errors"] += 1
            append_jsonl(args.out_jsonl, {
                "id": _id,
                "error": fetch_error or "Empty answer from Purple Agent",
                "fact": fact,
                "answer": ""
            })
            continue

        # 你的原脚本里是 rag.retrieve_ground_truth(original_fact)
        verified_context = rag.retrieve_ground_truth(fact)

        last_err: Optional[str] = None
        audit: Optional[Dict[str, Any]] = None

        for attempt in range(args.retries + 1):
            try:
                audit = auditor.evaluate_signal(fact, verified_context, answer)
                last_err = None
                break
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
                time.sleep(1.5 * (attempt + 1))

        if audit is None:
            stats["errors"] += 1
            append_jsonl(args.out_jsonl, {
                "id": _id,
                "error": last_err,
                "fact": fact,
                "answer": answer,
            })
            continue

        signal = str(audit.get("signal") or audit.get("verdict") or "YELLOW").upper()
        score = float(audit.get("score", 0.5))

        stats["total"] += 1
        stats["avg_score_sum"] += score
        stats["avg_score_count"] += 1

        if signal == "GREEN":
            stats["green"] += 1
        elif signal == "RED":
            stats["red"] += 1
        else:
            stats["yellow"] += 1

        append_jsonl(args.out_jsonl, {
            "id": _id,
            "signal": signal,
            "score": score,
            "reason": audit.get("reason", ""),
            "raw_audit": audit,
            "fact": fact,
            "answer": answer,
            "verified_context": verified_context,
        })

        done_ids.add(_id)

        # 进度条显示
        avg = (stats["avg_score_sum"] / stats["avg_score_count"]) if stats["avg_score_count"] else 0.0
        pbar.set_postfix({
            "G": stats["green"],
            "Y": stats["yellow"],
            "R": stats["red"],
            "err": stats["errors"],
            "avg": f"{avg:.3f}",
        })

        if args.sleep > 0:
            time.sleep(args.sleep)

        # 每 200 条顺手更新一次报告（防崩）
        if stats["total"] % 200 == 0:
            avg = (stats["avg_score_sum"] / stats["avg_score_count"]) if stats["avg_score_count"] else 0.0
            report = dict(stats)
            report["avg_score"] = avg
            with open(args.report, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

    # 最终报告
    avg = (stats["avg_score_sum"] / stats["avg_score_count"]) if stats["avg_score_count"] else 0.0
    report = dict(stats)
    report["avg_score"] = avg
    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Results appended to: {args.out_jsonl}")
    print(f"Report written to: {args.report}")


if __name__ == "__main__":
    main()
