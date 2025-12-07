# Green Agent v2.0: An Auditable, RAG-Native Legal Evaluation Framework

## 1. Executive Summary (项目摘要)

In the AgentBeats competition, we identified a critical flaw in traditional legal benchmarks: **static QA pairs cannot evaluate the "Reasoning Process" or "Hallucination Risks" of Large Language Models (LLMs).**

To address this, we developed **Green Agent v2.0**, a dynamic evaluation system powered by **Domain-Specific RAG (Retrieval-Augmented Generation)**. Unlike standard evaluators that only check final answers, our system acts as an **Omniscient Legal Auditor**. It utilizes **Voyage AI's SOTA legal embeddings** to retrieve ground truth context and employs a **"Traffic Light" protocol** (inspired by HalluGraph) to verify the factual integrity of the participating agent's outputs.

---

## 2. Core Methodology (核心方法论)

Our approach transforms the evaluation from simple string matching to a **Dual-View Consistency Check**:

1.  **The Agent View:** What the Purple Agent (competitor) claims and cites.
2.  **The Auditor View (Ground Truth):** What the Green Agent retrieves from the verified legal corpus using a superior RAG pipeline.

### 2.1 Theoretical Basis
* **Legal RAG Architecture:** Leveraging research from *Thomson Reuters* and *Harvard JOLT*, we prioritize context retrieval over model parameter knowledge to reduce hallucinations.
* **Safety-First Metrics:** Adopting the **Traffic Light System**, we classify model outputs not just as "Right/Wrong," but as "Safe/Risky/Dangerous."

---

## 3. Technical Architecture (技术架构)



[Image of retrieval augmented generation architecture]


### 3.1 Layer 1: The "Deep" Retrieval Engine
We replaced standard keyword search with a semantic retrieval engine to handle complex legal terminology.

* **Embedding Model:** **Voyage-3-Large**
    * *Why:* Specific fine-tuning on legal texts; supports **32k context window** (crucial for analyzing long contracts without truncation).
    * *Efficiency:* Utilizes **Matryoshka Representation Learning** to perform fast retrieval at lower dimensions (256d) and precise reranking at higher dimensions (1024d).
* **Query Strategy:** **HyDE (Hypothetical Document Embeddings)**
    * *Logic:* User queries are often short and vague. We generate a "Hypothetical Legal Clause" to bridge the semantic gap between the query and the actual statute in the vector database.

### 3.2 Layer 2: The Audit Logic (HalluGraph Lite)
Instead of relying on `BERTScore` or `Rouge-L`, we implemented a logic-based auditor.

* **Fact Triple Extraction:** The system extracts `(Claim, Source, Condition)` triples from the Agent's response.
* **Consistency Verification:**
    * *Step 1:* Green Agent retrieves the actual text of the cited `Source`.
    * *Step 2:* An LLM-Judge compares the Agent's `Claim` against the retrieved text.
    * *Step 3:* If the claim contradicts the text, it is flagged as a **Hallucination**.

---

## 4. The "Traffic Light" Evaluation Metric (红绿灯评估体系)

We introduce a novel metric, `safety_signal`, to quantify reliability:

| Signal | Color | Definition | Action |
| :--- | :--- | :--- | :--- |
| **Verified Success** | 🟢 **GREEN** | Answer is correct AND citations are fully supported by Ground Truth. | **Pass** (+1.0) |
| **Unsubstantiated** | 🟡 **YELLOW** | Answer is factually correct but lacks citations or reasoning (Lucky Guess). | **Warning** (+0.5) |
| **Hallucination** | 🔴 **RED** | Answer cites non-existent laws, misinterprets statutes, or gives illegal advice. | **Fail** (-1.0) |

---

## 5. Implementation Details (实现细节)

### 5.1 Repository Structure
* `src/green_rag_engine.py`: Manages the **Voyage AI** embedding lifecycle and **ChromaDB** vector storage.
* `src/traffic_light_eval.py`: Contains the **LLM-as-a-Judge** prompt logic for audit and safety signaling.
* `scripts/ingest_data.py`: Pre-processes the `LegalAgentBench` dataset into a deterministic vector index.

### 5.2 Key Technology Stack
* **Orchestration:** LangChain
* **Vector Database:** ChromaDB (Local & Deterministic)
* **Embedding:** Voyage AI (`voyage-3-large`)
* **Audit Model:** GPT-4o / GLM-4 (via API)

---

## 6. How to Run (运行指南)

### Step 1: Environment Setup
Install dependencies and configure API keys (Voyage AI & OpenAI/GLM).
```bash
pip install -r requirements.txt
cp .env.example .env