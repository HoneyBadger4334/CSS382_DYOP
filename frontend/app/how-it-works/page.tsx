import SiteNav from "@/components/SiteNav";

const LAYERS = [
  {
    number: "01",
    title: "RSS Ingestion Pipeline",
    color: "#3b82f6",
    details: [
      "Polls the UW Alerts RSS feed every 5 minutes via a FastAPI background task",
      "Caches the last successful fetch with a UTC timestamp",
      'Displays a "Last updated X minutes ago" indicator at all times',
      "If the feed is unreachable, stale cached alerts remain visible with a warning banner",
    ],
    flow: ["UW Alerts RSS Feed", "FastAPI poller (5 min)", "In-memory cache", "Map pins"],
  },
  {
    number: "02",
    title: "NLP Summarizer",
    color: "#10b981",
    details: [
      'Each new RSS item is sent to GPT-4o-mini with a structured prompt requesting JSON: { building_name, incident_type, severity, recommended_action }',
      "The JSON directly drives pin placement — no valid JSON means no structured alert",
      "On API failure or malformed JSON, the raw RSS text is displayed in a fallback pin at campus center",
      '⚠ "Live AI summarization unavailable" banner is shown so users are never silently given stale data',
      "Success threshold: ≥90% valid JSON across a 20-alert test suite",
    ],
    flow: ["Raw RSS text", "GPT-4o-mini prompt", "JSON response", "Building coords lookup", "Colored map pin"],
  },
  {
    number: "03",
    title: "Event Recommender",
    color: "#a855f7",
    details: [
      "Collaborative filtering built with Python's Surprise library (SVD algorithm)",
      "Global threshold: CF activates once the interaction matrix exceeds 50 records",
      "Per-user threshold: users with fewer than 10 interactions receive popularity-ranked content regardless of global matrix size",
      "Cold-start: first-time users are seeded by declared major via a category mapping",
      "Popularity fallback: most-viewed events in the past 7 days, used whenever either threshold is unmet",
    ],
    flow: ["User views/clicks event", "Interaction logged (hashed NetID)", "Threshold check", "SVD model or popularity rank", "For You feed"],
  },
  {
    number: "04",
    title: "Database Layer",
    color: "#f59e0b",
    details: [
      "PostgreSQL hosted on Supabase (cloud, RBAC restricted to project team)",
      "Stores only three fields per row: hashed NetID, event ID, interaction timestamp — no PII",
      "NetID is SHA-256 hashed server-side before storage; raw credentials never touch the database",
      "Row Level Security (RLS) enabled — anon key has no direct table access",
      "Auto-purge via pg_cron: interactions older than 90 days (one quarter) are deleted every Sunday at 3am UTC",
    ],
    flow: ["hashed_netid", "event_id", "timestamp", "Supabase PostgreSQL", "pg_cron purge (weekly)"],
  },
];

export default function HowItWorksPage() {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0f172a" }}>
      <SiteNav />

      <main style={{ flex: 1, overflowY: "auto", padding: "48px" }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: "#f1f5f9", marginBottom: 8 }}>
          How It Works
        </h1>
        <p style={{ fontSize: 14, color: "#64748b", marginBottom: 40, maxWidth: 600 }}>
          Campus Pulse is built in four distinct layers. Each layer has a defined
          fallback so the application remains functional even when individual
          components fail.
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
          {LAYERS.map((layer) => (
            <div
              key={layer.number}
              style={{
                background: "#1e293b",
                border: `1px solid ${layer.color}33`,
                borderLeft: `4px solid ${layer.color}`,
                borderRadius: 10,
                padding: "24px 28px",
              }}
            >
              {/* Layer header */}
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    color: layer.color,
                    background: `${layer.color}22`,
                    borderRadius: 4,
                    padding: "3px 8px",
                  }}
                >
                  Layer {layer.number}
                </span>
                <h2 style={{ fontSize: 16, fontWeight: 700, color: "#f1f5f9" }}>
                  {layer.title}
                </h2>
              </div>

              {/* Data flow swimlane */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0,
                  marginBottom: 20,
                  overflowX: "auto",
                  paddingBottom: 4,
                }}
              >
                {layer.flow.map((step, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", flexShrink: 0 }}>
                    <div
                      style={{
                        background: "#0f172a",
                        border: `1px solid ${layer.color}55`,
                        borderRadius: 6,
                        padding: "6px 12px",
                        fontSize: 11,
                        color: "#cbd5e1",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {step}
                    </div>
                    {i < layer.flow.length - 1 && (
                      <span style={{ color: layer.color, fontSize: 14, margin: "0 6px" }}>→</span>
                    )}
                  </div>
                ))}
              </div>

              {/* Detail bullets */}
              <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
                {layer.details.map((detail, i) => (
                  <li
                    key={i}
                    style={{
                      fontSize: 13,
                      color: "#94a3b8",
                      lineHeight: 1.6,
                      paddingLeft: 16,
                      position: "relative",
                      marginBottom: 6,
                    }}
                  >
                    <span
                      style={{
                        position: "absolute",
                        left: 0,
                        color: layer.color,
                        fontWeight: 700,
                      }}
                    >
                      ·
                    </span>
                    {detail}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
