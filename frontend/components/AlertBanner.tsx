"use client";

interface AlertBannerProps {
  aiAvailable: boolean;
  feedAvailable: boolean;
  lastUpdated: string;
}

export default function AlertBanner({ aiAvailable, feedAvailable, lastUpdated }: AlertBannerProps) {
  const minutesAgo = lastUpdated
    ? Math.floor((Date.now() - new Date(lastUpdated).getTime()) / 60000)
    : null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      {/* AI unavailable warning — renders within 3 s of API failure */}
      {!aiAvailable && (
        <div
          role="alert"
          style={{
            background: "#7c2d12",
            color: "#fed7aa",
            padding: "8px 16px",
            fontSize: 13,
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          ⚠ Live AI summarization unavailable — showing raw alert text
        </div>
      )}

      {/* RSS feed unavailable */}
      {!feedAvailable && (
        <div
          role="alert"
          style={{
            background: "#431407",
            color: "#fde68a",
            padding: "8px 16px",
            fontSize: 13,
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          ⚠ Live RSS feed unreachable — displaying cached data
        </div>
      )}

      {/* Last-updated indicator — always visible */}
      <div
        style={{
          background: "rgba(15,23,42,0.85)",
          color: "#94a3b8",
          padding: "4px 12px",
          fontSize: 11,
          textAlign: "right",
        }}
      >
        {minutesAgo === null
          ? "Fetching data…"
          : minutesAgo === 0
          ? "Last updated just now"
          : `Last updated ${minutesAgo} minute${minutesAgo !== 1 ? "s" : ""} ago`}
      </div>
    </div>
  );
}
