"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import AlertBanner from "@/components/AlertBanner";
import RecommendationsPanel from "@/components/RecommendationsPanel";
import type { AlertPin, CampusEventPin } from "@/components/CampusMap";

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
  const [alertsData, setAlertsData] = useState<AlertsResponse | null>(null);
  const [eventsData, setEventsData] = useState<CampusEventPin[] | null>(null);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [eventsLoading, setEventsLoading] = useState(true);

  async function fetchAlerts() {
    try {
      const res = await fetch(`${API_URL}/api/alerts`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: AlertsResponse = await res.json();
      setAlertsData(json);
    } catch {
      // Keep stale data if available; just stop showing loading spinner.
    } finally {
      setAlertsLoading(false);
    }
  }

  async function fetchEvents() {
    try {
      const res = await fetch(`${API_URL}/api/events?limit=60`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: CampusEventPin[] = await res.json();
      setEventsData(json);
    } catch {
      // Keep stale data if available; just stop showing loading spinner.
    } finally {
      setEventsLoading(false);
    }
  }

  useEffect(() => {
    fetchAlerts();
    fetchEvents();
    const alertsInterval = setInterval(fetchAlerts, POLL_MS);
    const eventsInterval = setInterval(fetchEvents, 300_000);
    return () => {
      clearInterval(alertsInterval);
      clearInterval(eventsInterval);
    };
  }, []);

  const alerts = alertsData?.alerts ?? [];
  const events = eventsData ?? [];
  const mapLoading = alertsLoading && eventsLoading;

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
              Live alerts and current events across campus.
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
          {alertsLoading
            ? "Loading alerts"
            : `${alerts.length} alert${alerts.length !== 1 ? "s" : ""}`}
        </div>
      </header>

      {alertsData && (
        <div className="dashboard-alerts">
          <AlertBanner
            aiAvailable={alertsData.ai_available}
            feedAvailable={alertsData.feed_available}
            lastUpdated={alertsData.last_updated}
          />
        </div>
      )}

      <main className="dashboard-main">
        <section className="dashboard-map">
          {mapLoading && (
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
          <CampusMap alerts={alerts} events={events} />
        </section>

        <section className="dashboard-panel">
          <RecommendationsPanel />
        </section>
      </main>

      <footer className="dashboard-footer">
        {[
          { color: "#38bdf8", label: "Events" },
          { color: "#ef4444", label: "High" },
          { color: "#f59e0b", label: "Medium" },
          { color: "#22c55e", label: "Low" },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span className="legend-dot" style={{ background: color }} />
            <span>{label}{label === "Events" ? "" : " severity"}</span>
          </div>
        ))}
        <span style={{ marginLeft: "auto" }}>Click a pin or event for details</span>
      </footer>
    </div>
  );
}
