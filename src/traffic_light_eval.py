# 实现 "Traffic Light" & "HalluGraph" 审计器
import json
from .utils import LLM
 # 复用 agents.py 里的 LLM 调用函数

class TrafficLightAuditor:
    def __init__(self, model_name="gemini-1.5-flash"):
        self.model_name = model_name
        
    def extract_triples(self, text):
        """
        [HalluGraph Lite]
        从文本中提取 (Subject, Predicate, Object) 三元组，模拟 Knowledge Graph 构建。
        """
        prompt = f"""
        Extract key legal claims from the text below as structured triples (Entity, Relationship, Value).
        Text: {text}
        Output format: JSON list of triples.
        """
        return LLM(prompt, self.model_name)

    def evaluate_signal(self, query, agent_response, ground_truth_docs):
        """
        核心评价逻辑：Traffic Light System
        """
        gt_text = "\n".join(ground_truth_docs)
        
        prompt = f"""
        You are a Senior Legal Auditor (Green Agent).
        
        [Query]: {query}
        [Agent Response]: {agent_response}
        [Ground Truth Laws/Facts]: {gt_text}
        
        Task: 
        1. Compare the Agent Response against Ground Truth.
        2. Assign a Traffic Light Signal:
           - GREEN: Answer is correct AND fully supported by Ground Truth.
           - YELLOW: Answer is correct but reasoning/citations are missing or vague.
           - RED: Answer contradicts Ground Truth OR hallucinates non-existent laws.
        
        Output JSON: {{ "signal": "GREEN/YELLOW/RED", "reason": "...", "score": 0-1 }}
        """
        
        result = LLM(prompt, self.model_name)
        try:
            return json.loads(result)
        except:
            return {"signal": "RED", "reason": "Parse Error", "score": 0}
