import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "UW Bothell Campus Pulse",
  description: "Real-time campus events and emergency alerts for UW Bothell",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
