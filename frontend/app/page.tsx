"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import AlertBanner from "@/components/AlertBanner";
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
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      {/* Header */}
      <header
        style={{
          background: "#1e293b",
          borderBottom: "1px solid #334155",
          padding: "12px 20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 20 }}>📍</span>
          <div>
            <h1 style={{ fontSize: 16, fontWeight: 700, color: "#f1f5f9" }}>
              UW Bothell Campus Pulse
            </h1>
            <p style={{ fontSize: 11, color: "#94a3b8" }}>
              Real-time alerts & campus activity
            </p>
          </div>
        </div>

        {/* Alert count badge */}
        <div
          style={{
            background: alerts.length > 0 ? "#7f1d1d" : "#1e3a5f",
            color: alerts.length > 0 ? "#fca5a5" : "#7dd3fc",
            borderRadius: 20,
            padding: "4px 12px",
            fontSize: 12,
            fontWeight: 600,
          }}
        >
          {loading
            ? "Loading…"
            : `${alerts.length} alert${alerts.length !== 1 ? "s" : ""}`}
        </div>
      </header>

      {/* Status banners */}
      {data && (
        <AlertBanner
          aiAvailable={data.ai_available}
          feedAvailable={data.feed_available}
          lastUpdated={data.last_updated}
        />
      )}

      {/* Map */}
      <main style={{ flex: 1, position: "relative" }}>
        {loading && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "rgba(15,23,42,0.7)",
              zIndex: 1000,
              fontSize: 14,
              color: "#94a3b8",
            }}
          >
            Loading campus map…
          </div>
        )}
        <CampusMap alerts={alerts} />
      </main>

      {/* Legend */}
      <footer
        style={{
          background: "#1e293b",
          borderTop: "1px solid #334155",
          padding: "8px 16px",
          display: "flex",
          gap: 20,
          alignItems: "center",
          flexShrink: 0,
        }}
      >
        {[
          { color: "#ef4444", label: "High" },
          { color: "#f59e0b", label: "Medium" },
          { color: "#22c55e", label: "Low" },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                background: color,
                display: "inline-block",
              }}
            />
            <span style={{ fontSize: 11, color: "#94a3b8" }}>{label} severity</span>
          </div>
        ))}
        <span style={{ marginLeft: "auto", fontSize: 11, color: "#475569" }}>
          Click a pin for details
        </span>
      </footer>
    </div>
  );
}
