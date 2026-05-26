"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/home",          label: "Home" },
  { href: "/how-it-works",  label: "How It Works" },
  { href: "/user-guide",    label: "User Guide" },
  { href: "/about",         label: "About" },
  { href: "/",              label: "Live Map" },
];

export default function SiteNav() {
  const pathname = usePathname();

  return (
    <nav
      style={{
        width: 200,
        flexShrink: 0,
        background: "#0f172a",
        borderRight: "1px solid #1e293b",
        display: "flex",
        flexDirection: "column",
        padding: "24px 0",
        minHeight: "100vh",
      }}
    >
      <div style={{ padding: "0 20px 24px" }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: "#f1f5f9" }}>
          Campus Pulse
        </div>
        <div style={{ fontSize: 11, color: "#475569", marginTop: 2 }}>
          UW Bothell
        </div>
      </div>

      <div style={{ flex: 1 }}>
        {LINKS.map(({ href, label }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              style={{
                display: "block",
                padding: "10px 20px",
                fontSize: 13,
                fontWeight: active ? 600 : 400,
                color: active ? "#7dd3fc" : "#94a3b8",
                background: active ? "#1e293b" : "transparent",
                borderLeft: active ? "2px solid #3b82f6" : "2px solid transparent",
                textDecoration: "none",
                transition: "all 0.15s",
              }}
            >
              {label}
            </Link>
          );
        })}
      </div>

    </nav>
  );
}
