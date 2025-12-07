import sys
import os
import json
# 添加 src 目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.green_rag_engine import GreenRAGEngine

def ingest():
    # 1. 加载主办方数据集
    data_path = './data/dataset.json'
    if not os.path.exists(data_path):
        print("Error: data/dataset.json 未找到。请先放入数据文件。")
        return

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. 准备数据
    documents = []
    ids = []
    metadatas = []

    print("正在处理数据...")
    for idx, item in enumerate(data):
        # 假设 dataset.json 有 question 和 key (答案) 字段
        # 我们把问题和标准答案作为 Ground Truth 存入
        content = f"Question: {item.get('question', '')}\nAnswer: {item.get('key', '')}"
        documents.append(content)
        ids.append(str(idx))
        metadatas.append({"source": "LegalAgentBench", "id": idx})

    # 3. 存入向量库
    rag = GreenRAGEngine()
    rag.add_documents(documents, metadatas, ids)
    print("数据入库完成！Green Agent 已准备就绪。")

if __name__ == "__main__":
    ingest()