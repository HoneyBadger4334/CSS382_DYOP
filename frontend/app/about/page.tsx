import SiteNav from "@/components/SiteNav";
import { colors } from "@/lib/tokens";

const TEAM: { name: string; role: string; contributions: string[] }[] = [
  {
    name: "Kyle Hale",
    role: "Full-Stack Lead",
    contributions: [
      "FastAPI backend architecture",
      "RSS ingestion pipeline",
      "NLP summarizer integration",
    ],
  },
  {
    name: "Nehemiah Soebroto",
    role: "Frontend Lead",
    contributions: [
      "Next.js + react-leaflet map",
      "Alert banner and UI components",
      "For You recommendations panel",
      "Auth0 UW login integration",
    ],
  },
  {
    name: "Andy Vu",
    role: "AI & Data Lead",
    contributions: [
      "Collaborative filtering recommender (Surprise SVD)",
      "Supabase schema and RLS policies",
      "Cold-start and threshold logic",
    ],
  },
];

export default function AboutPage() {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: colors.bgBase }}>
      <SiteNav />

      <main style={{ flex: 1, overflowY: "auto", padding: "48px" }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: colors.textPrimary, marginBottom: 8 }}>
          About
        </h1>
        <p style={{ fontSize: 14, color: colors.textFaint, marginBottom: 12, maxWidth: 560 }}>
          Campus Pulse was built for CSS 382 — Design Your Own Project at UW Bothell.
        </p>
        <p style={{ fontSize: 14, color: colors.textFaint, marginBottom: 40, maxWidth: 560, lineHeight: 1.7 }}>
          Our goal was to solve a real problem on our own campus: critical information
          scattered across email threads that students ignore. We built a zero-friction,
          real-time map that surfaces that information where students already spend
          their time — in a browser tab.
        </p>

        <h2 style={{ fontSize: 18, fontWeight: 700, color: colors.textPrimary, marginBottom: 20 }}>
          Team
        </h2>

        <div style={{ display: "flex", flexDirection: "column", gap: 16, maxWidth: 600 }}>
          {TEAM.map((member) => (
            <div
              key={member.name}
              style={{
                background: colors.bgPanel,
                border: `1px solid ${colors.border}`,
                borderRadius: 10,
                padding: "20px 24px",
              }}
            >
              <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 12 }}>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: colors.textPrimary }}>
                  {member.name}
                </h3>
                <span
                  style={{
                    fontSize: 11,
                    color: colors.blueLight,
                    background: colors.blueDark,
                    borderRadius: 4,
                    padding: "2px 8px",
                  }}
                >
                  {member.role}
                </span>
              </div>
              <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
                {member.contributions.map((c, i) => (
                  <li
                    key={i}
                    style={{
                      fontSize: 13,
                      color: colors.textMuted,
                      paddingLeft: 14,
                      position: "relative",
                      marginBottom: 4,
                    }}
                  >
                    <span style={{ position: "absolute", left: 0, color: colors.blue }}>·</span>
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div
          style={{
            marginTop: 40,
            padding: "20px 24px",
            background: colors.bgPanel,
            border: `1px solid ${colors.border}`,
            borderRadius: 10,
            maxWidth: 600,
          }}
        >
          <h3 style={{ fontSize: 14, fontWeight: 700, color: colors.textPrimary, marginBottom: 8 }}>
            Data & Privacy
          </h3>
          <p style={{ fontSize: 13, color: colors.textMuted, lineHeight: 1.7, margin: 0 }}>
            Campus Pulse stores only three fields per interaction: a SHA-256 hashed
            Auth0 user identifier, an event ID, and a timestamp. No names, emails,
            or personally identifiable information are stored. Interaction logs older
            than one academic quarter (90 days) are automatically purged. The project
            is designed in accordance with UW FERPA guidelines.
          </p>
        </div>
      </main>
    </div>
  );
}
