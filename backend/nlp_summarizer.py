import json
import os
from openai import OpenAI
from pydantic import BaseModel

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


class AlertSummary(BaseModel):
    building_name: str
    incident_type: str
    severity: str
    recommended_action: str


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
            temperature=0,
            max_tokens=200,
        )
        content = response.choices[0].message.content.strip()
        # Strip markdown fences if the model wraps with them
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)
        summary = AlertSummary(**data)
        # Normalize severity
        summary.severity = summary.severity.lower()
        if summary.severity not in ("low", "medium", "high"):
            summary.severity = "medium"
        return summary, True
    except Exception:
        return None, False
