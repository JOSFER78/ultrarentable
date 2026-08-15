"use client";

import Link from "next/link";

export default function BifurcacionPage() {
  return (
    <div className="stagger">
      {/* HERO */}
      <div className="page-header animate-in" style={{ marginBottom: 12 }}>
        <div className="bifurc-hero-badge" style={{ fontFamily: "monospace", fontSize: "11px", letterSpacing: "1px" }}>
          FASE 2 DE 3 · SELECCIÓN DE OBJETIVO DE CUENTA
        </div>
        <h1 className="page-title" style={{ fontSize: 28, maxWidth: 720, marginTop: 8 }}>
          Elección de Camino y Asignación de Riesgo
        </h1>
        <p className="page-desc" style={{ maxWidth: 640 }}>
          Las estrategias generadas en la Fase 1 se adaptan y filtran según el perfil operativo seleccionado. El motor aplicará reglas estrictas de drawdown o apalancamiento dinámico.
        </p>
      </div>

      {/* CARDS */}
      <div className="bifurc-grid" style={{ marginTop: 24 }}>
        {/* CAMINO A: ULTRARRENTABLE */}
        <Link
          href="/ultra"
          className="bifurc-panel bifurc-panel--ultra animate-in"
        >
          <div className="bifurc-panel-glow" />
          <div className="bifurc-panel-icon" style={{ fontFamily: "monospace", fontWeight: 800, fontSize: "14px", color: "var(--accent)" }}>
            [ULTRA]
          </div>
          <div className="bifurc-panel-tag">CUENTA PROPIA · BINGX MULTI-BROKER</div>
          <h2 className="bifurc-panel-title">Camino A: UltraRentable</h2>
          <p className="bifurc-panel-desc">
            Búsqueda de rendimiento máximo en cuenta propia. Apalancamiento dinámico y reinversión de beneficio, priorizando la tasa de crecimiento sin restricciones de drawdown arbitrarias.
          </p>
          <ul className="bifurc-panel-feats" style={{ fontFamily: "monospace", fontSize: "12px" }}>
            <li><span className="bifurc-feat-ico">[+]</span> Objetivo: Multiplicación de capital (≥1000%)</li>
            <li><span className="bifurc-feat-ico">[+]</span> Modo extremo sin filtros de Sharpe artificiales</li>
            <li><span className="bifurc-feat-ico">[+]</span> Ejecución 100% autónoma en BingX</li>
          </ul>
          <div className="bifurc-panel-cta">
            <span>Configurar Modo Ultra</span>
            <span className="bifurc-panel-arrow">&rarr;</span>
          </div>
        </Link>

        {/* CAMINO B: FONDEO */}
        <Link
          href="/fondeo"
          className="bifurc-panel bifurc-panel--funding animate-in"
        >
          <div className="bifurc-panel-glow" />
          <div className="bifurc-panel-icon" style={{ fontFamily: "monospace", fontWeight: 800, fontSize: "14px", color: "#60a5fa" }}>
            [FONDEO]
          </div>
          <div className="bifurc-panel-tag">EMPRESAS DE FONDEO · FUTUROS PROP</div>
          <h2 className="bifurc-panel-title">Camino B: Evaluaciones de Fondeo</h2>
          <p className="bifurc-panel-desc">
            Estrategias auditadas y optimizadas para superar evaluaciones de empresas financiada (Topstep, Earn2Trade, TradeDay, MFFU, etc.) respetando límites de drawdown EOD/intradía y consistencia.
          </p>
          <ul className="bifurc-panel-feats" style={{ fontFamily: "monospace", fontSize: "12px" }}>
            <li><span className="bifurc-feat-ico">[+]</span> Control estricto de drawdown diario e intradía</li>
            <li><span className="bifurc-feat-ico">[+]</span> Compatible con 34 empresas de fondeo de futuros</li>
            <li><span className="bifurc-feat-ico">[+]</span> Monitorización de reglas de cobro y retiros</li>
          </ul>
          <div className="bifurc-panel-cta">
            <span>Configurar Modo Fondeo</span>
            <span className="bifurc-panel-arrow">&rarr;</span>
          </div>
        </Link>
      </div>

      {/* BOTTOM ASSIST */}
      <div className="bifurc-assist animate-in" style={{ marginTop: 24, padding: 18, border: "1px solid var(--border)", background: "var(--bg-2)", borderRadius: "var(--radius-md)" }}>
        <div className="bifurc-assist-text" style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
          <strong>Flujo de Trabajo Recomendado:</strong> Puedes configurar ambos caminos simultáneamente. Las estrategias de la Fase 1 se distribuirán automáticamente al entorno correspondiente según sus métricas de riesgo y consistencia.
        </div>
      </div>
    </div>
  );
}

