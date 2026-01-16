# LegalAgentBench-A2A Green Agent

A reproducible and auditable **Green Agent** for legal evaluation on AgentBeats.

This Green Agent wraps **LegalAgentBench** into an **Agent-to-Agent (A2A)** compatible
benchmark host and evaluates Purple Agents with RAG-grounded, auditable scoring.


## What is this repository?

This repository implements a **Green Agent** for the AgentBeats competition.

The Green Agent is **not a contestant agent**.
Instead, it acts as a **benchmark host and legal auditor** that evaluates
Purple Agents on legal reasoning tasks.

Specifically, this Green Agent:

- Wraps **LegalAgentBench** into an **A2A-compatible evaluation agent**
- Communicates with Purple Agents via the official **Agent-to-Agent (A2A) protocol**
- Uses **retrieval-augmented generation (RAG)** to access authoritative legal texts
- Produces **structured, auditable, and reproducible evaluation results**

In short:

> Green Agent = LegalAgentBench + RAG + A2A

Any Purple Agent that speaks the A2A protocol can be evaluated
without modifying benchmark scripts or evaluation code.

## Quickstart (Docker, one-command run)

Run the following commands to execute the Green Agent end-to-end:

```bash
cp .env.example .env
# Edit .env and set ZHIPUAI_API_KEY
# Do NOT commit .env

./scripts/docker_run_once.sh

# Results will be written to:
# output/audit_results.jsonl


## Reproducibility (Run the same configuration twice)

This Green Agent supports reproducible evaluation.  
To demonstrate reproducibility, run the following command:

```bash
./scripts/docker_run_twice_same_config.sh

####This command runs the same evaluation configuration twice using the same Docker image,the same environment variables, and the same evaluation logic. All results are written to structured JSONL logs, enabling auditability, comparison across runs, andleaderboard-level reproducibility.

## Evaluation Outputs

Each evaluation produces structured audit outputs that capture task correctness,reasoning quality, citation grounding, and safety signals. Results are written records for easy inspection, replay, and comparison across runs.

```text
output/audit_results.jsonl

Each record contains normalized scores and a Traffic-Light safety signal that summarize whether the evaluated reasoning is verified, insufficiently grounded, or risky.

## High-level Method

Green Agent evaluates legal agents using a dual-view consistency check between what a Purple Agent claims and what authoritative legal texts support. The Purple Agent’s reasoning steps, tool calls, and citations are compared against ground truth retrieved via a deterministic RAG pipeline over verified legal corpora. For each step, the Green Agent determines whether claims are supported,under-specified, or hallucinated, enabling process-aware and safety-first legal evaluation beyond final-answer matching.

## Traffic Light Safety Signal

Green Agent introduces a Traffic Light safety signal to explicitly capture the reliability and safety of legal reasoning. Each evaluated response is classified as GREEN, YELLOW, or RED based on consistency with authoritative legal texts.
GREEN indicates that claims and citations are fully supported, YELLOW indicatesplausible but insufficiently grounded reasoning, and RED indicates hallucinated,incorrect, or legally unsafe claims. This safety signal directly influences theoverall evaluation scores, ensuring that unsafe reasoning can never receive ahigh evaluation result.

## Notes, Secrets, and License

This repository is designed for reproducible evaluation and submission on AgentBeats. Runtime secrets such as API keys must never be committed to version control. Only `.env.example` should be tracked, while `.env` remains local.

Evaluation outputs and local databases (e.g., JSONL audit logs and vector stores)
are generated at runtime and are not intended to be committed.

License: MIT
<!-- webhook test -->
##

