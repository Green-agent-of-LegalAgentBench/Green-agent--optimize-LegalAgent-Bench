# LegalAgentBench-A2A: A Benchmark-Native Green Agent
A standardized, reproducible, and A2A-compatible evaluation system for legal LLM agents.

---

## 1. Project Overview

Our team（Ashley XU， Xirui Zhu， Fanqi lin） create this agent for AgentBeats competition. This repository——The Green Agent (Benchmark Agent) serves as a comprehensive bridge between the LegalAgentBench dataset and the Agent-to-Agent (A2A) protocol.

The primary objective is to establish a standardized evaluation oracle that interacts with Purple Agents (Contestant Agents) strictly through the A2A protocol. By converting legal reasoning tasks into a deterministic execution environment, this project ensures that legal agents are evaluated on:

*Legal Text Comprehension*

*Tool Usage Proficiency*

*Reasoning Rigor*

*Safety & Compliance*

This system is tailored for Chinese Law but architected for extensibility.

---

## 2. Motivation & Problem Statement
Despite the proliferation of legal LLMs, existing benchmarks suffer from critical structural limitations. This project addresses four key pain points:

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
- Manages metadata, ground truth, and allowable toolsets.

### **B. Tool Layer**
- Wraps the original 37 LegalAgentBench tools into A2A tool schemas  
- Supports legal search, case retrieval, law citation lookup, filtering, sorting, etc.  
- Future extension: vector-store RAG tools to improve legal comprehension

### **C. Evaluation Layer**
Produces `results.json` with metrics:

- `success_score`  
- `process_score`  
- `citation_score`  
- `safety_score`  

Also performs:

- hallucination detection  
- reasoning-step alignment  
- legal citation validation  
- sensitive-content safety checks

### **D. Audit & Replay System**
- Logs comprehensive action traces (Thoughts -> Actions -> Observations).
- Enables full deterministic replay for debugging.

### **E. A2A Protocol Engine**
- Handles all communication between Green Agent and Purple Agent  
- Validates A2A message structure  
- Ensures tool calls and final answers comply with A2A specification

---
## 4.2 Advanced Architecture(RAG):
To surpass traditional lexical retrieval, we integrate a Hybrid-RAG Architecture optimized for high-stakes legal reasoning:

Embeddings & Context: Utilizes *Voyage 3 Large Embeddings* with Matryoshka Representation Learning.

Benefit: Supports 32k context windows for analyzing lengthy contracts/statutes while reducing token usage by ~85%.

Query Adaptation: Implements HyDE (Hypothetical Document Embeddings) and Query Expansion to bridge the semantic gap between layperson queries and formal legal terminology.

Self-Reflective Reasoning: Enforces *Chain-of-Thought (CoT)* combined with *Self-RAG mechanisms*, compelling the agent to critique its own citations prior to final output.

HalluGraph Verification: A novel graph-based audit system that maps reasoning steps against a Ground Truth Knowledge Graph to detect subtle semantic hallucinations.

## 5. Upstream Resources

This project is built upon the following open-source frameworks:

### LegalAgentBench (ACL 2025)
- Paper: https://aclanthology.org/2025.acl-long.116/  
- GitHub: https://github.com/CSHaitao/LegalAgentBench  

Key files:
- 37 tools: `src/generated_tools.py`  
- Reasoning agents: `react.py`, `plan_and_solve.py`, `plan_and_execute.py`  
- Tasks: `data/dataset.json`  `data/dataset_test.json`  

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

### reference
HalluGraph：https://arxiv.org/html/2512.01659v1
HyDE (Hypothetical Document Embeddings): Precise Zero-Shot Dense Retrieval without Relevance Labels (https://arxiv.org/abs/2212.10496)
Self-RAG: Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection (https://arxiv.org/abs/2310.11511)
Chain-of-Thought (CoT): Chain-of-Thought Prompting Elicits Reasoning in Large Language Models (https://arxiv.org/abs/2201.11903)

---

## 6. Future Outlook
We aim to evolve this project from a static benchmark into a dynamic legal simulation environment.

Multi-Jurisdiction Support: Expanding the HalluGraph and retrieval corpus to support Common Law jurisdictions (e.g., US, UK) alongside Chinese Civil Law.

Adversarial Evaluation: Introducing "Red Teaming" tasks where the Green Agent actively attempts to mislead the Purple Agent to test robustness against conflicting evidence.

Dynamic Legislation: Integrating real-time API feeds to update the ground truth as laws are amended, ensuring the benchmark never becomes obsolete.

Multi-Agent Simulation: Moving beyond 1-on-1 evaluation to courtroom simulations involving Judge, Prosecutor, and Defense agents.

## 7.How to use
