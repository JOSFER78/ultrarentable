import React from "react";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import AppShell from "@/components/layout/AppShell";

export const metadata = {
  title: "UltraRentable — Quant Lab v5.4.0",
  description: "Deterministic Quantitative Strategy Discovery & Execution Engine (Zero-Mocks · Real-Only)",
};

export const viewport = {
  themeColor: "#030712",
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
        className="antialiased bg-[#030712] text-slate-100 min-h-screen overflow-x-hidden selection:bg-emerald-500/20 selection:text-emerald-300"
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
