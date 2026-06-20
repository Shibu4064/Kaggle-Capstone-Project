from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from .security import redact_pii, security_audit
except ImportError:
    from security import redact_pii, security_audit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

HAZARD_KEYWORDS = {
    "flood": ["flood", "rain", "river", "water", "submerged", "boat", "low-lying", "inundated"],
    "cyclone": ["cyclone", "storm surge", "landfall", "coastal", "wind", "typhoon", "hurricane"],
    "wildfire": ["wildfire", "fire", "smoke", "ash", "evacuation route", "burn", "forest"],
    "heatwave": ["heatwave", "heat", "hot", "cooling", "hydration", "air conditioning", "outdoor work"],
    "landslide": ["landslide", "slope", "mud", "blocked road", "cracked ground", "hill"],
}

VULNERABILITY_WEIGHTS = {
    "children": 8,
    "older adults": 10,
    "people with limited mobility": 10,
    "people with respiratory risk": 9,
    "outdoor workers": 6,
    "pregnant people": 8,
}

def _load_guidelines() -> pd.DataFrame:
    path = DATA_DIR / "guidelines.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing guidelines file: {path}")
    return pd.read_csv(path)

def detect_hazards(text: str) -> Dict[str, int]:
    """Detect possible hazard types using transparent keyword evidence."""
    text_l = (text or "").lower()
    scores = {}
    for hazard, keywords in HAZARD_KEYWORDS.items():
        scores[hazard] = sum(1 for kw in keywords if kw in text_l)
    return dict(sorted(scores.items(), key=lambda kv: kv[1], reverse=True))

def rank_incidents(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Risk triage tool: returns hazard, severity score, urgency label, and evidence."""
    incident = str(scenario.get("incident_text", ""))
    location = str(scenario.get("location", "Unknown"))
    affected = int(scenario.get("affected_people", 0) or 0)
    vulnerable_groups = scenario.get("vulnerable_groups", []) or []
    resources = scenario.get("available_resources", {}) or {}

    hazard_scores = detect_hazards(f"{location}. {incident}")
    top_hazard, top_score = next(iter(hazard_scores.items()))

    scale_score = min(35, math.log10(max(affected, 1)) * 10)
    vuln_score = min(25, sum(VULNERABILITY_WEIGHTS.get(str(g).lower(), 4) for g in vulnerable_groups))
    keyword_score = min(25, top_score * 6)
    scarcity_score = 0

    if top_hazard in ["flood", "cyclone", "wildfire"] and int(resources.get("shelters", 0) or 0) < 2:
        scarcity_score += 6
    if int(resources.get("volunteers", 0) or 0) < max(5, affected / 100):
        scarcity_score += 5
    if int(resources.get("water_liters", 0) or 0) < affected * 3:
        scarcity_score += 5

    severity_score = min(100, round(scale_score + vuln_score + keyword_score + scarcity_score, 1))
    if severity_score >= 75:
        urgency = "critical"
    elif severity_score >= 55:
        urgency = "high"
    elif severity_score >= 35:
        urgency = "moderate"
    else:
        urgency = "low"

    return {
        "location": location,
        "primary_hazard": top_hazard,
        "hazard_keyword_scores": hazard_scores,
        "affected_people": affected,
        "vulnerable_groups": vulnerable_groups,
        "severity_score": severity_score,
        "urgency": urgency,
        "evidence": [
            f"Top hazard keyword match: {top_hazard}={top_score}",
            f"Affected population considered: {affected}",
            f"Vulnerable groups considered: {', '.join(map(str, vulnerable_groups)) or 'not specified'}",
        ],
    }

def retrieve_guidelines(query: str, top_k: int = 3) -> Dict[str, Any]:
    """Retrieve the most relevant local preparedness guidelines using TF-IDF RAG."""
    df = _load_guidelines()
    corpus = (df["hazard"].fillna("") + " " + df["title"].fillna("") + " " + df["guideline"].fillna("")).tolist()
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(corpus)
    q = vectorizer.transform([query or "general humanitarian communication privacy"])
    sims = cosine_similarity(q, X).ravel()
    ranked = sims.argsort()[::-1][:top_k]
    results = []
    for idx in ranked:
        row = df.iloc[int(idx)]
        results.append({
            "id": row["id"],
            "hazard": row["hazard"],
            "title": row["title"],
            "guideline": row["guideline"],
            "similarity": round(float(sims[idx]), 3)
        })
    return {"query": query, "top_k": top_k, "results": results}

def allocate_resources(scenario: Dict[str, Any], risk_report: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a practical resource-allocation plan from risk and local capacity."""
    affected = int(scenario.get("affected_people", 0) or 0)
    resources = scenario.get("available_resources", {}) or {}
    hazard = risk_report.get("primary_hazard", "general")
    urgency = risk_report.get("urgency", "moderate")
    channels = scenario.get("communication_channels", []) or ["SMS"]

    water_needed_72h = affected * 3 * 3
    available_water = int(resources.get("water_liters", 0) or 0)
    water_gap = max(0, water_needed_72h - available_water)

    actions: List[str] = []
    if hazard in ["flood", "cyclone"]:
        actions += [
            "Open nearest safe shelters and publish route map.",
            "Prioritize evacuation for low-lying households and vulnerable groups.",
            "Assign boats or high-clearance transport only to verified rescue routes."
        ]
    elif hazard == "wildfire":
        actions += [
            "Publish evacuation-route update and blocked-road warning.",
            "Move smoke-sensitive residents toward cleaner-air shelter areas.",
            "Distribute masks where available and reduce outdoor exposure."
        ]
    elif hazard == "heatwave":
        actions += [
            "Open cooling centres and announce opening hours.",
            "Run welfare checks for older adults and isolated residents.",
            "Move outdoor activities away from peak heat hours."
        ]
    elif hazard == "landslide":
        actions += [
            "Close unstable roads and mark alternative routes.",
            "Relocate households near steep slopes until inspected.",
            "Send field teams only after route safety confirmation."
        ]
    else:
        actions += [
            "Confirm incident details with local responders.",
            "Publish one verified public update and refresh regularly."
        ]

    if urgency in ["critical", "high"]:
        actions.insert(0, "Escalate to local emergency coordination immediately.")
    if water_gap > 0:
        actions.append(f"Request additional drinking water: estimated 72-hour gap is {water_gap:,} litres.")

    return {
        "urgency": urgency,
        "primary_hazard": hazard,
        "resource_summary": resources,
        "estimated_72h_water_need_litres": water_needed_72h,
        "estimated_water_gap_litres": water_gap,
        "recommended_actions": actions,
        "communication_channels": channels,
        "human_review_required": urgency in ["critical", "high"],
        "disclaimer": "Decision-support only. Follow official emergency services and local authority instructions."
    }

def generate_public_message(
    scenario: Dict[str, Any],
    risk_report: Dict[str, Any],
    plan: Dict[str, Any],
    language: str = "english",
) -> Dict[str, str]:
    """Create concise public-facing crisis messages in English or Bangla."""
    location = redact_pii(str(scenario.get("location", "your area")))
    hazard = risk_report.get("primary_hazard", "incident")
    urgency = risk_report.get("urgency", "moderate")
    first_actions = plan.get("recommended_actions", [])[:3]

    english = (
        f"Safety update for {location}: {hazard} risk is currently {urgency}. "
        f"Please follow official instructions. Priority actions: "
        + " ".join(f"{i+1}) {a}" for i, a in enumerate(first_actions))
        + " Do not share private phone numbers or exact home addresses in public comments."
    )

    bangla = (
        f"{location} এলাকার জন্য নিরাপত্তা আপডেট: বর্তমানে {hazard} ঝুঁকির মাত্রা {urgency}. "
        "আপনি স্থানীয় কর্তৃপক্ষের নির্দেশনা অনুসরণ করুন। অগ্রাধিকার কাজ: "
        + " ".join(f"{i+1}) {a}" for i, a in enumerate(first_actions))
        + " জনসমক্ষে ব্যক্তিগত ফোন নম্বর বা সুনির্দিষ্ট ঠিকানা শেয়ার করবেন না।"
    )

    return {
        "english": redact_pii(english),
        "bangla": redact_pii(bangla),
        "requested_language": language,
    }

def crisis_pipeline(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """End-to-end deterministic agent workflow used for offline Kaggle reproducibility."""
    audit = security_audit(scenario)
    safe_scenario = dict(scenario)
    safe_scenario["incident_text"] = redact_pii(str(safe_scenario.get("incident_text", "")))
    safe_scenario["location"] = redact_pii(str(safe_scenario.get("location", "")))

    risk = rank_incidents(safe_scenario)
    query = f"{risk['primary_hazard']} {safe_scenario.get('incident_text', '')} vulnerable groups communication privacy"
    evidence = retrieve_guidelines(query, top_k=4)
    plan = allocate_resources(safe_scenario, risk)
    messages = generate_public_message(safe_scenario, risk, plan)

    return {
        "case_id": safe_scenario.get("case_id", "unknown"),
        "security_audit": audit,
        "risk_triage": risk,
        "retrieved_guidelines": evidence,
        "resource_plan": plan,
        "public_messages": messages,
        "agent_technology_demonstrated": [
            "multi-agent workflow design",
            "MCP-compatible tool functions",
            "RAG over local crisis guidelines",
            "privacy/security guardrails",
            "structured JSON output for evaluation"
        ],
    }

def pretty_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)
