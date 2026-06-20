# CrisisWeave ADK — AI Agents for Climate Disaster Response

**Track:** Agents for Good  
**Capstone type:** Multi-agent, MCP-compatible, privacy-preserving crisis decision-support assistant  
**Built for:** Kaggle 5-Day AI Agents: Intensive Vibe Coding Capstone Project with Google

## 1. Problem

Disaster reports often arrive as messy text: community posts, local authority updates, weather notes, and volunteer messages. Small teams must quickly answer:

- What is the main hazard?
- How urgent is it?
- Which vulnerable groups need priority?
- Which resources are missing?
- What public message can be shared without leaking private data?

**CrisisWeave** solves this by orchestrating specialized agents for risk triage, evidence retrieval, resource planning, communication, and safety review.

## 2. Why this can stand out

Most capstone projects will build generic assistants. CrisisWeave is domain-specific, socially useful, and technically demonstrable. It combines deterministic tools with LLM/ADK orchestration so it is both **runnable in Kaggle** and **agentic when a Gemini key is available**.

## 3. Concepts demonstrated

1. **Multi-agent system with Google ADK**
   - Security Auditor Agent
   - Risk Triage Agent
   - Evidence Retrieval Agent
   - Resource Planner Agent
   - Orchestrator Agent

2. **MCP-compatible tool server**
   - `src/mcp_server.py` exposes crisis tools using FastMCP.

3. **Agent skills**
   - Skills are documented in `/skills` as reusable capability cards.

4. **Security features**
   - Prompt-injection detection
   - PII redaction
   - Deny-by-default style security audit
   - Human-review flag for high urgency

5. **RAG and structured outputs**
   - Local TF-IDF retrieval over crisis guidelines
   - JSON outputs for repeatable evaluation

## 4. Kaggle quick start

In a Kaggle notebook:

```python
!pip -q install -r requirements.txt
```

Then run:

```python
!python src/crisisweave_app.py --case-index 0
!python src/evaluation.py
```

Optional Gemini/ADK mode:

1. Add a Kaggle secret named `GOOGLE_API_KEY`.
2. Run the ADK cell in `crisisweave_capstone.ipynb`.

The project still works without the key using deterministic offline mode.

## 5. MCP server

Run locally:

```bash
python src/mcp_server.py
```

MCP clients can connect over stdio using:

```json
{
  "command": "python",
  "args": ["src/mcp_server.py"]
}
```

## 6. Output

The pipeline returns:

- `security_audit`
- `risk_triage`
- `retrieved_guidelines`
- `resource_plan`
- `public_messages`
- `agent_technology_demonstrated`

## 7. Suggested Kaggle submission title

**CrisisWeave ADK: A Multi-Agent Disaster Response Planner with MCP Tools and Privacy Guardrails**

## 8. Ethical note

This is not a replacement for emergency services. It is decision-support for planning, communication, and coordination. Final action should always follow official local authority instructions.
