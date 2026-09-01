import React from "react";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import AppShell from "@/components/layout/AppShell";

export const metadata = {
  // Sin número de versión hardcodeado (W5.4): la versión REAL del motor se lee en runtime de
  // getDiscoveryStatus() (ver hooks/useEngineVersion.ts) y se muestra en el Header.
  title: "UltraRentable — Quant Lab",
  description: "Deterministic Quantitative Strategy Discovery & Execution Engine (Zero-Mocks · Real-Only)",
};

export const viewport = {
  themeColor: "#0f0f0f",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className="dark" suppressHydrationWarning>
      <body
        className="antialiased bg-[var(--bg)] text-[var(--text-1)] min-h-screen overflow-x-hidden"
        suppressHydrationWarning
        style={{ margin: 0, padding: 0 }}
      >
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
