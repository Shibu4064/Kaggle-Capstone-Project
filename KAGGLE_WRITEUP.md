# CrisisWeave ADK: Multi-Agent Disaster Response Planner

## Track
**Agents for Good**

## One-line summary
CrisisWeave is a privacy-preserving multi-agent assistant that turns messy climate/disaster reports into a structured risk triage, evidence-backed resource plan, and safe public messages.

## Problem definition
During floods, heatwaves, wildfires, cyclones, and landslides, response teams often receive fragmented updates from residents, volunteers, social media, and local offices. The challenge is not only generating text; the system must decide what matters, retrieve relevant guidance, protect private data, and produce a plan that humans can review.

CrisisWeave focuses on four high-impact questions:

1. What is the likely primary hazard?
2. How urgent is the situation?
3. Which resource gaps should be addressed first?
4. What safe public message can be shared immediately?

## Solution design
The system uses a multi-agent design:

- **Security Auditor Agent** checks prompt-injection patterns and redacts private information.
- **Risk Triage Agent** classifies hazard type and urgency using transparent evidence.
- **Evidence Retrieval Agent** performs RAG over local crisis-response guidelines.
- **Resource Planner Agent** estimates gaps and recommends operational actions.
- **Communication Agent** creates public messages in English and Bangla.
- **Orchestrator Agent** coordinates the workflow through ADK-compatible tools.

The deterministic offline workflow makes the notebook reproducible on Kaggle even without an API key. When `GOOGLE_API_KEY` is available, `src/adk_agents.py` builds a Google ADK agent team around the same tools.

## Agent technologies used

### 1. Google ADK multi-agent architecture
The project defines specialized ADK agents in `src/adk_agents.py`. Each agent has a narrow role, instructions, and tools. This makes the system easier to evaluate than a single generic chatbot.

### 2. MCP-compatible tools
`src/mcp_server.py` exposes the core functions through FastMCP:

- `run_crisis_pipeline`
- `risk_triage`
- `guideline_search`
- `privacy_redact`
- `input_security_audit`

This demonstrates interoperability: the same crisis tools can be used by ADK, a local notebook, or any MCP-capable client.

### 3. Agent skills
The `/skills` folder documents reusable skills: crisis triage, humanitarian communication, privacy guardrails, and resource planning. This makes the project modular and easier to extend.

### 4. Security and privacy
The project adds deterministic safety gates:

- Prompt-injection detection
- PII redaction for emails, phone numbers, and precise addresses
- Human-review flags for high-risk situations
- Public-output privacy rule

This is important because disaster-response agents may handle sensitive community information.

### 5. RAG over local guidance
The evidence agent uses TF-IDF retrieval over a local guideline store. This avoids hallucinated emergency advice and keeps outputs tied to visible evidence.

## Example scenario
Input:

> Heavy rainfall for 36 hours. River water is entering homes in low-lying areas. Older adults are stranded. Roads are blocked. A school building is available as shelter.

Output includes:

- Primary hazard: flood
- Urgency: high or critical, depending on resources
- Evidence: affected population, vulnerable groups, flood keyword matches
- Plan: open shelters, prioritize low-lying households, request water gap, use SMS/radio updates
- Public message: privacy-preserving English and Bangla alert

## Evaluation
The notebook evaluates:

- JSON schema completeness
- Safety gate pass rate
- Guideline retrieval pass rate
- Action plan pass rate
- Latency per case

This makes the capstone measurable rather than only a demo.

## Innovation
The innovation is not just “an agent writes a plan.” CrisisWeave combines:

- disaster-domain reasoning,
- multi-agent decomposition,
- MCP interoperability,
- deterministic security gates,
- bilingual public communication,
- and reproducible evaluation.

That combination makes it suitable for real-world humanitarian AI prototyping.

## Limitations
CrisisWeave uses a small local guideline base for demo purposes. It does not replace official emergency services, verified GIS systems, weather agencies, or trained responders. Future versions should connect to verified weather APIs, maps, shelter databases, and authority-approved guidance.

## How to run
```bash
pip install -r requirements.txt
python src/crisisweave_app.py --case-index 0
python src/evaluation.py
```
