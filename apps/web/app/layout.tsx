import React from "react";

export const metadata = {
  title: "UltraRentable — Quant Lab v5.3.0",
  description: "Deterministic Quantitative Strategy Discovery & Execution Engine",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="antialiased bg-slate-950 text-slate-100">{children}</body>
    </html>
  );
}
