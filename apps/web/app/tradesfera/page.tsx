"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  ShieldCheck,
  TrendingUp,
  Brain,
  Layers,
  Calculator,
  Award,
  ChevronRight,
  ExternalLink,
  Zap,
  Building2,
  DollarSign,
  PieChart,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  FileText,
  Clock,
  Flame,
} from "lucide-react";

interface ModuleMeta {
  id: string;
  number: string;
  title: string;
  category: "DOCTRINA" | "MATEMÁTICA" | "OPERATIVA" | "PSICOTRADING" | "EJECUCIÓN";
  readTime: string;
  summary: string;
  keyRule: string;
  filePath: string;
}

const TRADESFERA_MODULES: ModuleMeta[] = [
  {
    id: "01",
    number: "M01",
    title: "Ecosistema Tradesfera & Modelo de Negocio",
    category: "DOCTRINA",
    readTime: "12 min",
    summary: "Arquitectura de las 4 Puertas, fundador Vicente Pons, Public Ledger auditado de 167K€ y estructura de partners.",
    keyRule: "Una cuenta de fondeo no es un patrimonio: es un vehículo asimétrico de extracción con vida útil finita.",
    filePath: "docs/tradesfera/01_ECOSISTEMA_TRADESFERA_Y_MODELO_DE_NEGOCIO.md",
  },
  {
    id: "02",
    number: "M02",
    title: "Matemática de Bankroll & Capital Munición",
    category: "MATEMÁTICA",
    readTime: "18 min",
    summary: "Formulación de munición (N disparos), Esperanza Matemática Positiva (EV), distribución binomial y regla de cosecha 50/30/20.",
    keyRule: "P(Aprobación >= 1) = 1 - (1 - p)^N. Con 10 balas y p=26.6%, la probabilidad de cobrar supera el 95%.",
    filePath: "docs/tradesfera/02_MATEMATICA_BANKROLL_Y_CAPITAL_MUNICION.md",
  },
  {
    id: "03",
    number: "M03",
    title: "Teoría de Varianza & Control de Rachas",
    category: "MATEMÁTICA",
    readTime: "15 min",
    summary: "Curvas de drawdown intradía vs EOD, cálculo de Ruina Absoluta y mitigación de rachas negativas consecutivas.",
    keyRule: "El trailing intradía aumenta la probabilidad de quiebra un 340% frente al trailing EOD a cierre de sesión.",
    filePath: "docs/tradesfera/03_TEORIA_VARIANZA_Y_CONTROL_DE_RACHAS.md",
  },
  {
    id: "04",
    number: "M04",
    title: "Protocolo Inteligente de Aprobación de Cuentas",
    category: "OPERATIVA",
    readTime: "14 min",
    summary: "Fases de evaluación, gestión de microcontratos (MES/MNQ) y timing óptimo para superar el profit target sin sobreexposición.",
    keyRule: "Nunca operar contratos grandes en fase de examen: 2 micros arriesgando $60-$80 por operación garantizan longevidad.",
    filePath: "docs/tradesfera/04_PROTOCOLO_INTELIGENTE_APROBACION_CUENTAS.md",
  },
  {
    id: "05",
    number: "M05",
    title: "Sistema Multicuenta & Copytrading",
    category: "OPERATIVA",
    readTime: "16 min",
    summary: "Topología master-slave con NinjaTrader / Rithmic / Tradovate. Desincronización de milisegundos para evitar flags de copytrading.",
    keyRule: "Diversificar 20 cuentas entre 4 empresas (5 por firma) elimina el riesgo de impago individual de un prop broker.",
    filePath: "docs/tradesfera/05_SISTEMA_MULTICUENTA_Y_COPYTRADING.md",
  },
  {
    id: "06",
    number: "M06",
    title: "Ciclo Óptimo de Retiros & Payouts",
    category: "OPERATIVA",
    readTime: "14 min",
    summary: "Calendario de transferencias bancarias semanales rotativas entre 4 a 6 firmas complementarias.",
    keyRule: "Regla 80/20: 80% del payout va a patrimonio bancario seguro; 20% a la Caja de Munición para recomprar exámenes.",
    filePath: "docs/tradesfera/06_CICLO_OPTIMO_RETIROS_Y_PAYOUTS.md",
  },
  {
    id: "07",
    number: "M07",
    title: "Psicología del Fondeo & Sesgos Operativos",
    category: "PSICOTRADING",
    readTime: "20 min",
    summary: "Neurobiología del trader, erradicación de la falacia de los $50,000 nominales y protocolos de reseteo del córtex prefrontal.",
    keyRule: "Una cuenta de $50k con drawdown de $2,000 tiene SOLO $2,000 de capital real. Tu apalancamiento real es 25x mayor.",
    filePath: "docs/tradesfera/07_PSICOLOGIA_DEL_FONDEO_Y_SESGOS_OPERATIVOS.md",
  },
  {
    id: "08",
    number: "M08",
    title: "Comparativa Prop Firms Futuros CME",
    category: "DOCTRINA",
    readTime: "15 min",
    summary: "Análisis forense de MyFundedFutures, Tradeify, TradeDay, BluSky, Lucid, Apex, Topstep, TakeProfitTrader y Bulenox.",
    keyRule: "Priorizar firmas con trailing EOD estricto y sin activación oculta: Tradeify y MyFundedFutures lideran el ranking.",
    filePath: "docs/tradesfera/08_COMPARATIVA_PROP_FIRMS_FUTUROS_CME.md",
  },
  {
    id: "09",
    number: "M09",
    title: "Infraestructura Técnica NinjaTrader Tools",
    category: "EJECUCIÓN",
    readTime: "18 min",
    summary: "VPS de baja latencia en Chicago (CME Aurora), configuración de brackets automáticos y conexión multi-gateway.",
    keyRule: "Configuración obligatoria de Hard Stop Loss en el servidor del broker antes de enviar la orden de mercado.",
    filePath: "docs/tradesfera/09_INFRAESTRUCTURA_TECNICA_NINJATRADER_TOOLS.md",
  },
  {
    id: "10",
    number: "M10",
    title: "Dossier Maestro: Tratado Integral Tradesfera",
    category: "DOCTRINA",
    readTime: "30 min",
    summary: "Tratado general que unifica los 16 módulos: microestructura cuantitativa, psicoterapia y marco de ejecución.",
    keyRule: "El sistema cuantitativo Tradesfera eleva la tasa de fondeo de la industria del 2.5% a un 26.6% auditado.",
    filePath: "docs/tradesfera/10_DOSSIER_MAESTRO_TRADESFERA_FONDEO_FUTUROS.md",
  },
  {
    id: "11",
    number: "M11",
    title: "Estrategias & Horarios Gerard García",
    category: "EJECUCIÓN",
    readTime: "16 min",
    summary: "Ventanas de liquidez institucional CME (08:30–11:00 EST / 14:30–17:00 CET), aperturas de sesión y patrones de absorción.",
    keyRule: "El 80% del profit se produce en los primeros 45 minutos tras la campana de Wall Street. Prohibido operar fuera de ventana.",
    filePath: "docs/tradesfera/11_ESTRATEGIAS_Y_HORARIOS_GERARD_GARCIA_FUTUROS.md",
  },
  {
    id: "12",
    number: "M12",
    title: "Maestría Psicológica (El Psicólogo del Trading)",
    category: "PSICOTRADING",
    readTime: "22 min",
    summary: "Protocolos clínicos de Víctor Corrales (@Elpsicologodeltrading): parada de pensamiento, desensibilización sistemática y diario de tilt.",
    keyRule: "Ante 2 pérdidas consecutivas en el día: cierre automático de plataforma por 24 horas sin excepción.",
    filePath: "docs/tradesfera/12_MAESTRIA_PSICOLOGICA_Y_PROTOCOLOS_EL_PSICOLOGO_DEL_TRADING.md",
  },
  {
    id: "13",
    number: "M13",
    title: "Sistema Táctico de Máxima Extracción",
    category: "OPERATIVA",
    readTime: "18 min",
    summary: "Secuencia matemática de cobros por niveles, amortización del colchón de seguridad y transición a cuenta live real.",
    keyRule: "Cosechar el primer payout en cuanto se desbloquee el umbral mínimo; nunca dejar acumular capital en un prop broker.",
    filePath: "docs/tradesfera/13_SISTEMA_TACTICO_MAXIMA_EXTRACCION_POR_EMPRESA.md",
  },
  {
    id: "14",
    number: "M14",
    title: "Hacks, Shorts & Reglas Rápidas de Fondeo",
    category: "EJECUCIÓN",
    readTime: "12 min",
    summary: "Cheat sheet de 25 reglas anti-descalificación: gestión de noticias NFP/FOMC, consistencia del 30% y micro-pips.",
    keyRule: "Comprobar el calendario económico 15 minutos antes de la sesión; cancelar todas las órdenes 2 minutos antes de noticias de alto impacto.",
    filePath: "docs/tradesfera/14_HACKS_SHORTS_Y_REGLAS_RAPIDAS_DE_FONDEO.md",
  },
  {
    id: "15",
    number: "M15",
    title: "Arbitraje de Negocio, Promos & Fiscalidad",
    category: "DOCTRINA",
    readTime: "16 min",
    summary: "Aprovechamiento de cupones del 80%-90%, deducción del coste de exámenes y tributación óptima como facturación de servicios.",
    keyRule: "Los payouts de prop firms se tributan como rendimiento de actividad económica / prestación de servicios, no como ganancia patrimonial directa.",
    filePath: "docs/tradesfera/15_ARBITRAJE_DE_NEGOCIO_PROMOS_Y_FISCALIDAD.md",
  },
  {
    id: "16",
    number: "M16",
    title: "Playbook Operativo Diario & Checklist",
    category: "EJECUCIÓN",
    readTime: "10 min",
    summary: "Checklist de 7 pasos antes del primer click: conexión ping, sincronización de cuentas esclavas, nivel de drawdown y estado mental.",
    keyRule: "Si el checklist falla en un solo punto, la sesión queda cancelada automáticamente.",
    filePath: "docs/tradesfera/16_PLAYBOOK_OPERATIVO_DIARIO_Y_CHECKLIST_EJECUCION.md",
  },
];

export default function TradesferaPortalPage() {
  const [selectedModule, setSelectedModule] = useState<ModuleMeta>(TRADESFERA_MODULES[0]);
  const [activeCategory, setActiveCategory] = useState<string>("ALL");

  // Calculadora de Bankroll interactiva
  const [bankroll, setBankroll] = useState<number>(3000);
  const [examCost, setExamCost] = useState<number>(38);
  const [passRate, setPassRate] = useState<number>(26.6);
  const [payoutTarget, setPayoutTarget] = useState<number>(2500);

  const numBullets = Math.floor(bankroll / examCost);
  const p = passRate / 100;
  const passProb = 1 - Math.pow(1 - p, numBullets);
  const expectedValue = passProb * payoutTarget - bankroll;

  const filteredModules = activeCategory === "ALL"
    ? TRADESFERA_MODULES
    : TRADESFERA_MODULES.filter((m) => m.category === activeCategory);

  return (
    <div style={{ maxWidth: "1400px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. HERO INSTITUCIONAL TRADESFERA */}
      <div
        style={{
          background: "linear-gradient(180deg, #0d131f 0%, #080c14 100%)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "10px",
          padding: "24px 28px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "20px",
        }}
      >
        <div style={{ maxWidth: "780px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <span
              style={{
                fontSize: "10.5px",
                fontWeight: 700,
                fontFamily: "var(--font-mono, monospace)",
                color: "#fbbf24",
                background: "rgba(251, 191, 36, 0.1)",
                border: "1px solid rgba(251, 191, 36, 0.25)",
                padding: "2px 8px",
                borderRadius: "4px",
              }}
            >
              TRATADO MAESTRO V2
            </span>
            <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
              FUTUROS CME · METODOLOGÍA TRADESFERA
            </span>
          </div>

          <h1 style={{ fontSize: "24px", fontWeight: 700, color: "#f8fafc", margin: "0 0 8px 0", letterSpacing: "-0.3px" }}>
            Portal Maestro Tradesfera: Sistema Inteligente de Extracción de Capital
          </h1>

          <p style={{ fontSize: "13.5px", color: "#94a3b8", lineHeight: 1.5, margin: 0 }}>
            Síntesis cuantitativa del tratado integral de 18 módulos: matemática de bankroll munición, varianza y control de drawdown EOD, psicotrading clínico y arquitectura multicuenta de futuros CME.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <div
            style={{
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid rgba(255, 255, 255, 0.07)",
              borderRadius: "8px",
              padding: "12px 16px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>TASA AUDITADA</div>
            <div style={{ fontSize: "20px", fontWeight: 700, color: "#10b981", fontFamily: "var(--font-mono, monospace)" }}>26.6%</div>
            <div style={{ fontSize: "9.5px", color: "#475569" }}>vs 2.5% media industria</div>
          </div>

          <div
            style={{
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid rgba(255, 255, 255, 0.07)",
              borderRadius: "8px",
              padding: "12px 16px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>CORPUS DOCUMENTAL</div>
            <div style={{ fontSize: "20px", fontWeight: 700, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>18 MÓDULOS</div>
            <div style={{ fontSize: "9.5px", color: "#475569" }}>Dossier completo en disco</div>
          </div>
        </div>
      </div>

      {/* 2. LAS 4 PUERTAS DEL ECOSISTEMA TRADESFERA */}
      <div>
        <div style={{ fontSize: "11px", fontWeight: 600, color: "#64748b", letterSpacing: "0.8px", marginBottom: "10px", fontFamily: "var(--font-mono, monospace)" }}>
          ARQUITECTURA DE LAS 4 PUERTAS TRADESFERA
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "12px" }}>
          <div style={{ background: "#0b0f19", border: "1px solid rgba(255, 255, 255, 0.07)", borderRadius: "8px", padding: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
              <div style={{ width: "24px", height: "24px", borderRadius: "4px", background: "rgba(251, 191, 36, 0.1)", color: "#fbbf24", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "11px", fontWeight: 700 }}>1</div>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "#f1f5f9" }}>Descuentos Centralizados</div>
            </div>
            <p style={{ fontSize: "12px", color: "#94a3b8", lineHeight: 1.4, margin: "0 0 10px 0" }}>
              Convenio unificado con las mejores prop firms de futuros CME con código <code style={{ color: "#fbbf24", background: "rgba(251,191,36,0.1)", padding: "1px 4px", borderRadius: "3px" }}>TRADESFERA</code> (50%-90% OFF).
            </p>
            <div style={{ fontSize: "11px", color: "#10b981", fontFamily: "var(--font-mono, monospace)" }}>Tradeify · MyFundedFutures · TradeDay</div>
          </div>

          <div style={{ background: "#0b0f19", border: "1px solid rgba(255, 255, 255, 0.07)", borderRadius: "8px", padding: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
              <div style={{ width: "24px", height: "24px", borderRadius: "4px", background: "rgba(56, 189, 248, 0.1)", color: "#38bdf8", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "11px", fontWeight: 700 }}>2</div>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "#f1f5f9" }}>Sistema de Ticks</div>
            </div>
            <p style={{ fontSize: "12px", color: "#94a3b8", lineHeight: 1.4, margin: "0 0 10px 0" }}>
              Acumulación de Ticks por cada examen adquirido, canjeables por cuentas gratuitas, reseteos y herramientas operativas en NinjaTrader.
            </p>
            <div style={{ fontSize: "11px", color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>account.tradesfera.com</div>
          </div>

          <div style={{ background: "#0b0f19", border: "1px solid rgba(255, 255, 255, 0.07)", borderRadius: "8px", padding: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
              <div style={{ width: "24px", height: "24px", borderRadius: "4px", background: "rgba(168, 85, 247, 0.1)", color: "#a855f7", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "11px", fontWeight: 700 }}>3</div>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "#f1f5f9" }}>Comunidad Auditada</div>
            </div>
            <p style={{ fontSize: "12px", color: "#94a3b8", lineHeight: 1.4, margin: "0 0 10px 0" }}>
              Canal privado de Telegram con operativa en directo de Gerard García, análisis de mercado diario y soporte de psicotrading clínico.
            </p>
            <div style={{ fontSize: "11px", color: "#c084fc", fontFamily: "var(--font-mono, monospace)" }}>Comunidad de Operadores CME</div>
          </div>

          <div style={{ background: "#0b0f19", border: "1px solid rgba(255, 255, 255, 0.07)", borderRadius: "8px", padding: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
              <div style={{ width: "24px", height: "24px", borderRadius: "4px", background: "rgba(16, 185, 129, 0.1)", color: "#10b981", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "11px", fontWeight: 700 }}>4</div>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "#f1f5f9" }}>Public Ledger Auditado</div>
            </div>
            <p style={{ fontSize: "12px", color: "#94a3b8", lineHeight: 1.4, margin: "0 0 10px 0" }}>
              Libro mayor público con más de 167,000€ en transferencias de retiros reales certificados sin sesgos de supervivencia.
            </p>
            <div style={{ fontSize: "11px", color: "#10b981", fontFamily: "var(--font-mono, monospace)" }}>167.000€+ Retiros Certificados</div>
          </div>
        </div>
      </div>

      {/* 3. CALCULADORA DE BANKROLL DE MUNICIÓN (MATEMÁTICA TRADESFERA) */}
      <div
        style={{
          background: "#0a0e17",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "10px",
          padding: "20px 24px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "14px" }}>
          <Calculator style={{ width: "16px", height: "16px", color: "#38bdf8" }} />
          <div style={{ fontSize: "14px", fontWeight: 700, color: "#f8fafc" }}>
            Calculadora Cuantitativa de Munición & Esperanza Matemática (M02)
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px", marginBottom: "18px" }}>
          <div>
            <label style={{ fontSize: "11px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>Bankroll Total de Fondeo ($):</label>
            <input
              type="number"
              value={bankroll}
              onChange={(e) => setBankroll(Number(e.target.value))}
              style={{
                width: "100%",
                background: "#111827",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "5px",
                padding: "8px 10px",
                color: "#f8fafc",
                fontSize: "13px",
                fontFamily: "var(--font-mono, monospace)",
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: "11px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>Coste Examen con Descuento ($):</label>
            <input
              type="number"
              value={examCost}
              onChange={(e) => setExamCost(Number(e.target.value))}
              style={{
                width: "100%",
                background: "#111827",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "5px",
                padding: "8px 10px",
                color: "#f8fafc",
                fontSize: "13px",
                fontFamily: "var(--font-mono, monospace)",
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: "11px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>Tasa de Aprobación Individual (%):</label>
            <input
              type="number"
              step="0.1"
              value={passRate}
              onChange={(e) => setPassRate(Number(e.target.value))}
              style={{
                width: "100%",
                background: "#111827",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "5px",
                padding: "8px 10px",
                color: "#f8fafc",
                fontSize: "13px",
                fontFamily: "var(--font-mono, monospace)",
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: "11px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>Objetivo Payout Neto ($):</label>
            <input
              type="number"
              value={payoutTarget}
              onChange={(e) => setPayoutTarget(Number(e.target.value))}
              style={{
                width: "100%",
                background: "#111827",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "5px",
                padding: "8px 10px",
                color: "#f8fafc",
                fontSize: "13px",
                fontFamily: "var(--font-mono, monospace)",
              }}
            />
          </div>
        </div>

        {/* RESULTADOS DE LA CALCULADORA */}
        <div
          style={{
            background: "rgba(15, 23, 42, 0.7)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "6px",
            padding: "14px 18px",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "14px",
          }}
        >
          <div>
            <div style={{ fontSize: "10.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>DISPAROS / BALAS (N)</div>
            <div style={{ fontSize: "18px", fontWeight: 700, color: "#f8fafc", fontFamily: "var(--font-mono, monospace)" }}>{numBullets} intentos</div>
          </div>

          <div>
            <div style={{ fontSize: "10.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>PROB. APROBAR AL MENOS 1</div>
            <div style={{ fontSize: "18px", fontWeight: 700, color: passProb > 0.9 ? "#10b981" : "#f59e0b", fontFamily: "var(--font-mono, monospace)" }}>
              {(passProb * 100).toFixed(2)}%
            </div>
          </div>

          <div>
            <div style={{ fontSize: "10.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>ESPERANZA MATEMÁTICA (EV)</div>
            <div style={{ fontSize: "18px", fontWeight: 700, color: expectedValue > 0 ? "#10b981" : "#ef4444", fontFamily: "var(--font-mono, monospace)" }}>
              {expectedValue > 0 ? "+" : ""}${expectedValue.toFixed(2)}
            </div>
          </div>

          <div>
            <div style={{ fontSize: "10.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>COSECHA REGLA 80/20</div>
            <div style={{ fontSize: "14px", fontWeight: 600, color: "#cbd5e1" }}>
              ${(payoutTarget * 0.8).toFixed(0)} Banco / ${(payoutTarget * 0.2).toFixed(0)} Caja
            </div>
          </div>
        </div>
      </div>

      {/* 4. EXPLORADOR INTERACTIVO DE LOS 18 MÓDULOS */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 600, color: "#64748b", letterSpacing: "0.8px", fontFamily: "var(--font-mono, monospace)" }}>
              CORPUS DOCUMENTAL TRADESFERA V2
            </div>
            <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#f8fafc", margin: "2px 0 0 0" }}>
              18 Módulos Especializados en Disco
            </h2>
          </div>

          <div style={{ display: "flex", gap: "4px", background: "rgba(15, 23, 42, 0.6)", padding: "3px", borderRadius: "6px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
            {["ALL", "DOCTRINA", "MATEMÁTICA", "OPERATIVA", "PSICOTRADING", "EJECUCIÓN"].map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                style={{
                  background: activeCategory === cat ? "rgba(255, 255, 255, 0.08)" : "transparent",
                  border: activeCategory === cat ? "1px solid rgba(255, 255, 255, 0.15)" : "1px solid transparent",
                  color: activeCategory === cat ? "#f8fafc" : "#94a3b8",
                  padding: "4px 10px",
                  borderRadius: "4px",
                  fontSize: "11px",
                  fontWeight: activeCategory === cat ? 600 : 500,
                  cursor: "pointer",
                  transition: "all 0.12s",
                }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "12px" }}>
          {filteredModules.map((mod) => {
            const isSelected = selectedModule.id === mod.id;
            return (
              <div
                key={mod.id}
                onClick={() => setSelectedModule(mod)}
                style={{
                  background: isSelected ? "rgba(30, 41, 59, 0.4)" : "#090d16",
                  border: isSelected ? "1px solid #38bdf8" : "1px solid rgba(255, 255, 255, 0.06)",
                  borderRadius: "8px",
                  padding: "16px",
                  cursor: "pointer",
                  transition: "all 0.12s ease",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: "10px",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <span
                      style={{
                        fontSize: "10px",
                        fontFamily: "var(--font-mono, monospace)",
                        fontWeight: 700,
                        color: "#38bdf8",
                        background: "rgba(56, 189, 248, 0.1)",
                        padding: "1px 5px",
                        borderRadius: "3px",
                      }}
                    >
                      {mod.number}
                    </span>
                    <span style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                      {mod.readTime}
                    </span>
                  </div>

                  <h3 style={{ fontSize: "13.5px", fontWeight: 600, color: "#f8fafc", margin: "0 0 6px 0", lineHeight: 1.3 }}>
                    {mod.title}
                  </h3>

                  <p style={{ fontSize: "11.5px", color: "#94a3b8", lineHeight: 1.4, margin: "0 0 8px 0" }}>
                    {mod.summary}
                  </p>
                </div>

                <div
                  style={{
                    background: "rgba(0, 0, 0, 0.3)",
                    borderLeft: "2px solid #fbbf24",
                    padding: "6px 8px",
                    borderRadius: "0 4px 4px 0",
                    fontSize: "11px",
                    color: "#cbd5e1",
                    fontStyle: "italic",
                  }}
                >
                  "{mod.keyRule}"
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
