"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Zap,
  GitFork,
  BookOpen,
  Activity,
  ShieldCheck,
  Database,
  PieChart,
  RefreshCw,
  ArrowRight,
  Radio,
  Building2,
  Lock,
  Flame,
  CheckCircle2,
  Sparkles,
  TrendingUp,
  Award,
  Layers,
  ArrowUpRight,
  Key,
} from "lucide-react";
import {
  getCandidates,
  getCertifiedMetaStrategies,
  getCertifiedStrategies,
  getDiscoveryStatus,
  type CandidateStrategy,
  type CertifiedMetaStrategy,
  type CertifiedStrategy,
  type DiscoveryStatus,
} from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import AuthModal from "@/components/auth/AuthModal";

export default function HomePage() {
  const { user, profile, loading: authLoading } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalTab, setAuthModalTab] = useState<"login" | "register">("register");

  const [candidates, setCandidates] = useState<CandidateStrategy[]>([]);
  const [certified, setCertified] = useState<CertifiedStrategy[]>([]);
  const [meta, setMeta] = useState<CertifiedMetaStrategy[]>([]);
  const [discovery, setDiscovery] = useState<DiscoveryStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const [candidateResult, certifiedResult, metaResult, discoveryResult] = await Promise.all([
        getCandidates({ limit: 100 }),
        getCertifiedStrategies(),
        getCertifiedMetaStrategies(),
        getDiscoveryStatus(),
      ]);
      setCandidates(Array.isArray(candidateResult) ? candidateResult : []);
      setCertified(Array.isArray(certifiedResult) ? certifiedResult : []);
      setMeta(Array.isArray(metaResult) ? metaResult : []);
      setDiscovery(discoveryResult || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sin conexión con API canónica.");
      setCandidates([]);
      setCertified([]);
      setMeta([]);
      setDiscovery(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const openAuth = (tab: "login" | "register") => {
    setAuthModalTab(tab);
    setAuthModalOpen(true);
  };

  // =========================================================================
  // VISTA 1: LANDING EXPLICATIVO (SI NO HAY USUARIO REGISTRADO / AUTENTICADO)
  // =========================================================================
  if (!user && !authLoading) {
    return (
      <div className="w-full max-w-6xl mx-auto space-y-12 py-6 sm:py-10 font-sans animate-in fade-in duration-300">
        <AuthModal isOpen={authModalOpen} onClose={() => setAuthModalOpen(false)} initialTab={authModalTab} />

        {/* 1. HERO PRINCIPAL */}
        <section className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-slate-900/90 via-slate-950/95 to-[#030712] border border-white/[0.08] p-8 sm:p-12 text-center space-y-6 shadow-2xl">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 text-xs font-mono font-bold tracking-wider uppercase">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>Laboratorio Cuantitativo Institucional v5.4.0</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight max-w-4xl mx-auto leading-tight sm:leading-tight">
            Minería Algorítmica, 11 Evidence Gates y Meta-Portafolios con{" "}
            <span className="bg-gradient-to-r from-emerald-400 via-sky-400 to-indigo-400 bg-clip-text text-transparent">
              Evidencia Real
            </span>
          </h1>

          <p className="text-slate-400 text-sm sm:text-base max-w-3xl mx-auto leading-relaxed">
            Plataforma institucional de investigación determinista y ejecución automatizada. Toda estrategia es auditada en holdout ciego fuera de muestra (OOS) y protegida por la doctrina inmutable{" "}
            <strong className="text-slate-200 font-mono">Zero-Mocks · Real-Only</strong>.
          </p>

          {/* BOTONES DE ACCIÓN PRINCIPALES */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <button
              onClick={() => openAuth("register")}
              className="px-6 py-3.5 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-black text-sm tracking-wide shadow-lg shadow-emerald-900/40 transition active:scale-95 cursor-pointer flex items-center gap-2"
            >
              <Zap className="w-4 h-4 fill-current" />
              <span>Crear Cuenta Gratis</span>
            </button>

            <button
              onClick={() => openAuth("login")}
              className="px-6 py-3.5 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-bold text-sm transition active:scale-95 cursor-pointer flex items-center gap-2 shadow-sm"
            >
              <Key className="w-4 h-4 text-sky-400" />
              <span>Iniciar Sesión</span>
            </button>
          </div>

          {/* BADGES DE VERIFICACIÓN */}
          <div className="pt-6 border-t border-white/[0.06] flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400 font-mono">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Cero Datos Sintéticos (Zero-Mocks)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-sky-400" />
              <span>11 Evidence Gates Auditadas</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Database className="w-4 h-4 text-indigo-400" />
              <span>Trazabilidad SQLite WAL + SHA-256</span>
            </div>
          </div>
        </section>

        {/* 2. LOS 3 PILARES CUANTITATIVOS */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* PILAR 1 */}
          <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 sm:p-7 space-y-4 hover:border-sky-500/30 transition shadow-xl flex flex-col justify-between">
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-xl bg-sky-500/10 text-sky-400 flex items-center justify-center font-bold">
                <Building2 className="w-6 h-6" />
              </div>
              <span className="text-[11px] font-mono font-bold text-sky-400 tracking-wider uppercase block">
                Ruta 01 · Institucional
              </span>
              <h3 className="text-lg font-black text-white">Track FONDEO (CME & FX)</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Algoritmos diseñados estrictamente para superar evaluaciones de Prop Firms. Control inviolable de Drawdown ($DD \le 4.0\%$), Daily Loss Limit ($0$ violaciones) y cierre diario obligatorio a las 16:59 EST.
              </p>
            </div>
            <div className="pt-3 border-t border-white/[0.06] text-[11px] font-mono text-slate-400">
              NQ · ES · YM · GC · SI · CL · EURUSD · GBPUSD
            </div>
          </div>

          {/* PILAR 2 */}
          <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 sm:p-7 space-y-4 hover:border-amber-500/30 transition shadow-xl flex flex-col justify-between">
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold">
                <Flame className="w-6 h-6" />
              </div>
              <span className="text-[11px] font-mono font-bold text-amber-400 tracking-wider uppercase block">
                Ruta 02 · Convexidad Taleb
              </span>
              <h3 className="text-lg font-black text-white">Track ULTRA (Perpetuos)</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Asimetría convexa multi-activo con margen aislado ($100–$1,000 por bala) y piramidación secuencial autofinanciada por beneficios flotantes. Cosecha automática a Bóveda Ratchet en Spot USDT.
              </p>
            </div>
            <div className="pt-3 border-t border-white/[0.06] text-[11px] font-mono text-slate-400">
              5 Temporalidades Intradía (1m, 5m, 15m, 1h, 4h)
            </div>
          </div>

          {/* PILAR 3 */}
          <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 sm:p-7 space-y-4 hover:border-emerald-500/30 transition shadow-xl flex flex-col justify-between">
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <span className="text-[11px] font-mono font-bold text-emerald-400 tracking-wider uppercase block">
                Gobernanza Cuantitativa
              </span>
              <h3 className="text-lg font-black text-white">11 Evidence Gates</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Ninguna estrategia entra a producción sin aprobar las 11 pruebas: continuidad OHLCV, costes institucionales, significancia muestral, WFO móvil, Monte Carlo 0% ruina, estrés 3x slippage y reconciliación NautilusTrader.
              </p>
            </div>
            <div className="pt-3 border-t border-white/[0.06] text-[11px] font-mono text-slate-400">
              Holdout Ciego OOS Inviolable
            </div>
          </div>
        </section>

        {/* 3. CTA FOOTER */}
        <section className="bg-gradient-to-r from-slate-900 to-indigo-950/60 border border-white/[0.08] rounded-3xl p-8 text-center space-y-4 shadow-xl">
          <h2 className="text-xl sm:text-2xl font-black text-white">
            Desbloquea el Acceso Completo a la Plataforma
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 max-w-2xl mx-auto">
            Regístrate para explorar el Catálogo Master de Estrategias Certificadas, consultar los Meta-Portafolios Risk-Parity, conectar tu Trading Desk y exportar auditorías en Excel (.xlsx) y CSV.
          </p>
          <div className="pt-2">
            <button
              onClick={() => openAuth("register")}
              className="px-8 py-3.5 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-sm tracking-wide shadow-lg shadow-emerald-900/40 transition active:scale-95 cursor-pointer"
            >
              Comenzar Ahora con Google / Email
            </button>
          </div>
        </section>
      </div>
    );
  }

  // =========================================================================
  // VISTA 2: DASHBOARD / CENTRO DE MANDO (USUARIO AUTENTICADO)
  // =========================================================================
  const avgPf = certified.length
    ? (certified.reduce((sum, item) => sum + item.profit_factor, 0) / certified.length).toFixed(2)
    : "NO EVIDENCE";

  return (
    <div className="w-full max-w-[1560px] mx-auto space-y-6 font-sans">
      {/* HERO CANÓNICO PARA USUARIOS AUTENTICADOS */}
      <section className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 sm:p-7 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-5">
        <div className="max-w-3xl space-y-2.5">
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="text-[10.5px] font-bold font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/25 px-2.5 py-0.5 rounded-md tracking-wider">
              v5.4.0 REAL-ONLY
            </span>
            <span className="text-xs text-slate-400 font-mono tracking-wide">
              USUARIO: {user?.displayName || user?.email || "Autenticado"}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Centro de Mando Cuantitativo
          </h1>

          <p className="text-slate-400 text-xs sm:text-sm leading-relaxed">
            Plataforma institucional de investigación determinista, validación OOS ciego y ejecución algorítmica.
            Todos los datos presentados provienen exclusivamente de registros físicos verificados en base de datos SQLite WAL.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-center shrink-0">
          <button
            onClick={() => void refresh()}
            disabled={loading}
            className="inline-flex items-center gap-2 bg-[#050811] hover:bg-slate-850 text-slate-200 border border-white/[0.1] px-4 py-2 rounded-xl text-xs font-bold font-mono shadow-sm transition active:scale-95 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-sky-400" : "text-slate-400"}`} />
            <span>{loading ? "Actualizando…" : "Actualizar Motor"}</span>
          </button>
        </div>
      </section>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-950/60 border border-rose-800 text-rose-200 flex items-start gap-3 shadow-lg font-mono text-xs">
          <span className="text-rose-400 font-bold">✕ Error:</span>
          <span>{error}</span>
        </div>
      )}

      {/* TARJETAS KPI CUANTITATIVAS */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 font-mono">
        <KpiCard
          title="CANDIDATOS SQLITE WAL"
          value={loading ? "…" : String(candidates.length)}
          subtitle="Base de datos SQLite local"
          icon={Database}
          accent="#818cf8"
          href="/candidatos"
        />
        <KpiCard
          title="ESTRATEGIAS CERTIFICADAS"
          value={loading ? "…" : String(certified.length)}
          subtitle="11/11 Gates Pass (Auditadas)"
          icon={ShieldCheck}
          accent="#34d399"
          href="/gates"
        />
        <KpiCard
          title="PROFIT FACTOR MEDIO OOS"
          value={loading ? "…" : avgPf}
          subtitle="Calculado sobre Blind Holdout"
          icon={Zap}
          accent="#38bdf8"
          href="/estrategias"
        />
        <KpiCard
          title="META-PORTAFOLIOS"
          value={loading ? "…" : String(meta.length)}
          subtitle="Paridad de riesgo multiactivo"
          icon={PieChart}
          accent="#c084fc"
          href="/portfolio"
        />
      </section>

      {/* ACCESOS DIRECTOS */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <QuickLinkCard
          title="Bóveda de Estrategias Aprobadas"
          subtitle="Catálogo oficial con evidencia 11/11 gates y descarga en Excel/CSV"
          icon={Award}
          accent="#10b981"
          href="/gates"
        />
        <QuickLinkCard
          title="Portfolio Studio & Meta-Estrategias"
          subtitle="Meta-FONDEO y Meta-ULTRA con matrices de covarianza real"
          icon={PieChart}
          accent="#8b5cf6"
          href="/portfolio"
        />
        <QuickLinkCard
          title="Trading Desk CME en Vivo"
          subtitle="Terminal de ejecución institucional y control de riesgo en Tradovate/NinjaTrader"
          icon={Activity}
          accent="#06b6d4"
          href="/trading-desk"
        />
      </section>
    </div>
  );
}

function KpiCard({
  title,
  value,
  subtitle,
  icon: Icon,
  accent,
  href,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
  accent: string;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] hover:border-white/[0.18] rounded-xl p-4 sm:p-5 flex flex-col justify-between gap-3 shadow-lg transition-all hover:-translate-y-0.5 group no-underline"
    >
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{title}</span>
        <div className="p-2 rounded-lg bg-slate-900 border border-white/[0.05] group-hover:border-white/[0.15] transition">
          <Icon className="w-4 h-4 text-slate-300" />
        </div>
      </div>

      <div>
        <div className="text-2xl sm:text-3xl font-black text-white tabular-nums tracking-tight">{value}</div>
        <div className="text-[11px] text-slate-500 mt-1 font-mono">{subtitle}</div>
      </div>
    </Link>
  );
}

function QuickLinkCard({
  title,
  subtitle,
  icon: Icon,
  accent,
  href,
}: {
  title: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
  accent: string;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] hover:border-white/[0.18] rounded-2xl p-5 flex items-start gap-4 transition hover:-translate-y-0.5 group no-underline shadow-lg"
    >
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 mt-0.5"
        style={{ backgroundColor: `${accent}15`, color: accent }}
      >
        <Icon className="w-5 h-5" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <h4 className="text-sm font-bold text-white group-hover:text-emerald-300 transition truncate">
            {title}
          </h4>
          <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 transition shrink-0" />
        </div>
        <p className="text-xs text-slate-400 leading-relaxed mt-1">{subtitle}</p>
      </div>
    </Link>
  );
}
