"""Google ADK agent definitions for CrisisWeave.

This file is intentionally version-tolerant:
- If google-adk is installed and GOOGLE_API_KEY is configured, it builds ADK agents.
- If not, the Kaggle notebook still runs the deterministic offline workflow.

Set Kaggle secret:
    Add GOOGLE_API_KEY in Kaggle -> Add-ons -> Secrets
"""

from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
from typing import Any, Dict
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from tools import crisis_pipeline, rank_incidents, retrieve_guidelines, allocate_resources
from security import redact_pii, security_audit

def run_crisisweave_tool(scenario_json: str) -> str:
    """Run full CrisisWeave workflow. Input must be a JSON scenario string."""
    return json.dumps(crisis_pipeline(json.loads(scenario_json)), indent=2, ensure_ascii=False)

def risk_triage_tool(scenario_json: str) -> str:
    """Risk triage skill. Input must be a JSON scenario string."""
    return json.dumps(rank_incidents(json.loads(scenario_json)), indent=2, ensure_ascii=False)

def rag_guideline_tool(query: str, top_k: int = 3) -> str:
    """Retrieve relevant local crisis-response guidelines."""
    return json.dumps(retrieve_guidelines(query, top_k=top_k), indent=2, ensure_ascii=False)

def resource_plan_tool(scenario_json: str, risk_json: str) -> str:
    """Create a resource plan from scenario JSON and risk JSON."""
    return json.dumps(
        allocate_resources(json.loads(scenario_json), json.loads(risk_json)),
        indent=2,
        ensure_ascii=False,
    )

def privacy_redaction_tool(text: str) -> str:
    """Redact private personal data from text before public output."""
    return redact_pii(text)

def security_audit_tool(scenario_json: str) -> str:
    """Audit the scenario for prompt injection and privacy risk."""
    return json.dumps(security_audit(json.loads(scenario_json)), indent=2, ensure_ascii=False)

def _get_agent_class():
    try:
        from google.adk.agents import Agent
        return Agent
    except Exception:
        try:
            from google.adk import Agent
            return Agent
        except Exception as exc:
            raise ImportError("google-adk is not installed. Run: pip install google-adk") from exc

def _make_agent(Agent, **kwargs):
    """Create an ADK Agent while filtering unsupported kwargs across ADK versions."""
    params = inspect.signature(Agent).parameters
    filtered = {k: v for k, v in kwargs.items() if k in params}
    return Agent(**filtered)

def build_agent_team(model: str = "gemini-2.0-flash"):
    """Build specialised ADK agents plus an orchestrator.

    Demonstrates:
    1. Multi-agent decomposition
    2. Custom function tools
    3. Safety/security tool callbacks at the application layer
    """
    Agent = _get_agent_class()

    security_agent = _make_agent(
        Agent,
        name="security_auditor",
        model=model,
        description="Checks prompt-injection and privacy risk before public outputs.",
        instruction="Audit all inputs and outputs. Never reveal private data. Require human review for high-risk prompts.",
        tools=[security_audit_tool, privacy_redaction_tool],
    )
    risk_agent = _make_agent(
        Agent,
        name="risk_triage_agent",
        model=model,
        description="Classifies hazard type and urgency from crisis reports.",
        instruction="Use transparent evidence. Return JSON with primary_hazard, severity_score, urgency, and evidence.",
        tools=[risk_triage_tool],
    )
    evidence_agent = _make_agent(
        Agent,
        name="evidence_retrieval_agent",
        model=model,
        description="Retrieves local guideline evidence using RAG tools.",
        instruction="Retrieve relevant guidelines and cite guideline IDs in the answer.",
        tools=[rag_guideline_tool],
    )
    planner_agent = _make_agent(
        Agent,
        name="resource_planner_agent",
        model=model,
        description="Creates resource allocation and communication plans.",
        instruction="Create practical, non-medical, decision-support plans. Defer to official emergency services.",
        tools=[resource_plan_tool],
    )

    root_kwargs = dict(
        name="crisisweave_orchestrator",
        model=model,
        description="Multi-agent crisis response assistant for climate and disaster decision support.",
        instruction=(
            "You orchestrate a crisis-response workflow. First audit safety, then triage risk, "
            "retrieve guideline evidence, allocate resources, and produce privacy-preserving public messages. "
            "Always state that outputs are decision-support only."
        ),
        tools=[run_crisisweave_tool],
    )

    # ADK versions with collaborative/multi-agent support may accept sub_agents.
    try:
        params = inspect.signature(Agent).parameters
        if "sub_agents" in params:
            root_kwargs["sub_agents"] = [security_agent, risk_agent, evidence_agent, planner_agent]
    except Exception:
        pass

    root_agent = _make_agent(Agent, **root_kwargs)
    return {
        "root_agent": root_agent,
        "security_agent": security_agent,
        "risk_agent": risk_agent,
        "evidence_agent": evidence_agent,
        "planner_agent": planner_agent,
    }

def run_adk_once(scenario: Dict[str, Any], model: str = "gemini-2.0-flash") -> str:
    """Run ADK once when GOOGLE_API_KEY is available; otherwise use offline fallback."""
    if not os.getenv("GOOGLE_API_KEY"):
        return json.dumps({
            "mode": "offline_fallback_no_google_api_key",
            "result": crisis_pipeline(scenario)
        }, indent=2, ensure_ascii=False)

    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
    except Exception as exc:
        return json.dumps({
            "mode": "offline_fallback_adk_import_failed",
            "error": str(exc),
            "result": crisis_pipeline(scenario)
        }, indent=2, ensure_ascii=False)

    agents = build_agent_team(model=model)
    session_service = InMemorySessionService()
    app_name = "crisisweave_capstone"
    user_id = "kaggle_user"
    session_id = "demo_session"

    try:
        session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
        runner = Runner(agent=agents["root_agent"], app_name=app_name, session_service=session_service)
        prompt = (
            "Run CrisisWeave on this JSON scenario and return a compact JSON answer:\n"
            + json.dumps(scenario, ensure_ascii=False)
        )
        content = types.Content(role="user", parts=[types.Part(text=prompt)])

        final_text = None
        for event in runner.run(user_id=user_id, session_id=session_id, new_message=content):
            if hasattr(event, "is_final_response") and event.is_final_response():
                if event.content and event.content.parts:
                    final_text = event.content.parts[0].text
        return final_text or json.dumps(crisis_pipeline(scenario), indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({
            "mode": "offline_fallback_runtime_issue",
            "error": str(exc),
            "result": crisis_pipeline(scenario)
        }, indent=2, ensure_ascii=False)
