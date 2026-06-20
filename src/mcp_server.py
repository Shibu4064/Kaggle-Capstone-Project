"""MCP server for CrisisWeave.

Run locally:
    python src/mcp_server.py

In a client that supports MCP stdio, expose this server as:
    command: python
    args: ["src/mcp_server.py"]

The tools mirror the deterministic functions used by the Kaggle notebook.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

# Allow running as `python src/mcp_server.py`
sys.path.append(str(Path(__file__).resolve().parent))

from tools import crisis_pipeline, rank_incidents, retrieve_guidelines, allocate_resources
from security import redact_pii, security_audit

try:
    from fastmcp import FastMCP
except Exception:
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:
        raise ImportError("Install FastMCP or MCP Python SDK: pip install fastmcp mcp") from exc

mcp = FastMCP("CrisisWeave-Crisis-Response-MCP")

@mcp.tool
def run_crisis_pipeline(scenario_json: str) -> str:
    """Run the full crisis response workflow from a JSON scenario string."""
    scenario = json.loads(scenario_json)
    return json.dumps(crisis_pipeline(scenario), indent=2, ensure_ascii=False)

@mcp.tool
def risk_triage(scenario_json: str) -> str:
    """Return hazard type, severity score, urgency label, and evidence."""
    scenario = json.loads(scenario_json)
    return json.dumps(rank_incidents(scenario), indent=2, ensure_ascii=False)

@mcp.tool
def guideline_search(query: str, top_k: int = 3) -> str:
    """Retrieve local disaster-response guidelines relevant to the query."""
    return json.dumps(retrieve_guidelines(query, top_k=top_k), indent=2, ensure_ascii=False)

@mcp.tool
def privacy_redact(text: str) -> str:
    """Redact emails, phone numbers, and precise street addresses from text."""
    return redact_pii(text)

@mcp.tool
def input_security_audit(scenario_json: str) -> str:
    """Audit a scenario for prompt-injection and privacy risk."""
    scenario = json.loads(scenario_json)
    return json.dumps(security_audit(scenario), indent=2, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run()
