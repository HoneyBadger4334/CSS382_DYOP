"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { useUser } from "@auth0/nextjs-auth0/client";
import AlertBanner from "@/components/AlertBanner";
import RecommendationsPanel from "@/components/RecommendationsPanel";
import type { AlertPin } from "@/components/CampusMap";

// Leaflet uses browser APIs — must be loaded client-side only.
const CampusMap = dynamic(() => import("@/components/CampusMap"), { ssr: false });

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://css382-dyop.onrender.com";
const POLL_MS = 30_000;

interface AlertsResponse {
  alerts: AlertPin[];
  last_updated: string;
  ai_available: boolean;
  feed_available: boolean;
}

async function sha256(value: string) {
  const encoded = new TextEncoder().encode(value);
  const hashBuffer = await crypto.subtle.digest("SHA-256", encoded);
  return Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export default function HomePage() {
  const { user, error: authError, isLoading: authLoading } = useUser();
  const [data, setData] = useState<AlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [netid, setNetid] = useState<string | null>(null);
  const [hashedNetid, setHashedNetid] = useState<string | null>(null);
  const [major, setMajor] = useState<string | null>(null);

  useEffect(() => {
    const storedMajor = localStorage.getItem("major");
    if (storedMajor) setMajor(storedMajor);
  }, []);

  useEffect(() => {
    if (!user) {
      setNetid(null);
      setHashedNetid(null);
      return;
    }

    const displayName = user.name ?? user.email ?? user.nickname ?? user.sub ?? "Signed in user";
    setNetid(displayName);

    const sourceId = user.sub ?? displayName;
    const storedSource = localStorage.getItem("hashed_netid_source");
    const storedHash = localStorage.getItem("hashed_netid");

    if (storedSource === sourceId && storedHash) {
      setHashedNetid(storedHash);
      return;
    }

    async function createHash() {
      const hashed = await sha256(sourceId);
      localStorage.setItem("hashed_netid", hashed);
      localStorage.setItem("hashed_netid_source", sourceId);
      setHashedNetid(hashed);
    }

    createHash();
  }, [user]);

  function handleMajorChange(m: string) {
    localStorage.setItem("major", m);
    setMajor(m);
  }

  function handleLogout() {
    localStorage.removeItem("major");
    localStorage.removeItem("hashed_netid");
    localStorage.removeItem("hashed_netid_source");
    window.location.href = "/api/auth/logout";
  }

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

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {/* Website link */}
          <a
            href="/home"
            style={{
              fontSize: 11,
              color: "#475569",
              textDecoration: "none",
              padding: "4px 8px",
              border: "1px solid #1e293b",
              borderRadius: 4,
            }}
          >
            Project Site
          </a>

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

          {/* Auth controls */}
          {netid ? (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 12, color: "#94a3b8" }}>
                Signed in as <strong style={{ color: "#f1f5f9" }}>{netid}</strong>
              </span>
              <button
                onClick={handleLogout}
                style={{
                  fontSize: 11,
                  color: "#94a3b8",
                  background: "transparent",
                  border: "1px solid #334155",
                  borderRadius: 4,
                  padding: "3px 8px",
                  cursor: "pointer",
                }}
              >
                Sign out
              </button>
            </div>
          ) : (
            <a
              href="/api/auth/login"
              style={{
                fontSize: 12,
                color: "#7dd3fc",
                background: "transparent",
                border: "1px solid #1e3a5f",
                borderRadius: 6,
                padding: "5px 12px",
                textDecoration: "none",
                fontWeight: 600,
              }}
            >
              {authLoading ? "Loading auth…" : "Sign in with Auth0"}
            </a>
          )}
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

      {/* Map + optional recommendations panel */}
      <main style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        <div style={{ flex: 1, position: "relative" }}>
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
        </div>

        {hashedNetid && (
          <RecommendationsPanel
            hashedNetid={hashedNetid}
            major={major}
            onMajorChange={handleMajorChange}
          />
        )}
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
