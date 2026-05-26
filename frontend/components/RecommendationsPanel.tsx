"use client";

import { FormEvent, ReactNode, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DEFAULT_TOKEN = "student-1";

interface RecommendationCard {
  id: string;
  title: string;
  description: string;
  building_name: string;
  coordinates: [number, number];
  category: string;
  tags: string[];
  audience: string[];
  start_time: string;
  end_time: string;
  rank: number;
  score: number;
  why: string;
  ai_score: number;
  matched_keywords: string[];
}

interface RecommendationResponse {
  user_token_hash: string;
  major: string | null;
  major_source: string;
  mode: string;
  model_ready: boolean;
  grace_period_active: boolean;
  global_interaction_count: number;
  user_interaction_count: number;
  ai_available: boolean;
  ai_target_major: string;
  fallback_reason: string | null;
  generated_at: string;
  recommendations: RecommendationCard[];
}

interface InteractionResponse {
  accepted: boolean;
  user_token_hash: string;
  event_id: string;
  interaction_type: "view" | "click" | "save";
  global_interaction_count: number;
  user_interaction_count: number;
  model_ready: boolean;
  mode: string;
  grace_period_active: boolean;
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatMode(mode: string): string {
  if (mode === "ai-match") return "AI matching";
  if (mode === "keyword-fallback") return "Keyword fallback";
  if (mode === "collaborative") return "Collaborative filtering";
  if (mode === "major-seeded") return "Major-seeded cold start";
  return "Live calendar feed";
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function highlightDescription(text: string, keywords: string[]): ReactNode {
  const normalizedKeywords = Array.from(
    new Set(
      keywords
        .map((keyword) => keyword.trim())
        .filter(Boolean)
        .sort((left, right) => right.length - left.length),
    ),
  );

  if (normalizedKeywords.length === 0) {
    return text;
  }

  const pattern = new RegExp(`(${normalizedKeywords.map(escapeRegExp).join("|")})`, "gi");
  const segments = text.split(pattern);

  return segments.map((segment, index) => {
    const match = normalizedKeywords.find((keyword) => keyword.toLowerCase() === segment.toLowerCase());
    if (match) {
      return (
        <mark
          key={`${segment}-${index}`}
          style={{
            background: "rgba(94, 234, 212, 0.22)",
            color: "#ecfeff",
            padding: "0 3px",
            borderRadius: 4,
          }}
        >
          {segment}
        </mark>
      );
    }

    return <span key={`${segment}-${index}`}>{segment}</span>;
  });
}

export default function RecommendationsPanel() {
  const [draftToken, setDraftToken] = useState(DEFAULT_TOKEN);
  const [activeToken, setActiveToken] = useState(DEFAULT_TOKEN);
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [savingEventId, setSavingEventId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadRecommendations(nextToken = activeToken) {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        user_token: nextToken,
        limit: "6",
      });

      const response = await fetch(`${API_URL}/api/recommendations?${params.toString()}`, {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const json: RecommendationResponse = await response.json();
      setData(json);
      setActiveToken(nextToken);
      setDraftToken(nextToken);
    } catch {
      setError("Recommendation feed is temporarily unavailable.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadRecommendations(DEFAULT_TOKEN);
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextToken = draftToken.trim() || DEFAULT_TOKEN;
    await loadRecommendations(nextToken);
  }

  async function handleInteraction(eventId: string, interactionType: InteractionResponse["interaction_type"]) {
    setSavingEventId(eventId);
    try {
      const response = await fetch(`${API_URL}/api/recommendations/interactions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_token: activeToken,
          event_id: eventId,
          interaction_type: interactionType,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const json: InteractionResponse = await response.json();
      if (json.accepted) {
        await loadRecommendations(activeToken);
      }
    } catch {
      setError("Could not save your interaction right now.");
    } finally {
      setSavingEventId(null);
    }
  }

  const modeLabel = data ? formatMode(data.mode) : "Loading recommendations";

  return (
    <>
      <div className="dashboard-panel-header">
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 14 }}>
          <div>
            <p style={{ color: "#5eead4", fontSize: 11, fontWeight: 800, letterSpacing: "0.14em", textTransform: "uppercase" }}>
              AI-ranked events
            </p>
            <h2 style={{ fontSize: 22, marginTop: 6, letterSpacing: "-0.02em" }}>For You</h2>
            <p style={{ color: "#94a3b8", fontSize: 13, lineHeight: 1.5, marginTop: 8 }}>
              AI extracts matching keywords from live UW Bothell event descriptions and ranks them for computer science students.
            </p>
          </div>

          <span className={`status-pill ${data?.mode ?? "loading"}`}>{modeLabel}</span>
        </div>

        {data && (
          <div className="panel-grid">
            <div className="metric-card">
              <div className="metric-label">Global records</div>
              <div className="metric-value">{data.global_interaction_count}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Your records</div>
              <div className="metric-value">{data.user_interaction_count}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">AI target</div>
              <div className="metric-value" style={{ fontSize: 14 }}>
                {data.ai_target_major}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Feed source</div>
              <div className="metric-value" style={{ fontSize: 14 }}>
                UW Bothell calendar
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Model ready</div>
              <div className="metric-value" style={{ fontSize: 14 }}>
                {data.model_ready ? "Yes" : "No"}
              </div>
            </div>
          </div>
        )}

        <form className="reco-form" onSubmit={handleSubmit}>
          <label className="reco-field">
            <span>Student token or hashed NetID</span>
            <input
              value={draftToken}
              onChange={(event) => setDraftToken(event.target.value)}
              placeholder="student-1"
            />
          </label>

          <div className="reco-actions">
            <button className="button-primary" type="submit">
              Refresh feed
            </button>
            <button
              className="button-secondary"
              type="button"
              onClick={() => void loadRecommendations(DEFAULT_TOKEN)}
            >
              Reset token
            </button>
          </div>
        </form>

        {data?.fallback_reason && (
          <p className="reco-note" style={{ marginTop: 12 }}>
            {data.fallback_reason}
          </p>
        )}
        {error && (
          <p className="reco-note" style={{ marginTop: 12, color: "#fca5a5" }}>
            {error}
          </p>
        )}
      </div>

      <div className="dashboard-panel-scroll">
        {!loading && data?.recommendations.length === 0 && (
          <div className="reco-card">
            <p className="reco-why">No recommendations are available yet.</p>
          </div>
        )}

        <div className="reco-list">
          {(data?.recommendations ?? []).map((card) => (
            <article key={card.id} className="reco-card">
              <div className="reco-card-top">
                <div>
                  <div className="reco-title">{card.title}</div>
                  <div className="reco-note" style={{ marginTop: 5 }}>
                    {card.building_name} · {formatTime(card.start_time)}
                  </div>
                </div>
                <span className="reco-score">AI {Math.round(card.ai_score)}%</span>
              </div>

              <p className="reco-why">{card.why}</p>

              <p className="reco-note" style={{ lineHeight: 1.6 }}>
                {highlightDescription(card.description, card.matched_keywords)}
              </p>

              <div className="reco-meta">
                <span className="chip">{card.category}</span>
                {card.tags.slice(0, 3).map((tag) => (
                  <span key={tag} className="chip">
                    {tag}
                  </span>
                ))}
                {card.matched_keywords.slice(0, 3).map((keyword) => (
                  <span key={keyword} className="chip" style={{ borderColor: "rgba(94, 234, 212, 0.32)" }}>
                    {keyword}
                  </span>
                ))}
              </div>

              <div className="reco-footer">
                <div className="reco-note">
                  Rank #{card.rank} · {card.audience.join(" / ")}
                </div>
                <div className="reco-actions">
                  <button
                    className="reco-link"
                    type="button"
                    onClick={() => void handleInteraction(card.id, "view")}
                    disabled={savingEventId === card.id}
                  >
                    Mark viewed
                  </button>
                  <button
                    className="button-secondary"
                    type="button"
                    onClick={() => void handleInteraction(card.id, "save")}
                    disabled={savingEventId === card.id}
                  >
                    {savingEventId === card.id ? "Saving…" : "Save"}
                  </button>
                </div>
              </div>

              <details style={{ color: "#94a3b8", fontSize: 12 }}>
                <summary style={{ cursor: "pointer" }}>More details</summary>
                <p style={{ marginTop: 8, lineHeight: 1.55 }}>{card.description}</p>
                <p style={{ marginTop: 8, lineHeight: 1.55 }}>
                  Runs {formatTime(card.start_time)} to {formatTime(card.end_time)}.
                </p>
              </details>
            </article>
          ))}
        </div>
      </div>
    </>
  );
}