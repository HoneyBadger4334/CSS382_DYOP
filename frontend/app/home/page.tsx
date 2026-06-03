"use client";

import { useState, useEffect, useRef } from "react";
import SiteNav from "@/components/SiteNav";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://css382-dyop.onrender.com";

const BUILDINGS = ["UW1", "UW2", "LIB", "ARC", "DISC", "HH", "NCH", "CC"];
const SEVERITIES = ["high", "medium", "low"] as const;
type Severity = typeof SEVERITIES[number];

const SEVERITY_COLORS: Record<Severity, { bg: string; border: string; text: string }> = {
  high:   { bg: "#7f1d1d", border: "#ef4444", text: "#fca5a5" },
  medium: { bg: "#451a03", border: "#f59e0b", text: "#fcd34d" },
  low:    { bg: "#14532d", border: "#22c55e", text: "#86efac" },
};

function DemoControls() {
  const [building, setBuilding] = useState("UW1");
  const [severity, setSeverity] = useState<Severity>("high");
  const [countdown, setCountdown] = useState(0);
  const [status, setStatus] = useState<"idle" | "active" | "cleared">("idle");
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function clearTimer() {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }

  async function handleTrigger() {
    clearTimer();
    const res = await fetch(`${API_URL}/api/demo?building=${building}&severity=${severity}`, { method: "POST" });
    if (!res.ok) return;
    const data = await res.json();
    setCountdown(data.expires_in);
    setStatus("active");
    timerRef.current = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) {
          clearTimer();
          setStatus("cleared");
          return 0;
        }
        return c - 1;
      });
    }, 1000);
  }

  async function handleClear() {
    clearTimer();
    await fetch(`${API_URL}/api/demo/clear`, { method: "POST" });
    setCountdown(0);
    setStatus("cleared");
  }

  useEffect(() => () => clearTimer(), []);

  const col = SEVERITY_COLORS[severity];

  return (
    <section style={{ padding: "32px 48px", borderBottom: "1px solid #1e293b" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: "#f1f5f9" }}>Demo Controls</h2>
        <span style={{ fontSize: 10, fontWeight: 700, color: "#f59e0b", background: "#451a03", borderRadius: 4, padding: "2px 8px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Presentation
        </span>
      </div>

      <div style={{ display: "flex", gap: 24, flexWrap: "wrap", alignItems: "flex-end" }}>

        {/* Building selector */}
        <div>
          <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8 }}>Building</div>
          <select
            value={building}
            onChange={(e) => setBuilding(e.target.value)}
            style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 6, color: "#f1f5f9", fontSize: 13, padding: "8px 12px", cursor: "pointer" }}
          >
            {BUILDINGS.map((b) => <option key={b} value={b}>{b}</option>)}
          </select>
        </div>

        {/* Severity toggle */}
        <div>
          <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8 }}>Severity</div>
          <div style={{ display: "flex", gap: 4 }}>
            {SEVERITIES.map((s) => {
              const c = SEVERITY_COLORS[s];
              const active = severity === s;
              return (
                <button
                  key={s}
                  onClick={() => setSeverity(s)}
                  style={{ background: active ? c.bg : "#1e293b", border: `1px solid ${active ? c.border : "#334155"}`, borderRadius: 6, color: active ? c.text : "#64748b", fontSize: 12, fontWeight: 600, padding: "7px 14px", cursor: "pointer", textTransform: "capitalize" }}
                >
                  {s}
                </button>
              );
            })}
          </div>
        </div>

        {/* Trigger button */}
        <button
          onClick={handleTrigger}
          style={{ background: col.bg, border: `1px solid ${col.border}`, borderRadius: 6, color: col.text, fontSize: 13, fontWeight: 700, padding: "8px 20px", cursor: "pointer" }}
        >
          Trigger Alert
        </button>

        {/* Countdown + clear */}
        {status === "active" && countdown > 0 && (
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 6, padding: "8px 14px", fontSize: 13, color: "#94a3b8" }}>
              Auto-clear in <strong style={{ color: "#f1f5f9" }}>{countdown}s</strong>
            </div>
            <button
              onClick={handleClear}
              style={{ background: "transparent", border: "1px solid #334155", borderRadius: 6, color: "#94a3b8", fontSize: 12, padding: "8px 14px", cursor: "pointer" }}
            >
              Clear Now
            </button>
          </div>
        )}

        {status === "cleared" && (
          <div style={{ fontSize: 13, color: "#22c55e" }}>✓ Alert cleared</div>
        )}
      </div>

      <p style={{ fontSize: 12, color: "#475569", marginTop: 16 }}>
        Injects a live alert onto the map for 60 seconds. The live demo iframe below will update on its next poll (≤30s).
      </p>
    </section>
  );
}

export default function HomePage() {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0f172a" }}>
      <SiteNav />

      <main style={{ flex: 1, overflowY: "auto" }}>
        {/* Hero */}
        <section
          style={{
            padding: "48px 48px 32px",
            borderBottom: "1px solid #1e293b",
          }}
        >
          <div
            style={{
              display: "inline-block",
              fontSize: 11,
              fontWeight: 600,
              color: "#3b82f6",
              background: "#1e3a5f",
              borderRadius: 20,
              padding: "4px 12px",
              marginBottom: 16,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            CSS 382 — Design Your Own Project
          </div>
          <h1
            style={{
              fontSize: 36,
              fontWeight: 800,
              color: "#f1f5f9",
              marginBottom: 16,
              lineHeight: 1.2,
            }}
          >
            UW Bothell Campus Pulse
          </h1>
          <p
            style={{
              fontSize: 16,
              color: "#94a3b8",
              maxWidth: 600,
              lineHeight: 1.7,
              marginBottom: 32,
            }}
          >
            Students at UW Bothell frequently miss critical campus information — club
            events, guest lectures, and emergency alerts — because email is an
            unreliable channel many students ignore. Campus Pulse is a real-time
            browser-based map of UW Bothell that automatically surfaces alerts and
            personalized event recommendations from official university sources.
          </p>

          {/* Stat chips */}
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            {[
              { label: "AI-powered alerts", sub: "GPT-4o-mini NLP" },
              { label: "Personalized feed", sub: "Collaborative filtering" },
              { label: "FERPA compliant", sub: "Hashed user ID storage" },
              { label: "No account required", sub: "Core map is public" },
            ].map(({ label, sub }) => (
              <div
                key={label}
                style={{
                  background: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: 8,
                  padding: "12px 16px",
                }}
              >
                <div style={{ fontSize: 13, fontWeight: 600, color: "#f1f5f9" }}>
                  {label}
                </div>
                <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>
                  {sub}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Live map embed */}
        <section style={{ padding: "32px 48px", borderBottom: "1px solid #1e293b" }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "#f1f5f9", marginBottom: 16 }}>
            Live Demo
          </h2>
          <div
            style={{
              borderRadius: 10,
              overflow: "hidden",
              border: "1px solid #334155",
              height: 480,
            }}
          >
            <iframe
              src="/"
              style={{ width: "100%", height: "100%", border: "none" }}
              title="Campus Pulse Live Map"
            />
          </div>
          <p style={{ fontSize: 12, color: "#475569", marginTop: 8 }}>
            Live map — pins update every 5 minutes from the UW Alerts RSS feed.
          </p>
        </section>

        <DemoControls />

        {/* Tech stack */}
        <section style={{ padding: "32px 48px 48px" }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "#f1f5f9", marginBottom: 20 }}>
            Tech Stack
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
              gap: 12,
            }}
          >
            {[
              { layer: "Frontend",  tech: "Next.js 14 + TypeScript" },
              { layer: "Map",       tech: "OpenStreetMap + Leaflet" },
              { layer: "Backend",   tech: "FastAPI + Python 3.11" },
              { layer: "AI Alerts", tech: "GPT-4o-mini (OpenAI)" },
              { layer: "Recommender", tech: "Surprise (SVD)" },
              { layer: "Database",  tech: "PostgreSQL / Supabase" },
              { layer: "Auth",       tech: "Auth0 (UW login)" },
              { layer: "Deployment", tech: "Vercel + Render" },
            ].map(({ layer, tech }) => (
              <div
                key={layer}
                style={{
                  background: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: 8,
                  padding: "14px 16px",
                }}
              >
                <div style={{ fontSize: 10, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 4 }}>
                  {layer}
                </div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>
                  {tech}
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
