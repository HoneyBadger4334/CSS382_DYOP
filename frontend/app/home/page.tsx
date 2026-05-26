"use client";

import SiteNav from "@/components/SiteNav";

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
              { label: "FERPA compliant", sub: "Hashed NetID storage" },
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
