"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function NautilusRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/gates/gate-11-nautilus-trader");
  }, [router]);

  return (
    <div style={{ minHeight: "100vh", background: "#06090e", color: "#f8fafc", padding: "40px", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-sans, system-ui)" }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: "32px", marginBottom: "12px" }}>⚡</div>
        <div style={{ fontSize: "16px", color: "#38bdf8", fontWeight: 900 }}>Redirigiendo a NautilusTrader Core (Gate 11)...</div>
        <div style={{ fontSize: "12px", color: "#64748b", marginTop: "6px" }}>Cargando motor de simulación Rust/Cython</div>
      </div>
    </div>
  );
}
