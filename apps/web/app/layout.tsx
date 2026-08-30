import React from "react";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import { AuthProvider } from "@/context/AuthContext";

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
        className="antialiased bg-[#030712] text-slate-100 min-h-screen overflow-x-hidden selection:bg-sky-500/20 selection:text-sky-200"
        suppressHydrationWarning
        style={{ margin: 0, padding: 0 }}
      >
        <AuthProvider>
          <div className="flex min-h-screen w-full bg-[#030712] text-slate-100 overflow-x-hidden">
            <React.Suspense
              fallback={
                <aside
                  className="w-[250px] min-w-[250px] max-w-[250px] h-screen bg-[#070a10] border-r border-white/[0.07] sticky top-0 z-[110]"
                />
              }
            >
              <Sidebar />
            </React.Suspense>
            <div className="flex flex-col flex-1 min-w-0 min-h-screen overflow-x-hidden bg-[#030712]">
              <Header />
              <main className="flex-1 p-3.5 sm:p-5 md:p-6 lg:p-7 overflow-y-auto overflow-x-hidden max-w-full">
                {children}
              </main>
            </div>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
