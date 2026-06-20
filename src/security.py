"""Security and privacy utilities for CrisisWeave.

The goal is not to replace emergency services. This module adds deterministic
safety gates so the agent cannot silently leak private data, follow prompt
injection, or generate overconfident emergency instructions.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List, Any

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"forget\s+your\s+system\s+prompt",
    r"reveal\s+(the\s+)?system\s+prompt",
    r"developer\s+message",
    r"bypass\s+(the\s+)?safety",
    r"disable\s+(the\s+)?guardrails",
    r"act\s+as\s+an\s+unrestricted",
]

PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "phone": r"(?:(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4})",
    "precise_address": r"\b\d{1,5}\s+[A-Za-z0-9\s]{3,40}\s+(Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr)\b",
}

def detect_prompt_injection(text: str) -> Dict[str, Any]:
    """Return prompt-injection risk score and matched patterns."""
    text = text or ""
    matches: List[str] = []
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            matches.append(pattern)
    score = min(1.0, len(matches) / 2)
    return {
        "score": round(score, 2),
        "risk": "high" if score >= 0.5 else ("medium" if score > 0 else "low"),
        "matches": matches,
    }

def redact_pii(text: str) -> str:
    """Redact common PII in public-facing text."""
    text = text or ""
    redacted = text
    for label, pattern in PII_PATTERNS.items():
        redacted = re.sub(pattern, f"[REDACTED_{label.upper()}]", redacted, flags=re.IGNORECASE)
    return redacted

def security_audit(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Deny-by-default style audit for crisis-agent input."""
    incident_text = str(scenario.get("incident_text", ""))
    location = str(scenario.get("location", ""))
    combined = f"{location}\n{incident_text}"
    injection = detect_prompt_injection(combined)
    pii_text = redact_pii(combined)
    pii_found = pii_text != combined

    status = "pass"
    reasons: List[str] = []
    if injection["risk"] == "high":
        status = "needs_human_review"
        reasons.append("High prompt-injection risk detected.")
    if len(combined) > 5000:
        status = "needs_human_review"
        reasons.append("Scenario text is unusually long for an emergency triage request.")
    if pii_found:
        reasons.append("PII was detected and will be redacted from public outputs.")

    return {
        "status": status,
        "timestamp_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "prompt_injection": injection,
        "pii_found": pii_found,
        "reasons": reasons or ["No blocking security issue detected."],
    }
