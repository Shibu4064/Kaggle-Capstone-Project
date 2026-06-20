# 2-Minute Demo Script

Hello, I’m presenting **CrisisWeave ADK**, an Agents for Good project for climate and disaster response.

The problem is simple but serious: during floods, heatwaves, wildfires, and cyclones, responders receive messy information from many channels. They need to quickly understand the risk, protect private information, allocate resources, and communicate clearly.

Here is the demo scenario: heavy rainfall is entering homes in low-lying areas, older adults are stranded, roads are blocked, and a school can be used as a shelter.

I run the CrisisWeave workflow. The first agent is the Security Auditor. It checks prompt injection and redacts private information. The second is the Risk Triage Agent. It identifies the primary hazard and urgency using transparent evidence. The third is the Evidence Retrieval Agent, which retrieves relevant local guidelines using RAG. The fourth is the Resource Planner Agent, which estimates resource gaps and recommends actions. Finally, the Communication Agent produces public messages in English and Bangla.

The output is structured JSON, so it is easy to inspect and evaluate. Here we can see the primary hazard, severity score, affected population, vulnerable groups, recommended actions, water gap, and public alerts.

Technically, this project demonstrates Google ADK multi-agent design, MCP-compatible tools through FastMCP, reusable agent skills, RAG, and security guardrails. It also includes an offline deterministic mode so judges can run it on Kaggle without an API key, and an optional Gemini/ADK mode when `GOOGLE_API_KEY` is available.

The key point is that CrisisWeave does not replace emergency services. It is a decision-support layer that helps teams turn fragmented reports into safer, clearer, and faster action plans.
