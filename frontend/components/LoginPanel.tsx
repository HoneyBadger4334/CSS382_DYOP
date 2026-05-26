"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Props {
  onLogin: (netid: string, hashedNetid: string) => void;
  onClose: () => void;
}

export default function LoginPanel({ onLogin, onClose }: Props) {
  const [netid, setNetid] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = netid.trim();
    if (!trimmed) return;

    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ netid: trimmed }),
      });
      const json = await res.json();
      if (json.error) throw new Error(json.error);
      onLogin(trimmed, json.hashed_netid);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    // Backdrop
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.6)",
        zIndex: 2000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Modal — stop clicks from closing */}
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "#1e293b",
          border: "1px solid #334155",
          borderRadius: 10,
          padding: "28px 32px",
          width: 340,
          boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
        }}
      >
        <h2 style={{ color: "#f1f5f9", fontSize: 16, fontWeight: 700, marginBottom: 6 }}>
          Sign in with NetID
        </h2>
        <p style={{ color: "#94a3b8", fontSize: 12, marginBottom: 20 }}>
          Your NetID is hashed before storage — raw credentials never leave your browser.
        </p>

        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="e.g. kghale"
            value={netid}
            onChange={(e) => setNetid(e.target.value)}
            autoFocus
            style={{
              width: "100%",
              padding: "10px 12px",
              borderRadius: 6,
              border: "1px solid #475569",
              background: "#0f172a",
              color: "#f1f5f9",
              fontSize: 14,
              marginBottom: 12,
              boxSizing: "border-box",
            }}
          />

          {error && (
            <p style={{ color: "#f87171", fontSize: 12, marginBottom: 10 }}>{error}</p>
          )}

          <div style={{ display: "flex", gap: 10 }}>
            <button
              type="submit"
              disabled={loading || !netid.trim()}
              style={{
                flex: 1,
                padding: "10px 0",
                background: loading || !netid.trim() ? "#334155" : "#3b82f6",
                color: "#fff",
                border: "none",
                borderRadius: 6,
                fontSize: 13,
                fontWeight: 600,
                cursor: loading || !netid.trim() ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: "10px 16px",
                background: "transparent",
                color: "#94a3b8",
                border: "1px solid #334155",
                borderRadius: 6,
                fontSize: 13,
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
