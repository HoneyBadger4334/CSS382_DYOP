"use client";

import { useState } from "react";
import { API_URL } from "@/lib/config";
import { colors } from "@/lib/tokens";

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
    const trimmed = netid.trim().toLowerCase();
    if (!trimmed) return;

    if (!/^[a-z][a-z0-9]{2,7}$/.test(trimmed)) {
      setError("Enter a valid UW NetID (3–8 characters, letters and numbers only)");
      return;
    }

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
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: colors.bgPanel,
          border: `1px solid ${colors.border}`,
          borderRadius: 10,
          padding: "28px 32px",
          width: 340,
          boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
        }}
      >
        <h2 style={{ color: colors.textPrimary, fontSize: 16, fontWeight: 700, marginBottom: 6 }}>
          Sign in with NetID
        </h2>
        <p style={{ color: colors.textMuted, fontSize: 12, marginBottom: 20 }}>
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
              border: `1px solid ${colors.textDimmer}`,
              background: colors.bgBase,
              color: colors.textPrimary,
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
                background: loading || !netid.trim() ? colors.border : colors.blue,
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
                color: colors.textMuted,
                border: `1px solid ${colors.border}`,
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
