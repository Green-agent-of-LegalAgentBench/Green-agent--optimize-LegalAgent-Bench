import sys
import os
import json
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.green_rag_engine import GreenRAGEngine
from src.traffic_light_eval import TrafficLightAuditor

def run_evaluation():
    # 配置路径
    output_file_path = './output/your_agent_result.json' # 你的 Purple Agent 输出文件
    dataset_path = './data/dataset.json'
    
    if not os.path.exists(output_file_path):
        print("未找到 Purple Agent 输出文件，请先运行 Agent 生成结果。")
        return

    # 加载组件
    rag = GreenRAGEngine()
    auditor = TrafficLightAuditor()
    
    # 加载数据
    with open(output_file_path, 'r') as f:
        agent_outputs = [json.loads(line) for line in f.readlines()]
    
    with open(dataset_path, 'r') as f:
        ground_truth_data = json.load(f)

    results = []
    
    print("=== 开始 Green Agent 审计 (Traffic Light System) ===")
    
    # 限制测试数量，方便调试 (上线时去掉 [:10])
    for i, item in enumerate(tqdm(agent_outputs[:10])): 
        
        # 1. 获取输入
        agent_response = item.get('res') or item.get('summary') or item.get('answer', '')
        # 对应 dataset 中的原始问题
        original_idx = i  # 假设顺序一致，如果不一致需要用 ID 匹配
        original_question = ground_truth_data[original_idx].get('question')

        # 2. Green Agent 独立检索 (SOTA Retrieval)
        # 不相信 Purple Agent 的检索，Green Agent 自己查一遍真值
        verified_context = rag.retrieve(original_question)

        # 3. 审计 (Audit)
        audit_result = auditor.evaluate(original_question, agent_response, verified_context)

        # 4. 记录结果
        record = {
            "id": i,
            "question": original_question,
            "agent_response": agent_response,
            "audit_signal": audit_result['signal'],
            "audit_score": audit_result['score'],
            "audit_reason": audit_result['reason']
        }
        results.append(record)
        
        # 实时打印红色警报
        if audit_result['signal'] == 'RED':
            print(f"\n[ALERT] Hallucination detected in Case {i}: {audit_result['reason']}")

    # 5. 保存最终报告
    with open('./output/final_audit_report.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
    print(f"\n审计完成！完整报告已保存至 ./output/final_audit_report.json")

if __name__ == "__main__":
    run_evaluation()