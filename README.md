# LegalAgentBench-A2A Green Agent  
A benchmark-native legal agent for the AgentBeats competition

---

## 1. Project Overview

This repository implements the **Green Agent (benchmark agent)** for the AgentBeats competition.  
The goal of this project is to wrap **LegalAgentBench** into an **A2A-compatible benchmark agent** that can be directly used by any Purple Agent through the official **Agent-to-Agent (A2A) protocol**.

More specifically, this project converts LegalAgentBench’s tasks, tools, and evaluation logic into a fully standardized benchmark that is:

- **A2A-native**
- **Deterministic & reproducible**
- **Structured & extensible**
- **Designed for Chinese-law legal reasoning**

### Key Features of the Green Agent
- Provides **tasks** in A2A JSON format  
- Provides **tools** (legal search, case retrieval, filtering, etc.)  
- Provides **evaluation metrics** (success, process, citation, safety)  
- Records **action logs** for reproducibility  
- Communicates with Purple Agents strictly through the **A2A protocol**

---

## 2. Motivation & Goals

This project responds to limitations identified in **LegalAgentBench** and aligns with the AgentBeats competition goals for creating stronger, more usable benchmarks.

### Problems with existing legal benchmarks
1. **Interoperability**  
   - Current benchmarks cannot be directly used by real LLM agents.

2. **Reproducibility**  
   - Evaluation pipelines are not deterministic; scores vary across runs.

3. **Fragmentation**  
   - Evaluation criteria are inconsistent and scattered.

4. **Discovery**  
   - Benchmarks are difficult to understand, extend, and reuse.

---

## 3. Our Goals

### **1. Build an A2A-Compatible Legal Benchmark (Interoperability)**  
- Convert all **300 LegalAgentBench tasks** into standardized A2A task JSON  
- Ensure retrieval, analysis, reasoning, and tool-use tasks can be executed by any LLM agent using the A2A interface

### **2. Enable Highly Reproducible Evaluation (Reproducibility)**  
- Implement **deterministic** task generation & scoring logic  
- Fix tool behavior, corpus usage, retrieval logic, and evaluation rules  
- Provide benchmark-side logging & action replay  
- Ensure identical inputs → consistent outputs (or explainable differences)

### **3. Build a Structured Capability Evaluation System (Fragmentation)**  
Unify evaluation across tasks with dimensions such as:

- Legal text comprehension  
- Legal tool-use ability  
- Legal argumentation & writing quality  
- Reasoning explainability (full reasoning trace)  
- Compliance & safety (no hallucinated laws, no illegal advice)

### **4. Improve Discoverability & Extensibility (Discovery)**  
- Create a benchmark that is **easy to use, easy to extend, and easy to integrate**  
- Standardize:
  - Task schema  
  - Tool schema  
  - Evaluation outputs  
- Provide clear documentation and example workflows

---

## 4. System Components

### **A. Task Provider**
- Converts LegalAgentBench dataset into A2A task definitions  
- Enforces the unified task schema  
- Includes allowed tools, evaluation references, and metadata

### **B. Tool Layer**
- Wraps the original 37 LegalAgentBench tools into A2A tool schemas  
- Supports legal search, case retrieval, law citation lookup, filtering, sorting, etc.  
- Future extension: vector-store RAG tools to improve legal comprehension

### **C. Evaluation Layer**
Produces `result.json` with metrics:

- `success_score`  
- `process_score`  
- `citation_score`  
- `safety_score`  

Also performs:

- hallucination detection  
- reasoning-step alignment  
- legal citation validation  
- sensitive-content safety checks

### **D. Logging & Reproducibility**
- Logs every A2A message  
- Logs every tool call & observation  
- Supports full **action replay** for debugging / reproducibility

### **E. A2A Protocol Engine**
- Handles all communication between Green Agent and Purple Agent  
- Validates A2A message structure  
- Ensures tool calls and final answers comply with A2A specification

---

## 5. Upstream Resources

This project is built upon the following open-source frameworks:

### LegalAgentBench (ACL 2025)
- Paper: https://aclanthology.org/2025.acl-long.116/  
- GitHub: https://github.com/CSHaitao/LegalAgentBench  

Key files:
- 37 tools: `src/generated_tools.py`  
- Reasoning agents: `react.py`, `plan_and_solve.py`, `plan_and_execute.py`  
- Tasks: `data/dataset.json`  

### Related Legal Benchmarks
- LawBench — https://arxiv.org/abs/2309.16289  
- CitaLaw — https://arxiv.org/abs/2412.14556  
- DISC-LawLLM — https://github.com/FudanDISC/DISC-LawLLM  
- Chinese-LawBench — https://arxiv.org/abs/2406.04500  

### AgentBeats & A2A Resources
- A2A Protocol Spec — https://github.com/a2aproject/A2A  
- AgentBeats SDK — https://github.com/agentbeats/agentbeats  
- A2A Tutorial — https://github.com/agentbeats/tutorial  
- A2A Example Implementation — https://github.com/sap156/Agent-to-Agent-A2A-Protocol-Implementation  

---

## 6. Repository Structure (Planned)

