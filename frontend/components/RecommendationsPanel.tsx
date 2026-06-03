"use client";

import { useEffect, useRef, useState } from "react";
import { API_URL } from "@/lib/config";
import { useWindowWidth } from "@/lib/useWindowWidth";
import { colors } from "@/lib/tokens";

interface Event {
  id: string;
  title: string;
  category: string;
  building: string;
  date: string;
  description: string;
  url?: string;
}

interface Props {
  hashedNetid: string;
  major: string | null;
  onMajorChange: (major: string) => void;
}

const CATEGORY_COLOR: Record<string, string> = {
  technology: "#3b82f6",
  science:    "#10b981",
  business:   "#f59e0b",
  arts:       "#a855f7",
  health:     "#ec4899",
  social:     "#06b6d4",
  sports:     "#ef4444",
};

const MODE_LABEL: Record<string, string> = {
  "cold-start":              "Seeded by major",
  "popularity":              "Trending on campus",
  "collaborative-filtering": "Personalized for you",
};

export default function RecommendationsPanel({ hashedNetid, major, onMajorChange }: Props) {
  const isMobile = useWindowWidth() < 768;
  const [events, setEvents] = useState<Event[]>([]);
  const [mode, setMode] = useState("");
  const [loading, setLoading] = useState(true);
  const [majorInput, setMajorInput] = useState(major ?? "");
  const [clickedIds, setClickedIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [displayCount, setDisplayCount] = useState(10);
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchRecommendations();
  }, [hashedNetid, major]);

  async function fetchRecommendations() {
    setLoading(true);
    setDisplayCount(10);
    try {
      const params = new URLSearchParams({ hashed_netid: hashedNetid, limit: "200" });
      if (major) params.set("major", major);
      const res = await fetch(`${API_URL}/api/recommendations?${params}`);
      const json = await res.json();
      setEvents(json.events ?? []);
      setMode(json.mode ?? "");
    } catch {
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleEventClick(event: Event) {
    try {
      await fetch(`${API_URL}/api/interactions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hashed_netid: hashedNetid, event_id: event.id }),
      });
    } catch {
      // Non-critical — don't block the UI
    }
    setClickedIds((prev) => new Set(prev).add(event.id));
    if (event.url) window.open(event.url, "_blank", "noopener,noreferrer");
  }

  function handleMajorSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (majorInput.trim()) onMajorChange(majorInput.trim());
  }

  // Search checks all fetched events regardless of displayCount
  const filteredEvents = search.trim()
    ? events.filter((e) =>
        e.title.toLowerCase().includes(search.toLowerCase()) ||
        e.description.toLowerCase().includes(search.toLowerCase()) ||
        e.category.toLowerCase().includes(search.toLowerCase())
      )
    : events.slice(0, displayCount);

  const hasMore = !search.trim() && displayCount < events.length;

  // Infinite scroll — load next 10 when sentinel comes into view
  useEffect(() => {
    if (!sentinelRef.current) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore) {
          setDisplayCount((prev) => Math.min(prev + 10, events.length));
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [hasMore, events.length]);

  return (
    <aside
      style={{
        width: isMobile ? "100%" : 280,
        height: isMobile ? "40vh" : "auto",
        flexShrink: 0,
        background: colors.bgBase,
        borderLeft: isMobile ? "none" : `1px solid ${colors.bgPanel}`,
        borderTop: isMobile ? `1px solid ${colors.bgPanel}` : "none",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Panel header */}
      <div
        style={{
          padding: "14px 16px 10px",
          borderBottom: `1px solid ${colors.bgPanel}`,
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, color: colors.textPrimary }}>For You</h2>
          {mode && (
            <span
              style={{
                fontSize: 10,
                color: colors.textMuted,
                background: colors.bgPanel,
                borderRadius: 10,
                padding: "2px 8px",
              }}
            >
              {MODE_LABEL[mode] ?? mode}
            </span>
          )}
        </div>

        <form onSubmit={handleMajorSubmit} style={{ marginTop: 8, display: "flex", gap: 6 }}>
          <input
            type="text"
            placeholder="Your major (optional)"
            value={majorInput}
            onChange={(e) => setMajorInput(e.target.value)}
            style={{
              flex: 1,
              fontSize: 11,
              padding: "5px 8px",
              background: colors.bgPanel,
              border: `1px solid ${colors.border}`,
              borderRadius: 4,
              color: colors.textPrimary,
            }}
          />
          <button
            type="submit"
            style={{
              fontSize: 11,
              padding: "5px 8px",
              background: colors.border,
              border: "none",
              borderRadius: 4,
              color: colors.textMuted,
              cursor: "pointer",
            }}
          >
            Set
          </button>
        </form>

        <div style={{ marginTop: 8, position: "relative" }}>
          <input
            type="text"
            placeholder="Search events…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: "100%",
              fontSize: 11,
              padding: "5px 24px 5px 8px",
              background: colors.bgPanel,
              border: `1px solid ${colors.border}`,
              borderRadius: 4,
              color: colors.textPrimary,
              boxSizing: "border-box",
            }}
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              style={{
                position: "absolute",
                right: 6,
                top: "50%",
                transform: "translateY(-50%)",
                background: "transparent",
                border: "none",
                color: colors.textFaint,
                fontSize: 12,
                cursor: "pointer",
                padding: 0,
                lineHeight: 1,
              }}
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Event list */}
      <div style={{ flex: 1, overflowY: "auto" }}>
        {loading ? (
          <div style={{ padding: 16, fontSize: 12, color: colors.textDimmer, textAlign: "center" }}>
            Loading recommendations…
          </div>
        ) : filteredEvents.length === 0 ? (
          <div style={{ padding: 16, fontSize: 12, color: colors.textDimmer, textAlign: "center" }}>
            {search ? `No events matching "${search}"` : "No events available right now."}
          </div>
        ) : (
          filteredEvents.map((event) => {
            const clicked = clickedIds.has(event.id);
            const catColor = CATEGORY_COLOR[event.category] ?? colors.textFaint;
            return (
              <div
                key={event.id}
                onClick={() => handleEventClick(event)}
                style={{
                  padding: "12px 16px",
                  borderBottom: `1px solid ${colors.bgPanel}`,
                  cursor: "pointer",
                  background: clicked ? colors.bgClicked : "transparent",
                  transition: "background 0.15s",
                }}
                onMouseEnter={(e) => {
                  if (!clicked) (e.currentTarget as HTMLDivElement).style.background = colors.bgPanel;
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLDivElement).style.background = clicked ? colors.bgClicked : "transparent";
                }}
              >
                <div style={{ display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 4 }}>
                  <span
                    style={{
                      fontSize: 9,
                      fontWeight: 700,
                      color: catColor,
                      background: `${catColor}22`,
                      border: `1px solid ${catColor}44`,
                      borderRadius: 4,
                      padding: "2px 6px",
                      whiteSpace: "nowrap",
                      marginTop: 1,
                      textTransform: "uppercase",
                    }}
                  >
                    {event.category}
                  </span>
                  {clicked && (
                    <span style={{ fontSize: 9, color: colors.lowBorder, marginTop: 2 }}>viewed</span>
                  )}
                  {event.url && (
                    <span style={{ fontSize: 9, color: colors.textFaint, marginTop: 2, marginLeft: "auto" }}>↗ details</span>
                  )}
                </div>
                <div style={{ fontSize: 12, fontWeight: 600, color: colors.textSecondary, marginBottom: 4, lineHeight: 1.3 }}>
                  {event.title}
                </div>
                <div style={{ fontSize: 11, color: colors.textFaint }}>
                  {event.building} · {event.date}
                </div>
                <div style={{ fontSize: 11, color: colors.textDimmer, marginTop: 4, lineHeight: 1.4 }}>
                  {event.description}
                </div>
              </div>
            );
          })
        )}

        {/* Sentinel must be inside the scrollable div to trigger IntersectionObserver */}
        {hasMore && (
          <div
            ref={sentinelRef}
            style={{ padding: "10px 16px", textAlign: "center", fontSize: 11, color: colors.textFaint }}
          >
            Loading more… ({events.length - displayCount} remaining)
          </div>
        )}
      </div>

      <div
        style={{
          padding: "8px 16px",
          borderTop: `1px solid ${colors.bgPanel}`,
          fontSize: 10,
          color: colors.border,
          flexShrink: 0,
        }}
      >
        Click an event to log your interest
      </div>
    </aside>
  );
}
