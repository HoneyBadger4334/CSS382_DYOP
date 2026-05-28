import type { Metadata } from "next";
import { UserProvider } from "@auth0/nextjs-auth0/client";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "UW Bothell Campus Pulse",
  description: "Real-time campus events and emergency alerts for UW Bothell",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <UserProvider>{children}</UserProvider>
      </body>
    </html>
  );
}
