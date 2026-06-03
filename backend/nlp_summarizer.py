import json
import logging
import os
from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a campus safety alert parser for UW Bothell.
Given raw alert text, return ONLY a valid JSON object — no markdown, no extra text.

JSON schema:
{
  "building_name": "<abbreviation: UW1|UW2|DISC|STEM|LIB|CAB|HH|NCH|CAMPUS>",
  "incident_type": "<e.g. Police Activity|Medical Emergency|Fire|Suspicious Person|Weather|Utility Outage|All-Clear>",
  "severity": "<low|medium|high>",
  "recommended_action": "<concise student instruction, max 20 words>"
}

Rules:
- severity=high: active threat, police, fire, evacuation
- severity=medium: medical, suspicious activity, utility outage
- severity=low: all-clear, informational, minor disruption
- If no specific building is mentioned, use CAMPUS."""

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


TRIAGE_PROMPT = """You are a campus safety communications officer for UW Bothell.
A high-severity emergency alert has just been issued. Write two things:

1. "headline": A single urgent sentence (max 12 words) for a push notification.
2. "safety_brief": Exactly 3 sentences of calm, actionable safety guidance for students.

Return ONLY valid JSON with keys "headline" and "safety_brief"."""


class AlertSummary(BaseModel):
    building_name: str
    incident_type: str
    severity: str
    recommended_action: str


class AlertTriage(BaseModel):
    headline: str
    safety_brief: str


def triage(raw_text: str, summary: AlertSummary) -> AlertTriage | None:
    """
    Second GPT call — only fires for severity=high.
    Generates a push-notification headline and 3-sentence safety brief.
    """
    try:
        context = (
            f"Incident: {summary.incident_type} at {summary.building_name}.\n"
            f"Raw alert: {raw_text}"
        )
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": TRIAGE_PROMPT},
                {"role": "user", "content": context},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=200,
        )
        data = json.loads(response.choices[0].message.content.strip())
        return AlertTriage(**data)
    except Exception as e:
        logger.error("Triage failed: %s", e)
        return None


def summarize(raw_text: str) -> tuple[AlertSummary | None, bool]:
    """
    Returns (summary, ai_available).
    summary is None only on hard parse failure; ai_available=False on API error.
    """
    try:
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Alert text: {raw_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=200,
        )
        content = response.choices[0].message.content.strip()
        data = json.loads(content)
        summary = AlertSummary(**data)
        # Normalize severity
        summary.severity = summary.severity.lower()
        if summary.severity not in ("low", "medium", "high"):
            summary.severity = "medium"
        return summary, True
    except Exception:
        return None, False
