"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function EstrategiasIndexPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/sistema");
  }, [router]);

  return (
    <div style={{ minHeight: "100vh", background: "#06090e", color: "#f8fafc", padding: "40px", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: "32px", marginBottom: "12px" }}>⚡</div>
        <div style={{ fontSize: "16px", color: "#34d399", fontWeight: 900 }}>Cargando Estrategias (6 Fases)...</div>
      </div>
    </div>
  );
}
