"""
Week 8 acceptance criterion: NLP summarizer returns valid, parseable JSON
for ≥90% of inputs across a 20-alert test suite.

Run: python test_nlp_summarizer.py
Requires OPENAI_API_KEY in environment or .env file.
"""

import json
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from nlp_summarizer import summarize, AlertSummary

TWENTY_ALERTS = [
    "Police activity near UW1, avoid the area.",
    "Fire alarm activated in Discovery Hall. Evacuate immediately.",
    "Medical emergency in the Library. Avoid 2nd floor.",
    "Suspicious person reported near CAB. Exercise caution.",
    "Utility outage affecting UW2 — no power expected for 2 hours.",
    "All-clear: Police activity near UW1 has been resolved.",
    "Weather advisory: High winds expected. Secure outdoor belongings.",
    "Road closure on Campus Way NE due to water main break.",
    "Emergency maintenance in STEM building — labs closed until further notice.",
    "Active fire in Husky Hall. Evacuate building immediately. Do not use elevators.",
    "Gas leak detected near North Creek Hall. Clear the area.",
    "Flooding in CAB lower level. Avoid basement areas.",
    "Power restored to UW2. Normal operations may resume.",
    "Elevator out of service in UW1. Use stairs.",
    "Bomb threat received for DISC building. Evacuate now.",
    "Construction noise near Library through 5 PM.",
    "Parking lot closure near STEM through end of week.",
    "Mental health crisis near campus center — please give space and call 911.",
    "Network outage affecting all campus buildings. IT working on resolution.",
    "All-clear: Gas leak near North Creek Hall resolved. Buildings accessible.",
]

VALID_SEVERITIES = {"low", "medium", "high"}
VALID_BUILDINGS = {"UW1", "UW2", "DISC", "STEM", "LIB", "CAB", "HH", "NCH", "CAMPUS"}


def validate(summary: Optional[AlertSummary]) -> bool:
    if summary is None:
        return False
    if not summary.building_name or not summary.incident_type:
        return False
    if summary.severity not in VALID_SEVERITIES:
        return False
    if not summary.recommended_action:
        return False
    return True


def run():
    passed = 0
    total = len(TWENTY_ALERTS)

    for i, alert_text in enumerate(TWENTY_ALERTS, 1):
        summary, ai_ok = summarize(alert_text)
        ok = ai_ok and validate(summary)
        status = "PASS" if ok else "FAIL"
        print(f"[{i:02d}] {status} — {alert_text[:60]}")
        if ok:
            print(f"       → {summary.building_name} | {summary.incident_type} | {summary.severity}")
            passed += 1
        else:
            print(f"       → ai_ok={ai_ok}, summary={summary}")

    rate = passed / total
    print(f"\nResult: {passed}/{total} ({rate:.0%}) valid JSON responses")
    if rate >= 0.90:
        print("✓ PASS — meets Week 8 MVP criterion (≥90%)")
    else:
        print("✗ FAIL — below 90% threshold")


if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set. Add it to backend/.env and retry.")
    else:
        run()
