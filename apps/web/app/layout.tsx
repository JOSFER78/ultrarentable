import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export const metadata: Metadata = {
  title: "UltraRentable — Laboratorio de Estrategias",
  description:
    "Laboratorio de búsqueda de estrategias con StrategyQuant X: la IA busca, prueba y ejecuta por ti, con dos caminos: multiplicar tu cuenta (UltraRentable) o pasar evaluaciones de fondeo.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <div className="app-shell">
          <Sidebar />
          <div className="main-content" id="main-content">
            <Header />
            <main className="page-content">{children}</main>
            <footer className="footer">
              El objetivo ≥1000% es un criterio de investigación histórica, no una
              garantía. La aplicación no muestra resultados sin artefactos reales
              y reproducibles.
            </footer>
          </div>
        </div>
      </body>
    </html>
  );
}
