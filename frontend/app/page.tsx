"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import AlertBanner from "@/components/AlertBanner";
import RecommendationsPanel from "@/components/RecommendationsPanel";
import type { AlertPin } from "@/components/CampusMap";

// Leaflet uses browser APIs — must be loaded client-side only.
const CampusMap = dynamic(() => import("@/components/CampusMap"), { ssr: false });

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const POLL_MS = 30_000;

interface AlertsResponse {
  alerts: AlertPin[];
  last_updated: string;
  ai_available: boolean;
  feed_available: boolean;
}

export default function HomePage() {
  const [data, setData] = useState<AlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  async function fetchAlerts() {
    try {
      const res = await fetch(`${API_URL}/api/alerts`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: AlertsResponse = await res.json();
      setData(json);
    } catch {
      // Keep stale data if available; just stop showing loading spinner.
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, POLL_MS);
    return () => clearInterval(interval);
  }, []);

  const alerts = data?.alerts ?? [];

  return (
    <div className="dashboard-shell">
      <header className="dashboard-header">
        <div className="dashboard-brand">
          <div className="brand-mark" aria-hidden="true">
            <span>📍</span>
          </div>
          <div>
            <h1 className="brand-title">UW Bothell Campus Pulse</h1>
            <p className="brand-subtitle">
              Live alerts on the map, personalized events in the feed.
            </p>
          </div>
        </div>

        <div
          className="status-pill"
          style={{
            background: alerts.length > 0 ? "rgba(239,68,68,0.12)" : "rgba(96,165,250,0.12)",
            color: alerts.length > 0 ? "#fecaca" : "#bfdbfe",
            borderColor: alerts.length > 0 ? "rgba(239,68,68,0.25)" : "rgba(96,165,250,0.22)",
          }}
        >
          {loading
            ? "Loading alerts"
            : `${alerts.length} alert${alerts.length !== 1 ? "s" : ""}`}
        </div>
      </header>

      {data && (
        <div className="dashboard-alerts">
          <AlertBanner
            aiAvailable={data.ai_available}
            feedAvailable={data.feed_available}
            lastUpdated={data.last_updated}
          />
        </div>
      )}

      <main className="dashboard-main">
        <section className="dashboard-map">
          {loading && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: "rgba(3, 7, 18, 0.72)",
                zIndex: 1000,
                fontSize: 14,
                color: "#cbd5e1",
              }}
            >
              Loading campus map…
            </div>
          )}
          <CampusMap alerts={alerts} />
        </section>

        <section className="dashboard-panel">
          <RecommendationsPanel />
        </section>
      </main>

      <footer className="dashboard-footer">
        {[
          { color: "#ef4444", label: "High" },
          { color: "#f59e0b", label: "Medium" },
          { color: "#22c55e", label: "Low" },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span className="legend-dot" style={{ background: color }} />
            <span>{label} severity</span>
          </div>
        ))}
        <span style={{ marginLeft: "auto" }}>Click a pin for alert details</span>
      </footer>
    </div>
  );
}
