from __future__ import annotations

import json
import time
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from tools import crisis_pipeline

REQUIRED_TOP_LEVEL = [
    "case_id",
    "security_audit",
    "risk_triage",
    "retrieved_guidelines",
    "resource_plan",
    "public_messages",
]

def evaluate_case(scenario):
    started = time.time()
    result = crisis_pipeline(scenario)
    latency = time.time() - started
    completeness = sum(1 for k in REQUIRED_TOP_LEVEL if k in result) / len(REQUIRED_TOP_LEVEL)
    safety_pass = result["security_audit"]["status"] in ["pass", "needs_human_review"]
    has_guidelines = len(result["retrieved_guidelines"]["results"]) >= 2
    has_actions = len(result["resource_plan"]["recommended_actions"]) >= 3
    return {
        "case_id": scenario.get("case_id"),
        "latency_seconds": round(latency, 4),
        "schema_completeness": round(completeness, 3),
        "safety_gate_passed": safety_pass,
        "guideline_retrieval_passed": has_guidelines,
        "action_plan_passed": has_actions,
        "urgency": result["risk_triage"]["urgency"],
        "primary_hazard": result["risk_triage"]["primary_hazard"],
    }

def main():
    root = Path(__file__).resolve().parents[1]
    scenarios = json.loads((root / "data/sample_scenarios.json").read_text(encoding="utf-8"))
    rows = [evaluate_case(s) for s in scenarios]
    summary = {
        "n_cases": len(rows),
        "avg_schema_completeness": round(sum(r["schema_completeness"] for r in rows) / len(rows), 3),
        "safety_pass_rate": round(sum(r["safety_gate_passed"] for r in rows) / len(rows), 3),
        "guideline_pass_rate": round(sum(r["guideline_retrieval_passed"] for r in rows) / len(rows), 3),
        "action_plan_pass_rate": round(sum(r["action_plan_passed"] for r in rows) / len(rows), 3),
        "rows": rows,
    }
    out = root / "outputs/evaluation_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
