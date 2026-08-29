import React from "react";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export const metadata = {
  title: "UltraRentable — Quant Lab v5.4.0",
  description: "Deterministic Quantitative Strategy Discovery & Execution Engine (Zero-Mocks · Real-Only)",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className="antialiased bg-slate-950 text-slate-100 min-h-screen" suppressHydrationWarning style={{ margin: 0, padding: 0 }}>
        <div style={{ display: "flex", minHeight: "100vh", width: "100%" }}>
          <React.Suspense fallback={<aside style={{ width: "250px", background: "#070a10" }} />}>
            <Sidebar />
          </React.Suspense>
          <div style={{ display: "flex", flexDirection: "column", flex: 1, minWidth: 0, overflow: "hidden" }}>
            <Header />
            <main style={{ flex: 1, padding: "20px", overflowY: "auto" }}>{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
