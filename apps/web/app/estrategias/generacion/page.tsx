"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Cpu,
  Server,
  Zap,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  Database,
  Layers,
  ChevronRight,
  ArrowRight,
  Terminal,
  Settings,
  RefreshCw,
  Sliders,
  DollarSign,
  Filter,
  Flame,
  ShieldCheck,
  Radio,
} from "lucide-react";
import {
  getDiscoveryStatus,
  getStrategyLabOverview,
  getStrategyLabSQXStatus,
  getStrategyLabStrategies,
  type StrategyLabOverview,
  type StrategyLabRecord,
} from "@/lib/api";
import NavBloques from "../_bloques/NavBloques";
import SQXToolsPanel from "../SQXToolsPanel";

interface SqxResultado {
  status?: string;
  base_url?: string;
  projects?: string[];
  version?: string;
  uptime?: string;
}

type SubmenuTab = "config_activos" | "monitor_sqx" | "crudas_extraidas" | "tools_puente";
type TrackFiltro = "FONDEO" | "ULTRA";

interface ActivoConfig {
  simbolo: string;
  microsimbolo: string;
  nombre: string;
  clase: "ÍNDICES CME" | "METALES & ENERGÍA" | "BONOS & DIVISAS" | "CRIPTO SWAP";
  timeframes: string[];
  comision: string;
  tickSize: string;
  rangoFechas: string;
  sesion: string;
  estadoDataset: "VERIFICADO_SHA256" | "PENDIENTE_INGESTA";
}

const ACTIVOS_FONDEO_CME: ActivoConfig[] = [
  {
    simbolo: "ES",
    microsimbolo: "MES",
    nombre: "Micro E-mini S&P 500",
    clase: "ÍNDICES CME",
    timeframes: ["1m", "5m", "15m", "1h", "4h"],
    comision: "$0.60 / lado (MES) · $2.50 (ES)",
    tickSize: "0.25 ($1.25 / tick MES)",
    rangoFechas: "2008 – 2026 (18 años)",
    sesion: "RTH (08:30–15:15 CST) / ETH",
    estadoDataset: "VERIFICADO_SHA256",
  },
  {
    simbolo: "NQ",
    microsimbolo: "MNQ",
    nombre: "Micro E-mini Nasdaq 100",
    clase: "ÍNDICES CME",
    timeframes: ["1m", "5m", "15m", "1h", "4h"],
    comision: "$0.60 / lado (MNQ) · $2.50 (NQ)",
    tickSize: "0.25 ($0.50 / tick MNQ)",
    rangoFechas: "2010 – 2026 (16 años)",
    sesion: "RTH / ETH",
    estadoDataset: "VERIFICADO_SHA256",
  },
  {
    simbolo: "YM",
    microsimbolo: "MYM",
    nombre: "Micro E-mini Dow Jones",
    clase: "ÍNDICES CME",
    timeframes: ["1m", "5m", "15m", "1h"],
    comision: "$0.60 / lado (MYM)",
    tickSize: "1.0 ($0.50 / tick MYM)",
    rangoFechas: "2012 – 2026 (14 años)",
    sesion: "RTH / ETH",
    estadoDataset: "VERIFICADO_SHA256",
  },
  {
    simbolo: "RTY",
    microsimbolo: "M2K",
    nombre: "Micro E-mini Russell 2000",
    clase: "ÍNDICES CME",
    timeframes: ["5m", "15m", "1h"],
    comision: "$0.60 / lado (M2K)",
    tickSize: "0.10 ($0.50 / tick M2K)",
    rangoFechas: "2015 – 2026 (11 años)",
    sesion: "RTH / ETH",
    estadoDataset: "VERIFICADO_SHA256",
  },
  {
    simbolo: "GC",
    microsimbolo: "MGC",
    nombre: "Micro Gold (Oro Físico CME)",
    clase: "METALES & ENERGÍA",
    timeframes: ["5m", "15m", "1h", "4h"],
    comision: "$0.70 / lado (MGC)",
    tickSize: "0.10 ($1.00 / tick MGC)",
    rangoFechas: "2010 – 2026 (16 años)",
    sesion: "Globex 23h",
    estadoDataset: "VERIFICADO_SHA256",
  },
  {
    simbolo: "CL",
    microsimbolo: "MCL",
    nombre: "Micro WTI Crude Oil",
    clase: "METALES & ENERGÍA",
    timeframes: ["5m", "15m", "1h"],
    comision: "$0.70 / lado (MCL)",
    tickSize: "0.01 ($1.00 / tick MCL)",
    rangoFechas: "2012 – 2026 (14 años)",
    sesion: "NYMEX RTH",
    estadoDataset: "VERIFICADO_SHA256",
  },
  {
    simbolo: "ZB",
    microsimbolo: "UB",
    nombre: "U.S. Treasury Bond (30A)",
    clase: "BONOS & DIVISAS",
    timeframes: ["15m", "1h", "4h"],
    comision: "$0.85 / lado",
    tickSize: "1/32 ($31.25 / tick)",
    rangoFechas: "2010 – 2026 (16 años)",
    sesion: "CBOT Financials",
    estadoDataset: "VERIFICADO_SHA256",
  },
  {
    simbolo: "6E",
    microsimbolo: "M6E",
    nombre: "Euro FX Futures",
    clase: "BONOS & DIVISAS",
    timeframes: ["5m", "15m", "1h"],
    comision: "$0.60 / lado (M6E)",
    tickSize: "0.0001 ($1.25 / tick M6E)",
    rangoFechas: "2012 – 2026 (14 años)",
    sesion: "24h FX Session",
    estadoDataset: "VERIFICADO_SHA256",
  },
];

const ACTIVOS_ULTRA_CRIPTO: ActivoConfig[] = [
  {
    simbolo: "BTCUSDT",
    microsimbolo: "BTC",
    nombre: "Bitcoin Perpetuals (BingX / Binance)",
    clase: "CRIPTO SWAP",
    timeframes: ["1m", "5m", "15m", "1h", "4h"],
    comision: "0.045% Taker · 0.020% Maker",
    tickSize: "0.1 USDT",
    rangoFechas: "2019 – 2026 (7 años)",
    sesion: "24/7/365 Continua",
    estadoDataset: "PENDIENTE_INGESTA",
  },
  {
    simbolo: "ETHUSDT",
    microsimbolo: "ETH",
    nombre: "Ethereum Perpetuals",
    clase: "CRIPTO SWAP",
    timeframes: ["1m", "5m", "15m", "1h", "4h"],
    comision: "0.045% Taker · 0.020% Maker",
    tickSize: "0.01 USDT",
    rangoFechas: "2019 – 2026 (7 años)",
    sesion: "24/7/365 Continua",
    estadoDataset: "PENDIENTE_INGESTA",
  },
  {
    simbolo: "SOLUSDT",
    microsimbolo: "SOL",
    nombre: "Solana Perpetuals",
    clase: "CRIPTO SWAP",
    timeframes: ["5m", "15m", "1h", "4h"],
    comision: "0.050% Taker",
    tickSize: "0.01 USDT",
    rangoFechas: "2021 – 2026 (5 años)",
    sesion: "24/7/365 Continua",
    estadoDataset: "PENDIENTE_INGESTA",
  },
  {
    simbolo: "SUIUSDT",
    microsimbolo: "SUI",
    nombre: "Sui Network Perpetuals",
    clase: "CRIPTO SWAP",
    timeframes: ["5m", "15m", "1h"],
    comision: "0.050% Taker",
    tickSize: "0.001 USDT",
    rangoFechas: "2023 – 2026 (3 años)",
    sesion: "24/7/365 Continua",
    estadoDataset: "PENDIENTE_INGESTA",
  },
  {
    simbolo: "LINKUSDT",
    microsimbolo: "LINK",
    nombre: "Chainlink Perpetuals",
    clase: "CRIPTO SWAP",
    timeframes: ["15m", "1h", "4h"],
    comision: "0.050% Taker",
    tickSize: "0.001 USDT",
    rangoFechas: "2020 – 2026 (6 años)",
    sesion: "24/7/365 Continua",
    estadoDataset: "PENDIENTE_INGESTA",
  },
];

/**
 * Herramientas y carpetas fijas que StrategyQuant X crea de fábrica en user/projects/.
 * No son proyectos de trading creados por Ultrarentable.
 * Fuente: instalación estándar de StrategyQuant X (verificada en Hetzner y Oracle).
 * Si un nombre no está en esta lista, se asume por defecto que es proyecto de usuario/nuestro (fail-open).
 */
const HERRAMIENTAS_SQX_FABRICA = new Set([
  "Builder",
  "Optimizer",
  "Retester",
  "PortfolioMaster",
  "PortfolioComposer",
  "backups",
]);

export default function PaginaGeneracion() {
  const [engineVersion, setEngineVersion] = useState<string | null>(null);
  const [sqxOnline, setSqxOnline] = useState<boolean | null>(null);
  const [sqxDetalle, setSqxDetalle] = useState("comprobando…");
  const [proyectos, setProyectos] = useState<string[]>([]);
  const [overview, setOverview] = useState<StrategyLabOverview | null>(null);
  const [extracciones, setExtracciones] = useState<StrategyLabRecord[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Submenú y filtros solicitados por Emilio
  const [activeTab, setActiveTab] = useState<SubmenuTab>("config_activos");
  const [trackFiltro, setTrackFiltro] = useState<TrackFiltro>("FONDEO");

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const [disc, ov, sqx, ext] = await Promise.all([
        getDiscoveryStatus().catch(() => null),
        getStrategyLabOverview().catch(() => null),
        getStrategyLabSQXStatus().catch(() => null),
        getStrategyLabStrategies(20).catch(() => null),
      ]);
      setEngineVersion(disc?.current_engine_version ?? null);
      setOverview(ov);
      setExtracciones(ext?.strategies ?? []);

      const resultado = sqx?.result as SqxResultado | undefined;
      const online = sqx?.status === "SUCCESS" && resultado?.status === "ONLINE";
      setSqxOnline(Boolean(online));
      setSqxDetalle(online ? (resultado?.base_url || "127.0.0.1:5050") : sqx?.error || "no conectado");
      setProyectos(Array.isArray(resultado?.projects) ? (resultado!.projects as string[]) : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al consultar la API.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const activosVigentes = trackFiltro === "FONDEO" ? ACTIVOS_FONDEO_CME : ACTIVOS_ULTRA_CRIPTO;

  const herramientasSqx = proyectos.filter((p) => HERRAMIENTAS_SQX_FABRICA.has(p));
  const proyectosNuestros = proyectos.filter((p) => !HERRAMIENTAS_SQX_FABRICA.has(p));

  return (
    <div className="w-full max-w-7xl mx-auto space-y-4 pb-20 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
                <span>M1: Generación de Estrategias (StrategyQuant X)</span>
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-3)]">
                  SQX (headless pendiente)
                </span>
              </h1>
              <p className="text-xs text-[var(--text-2)] font-mono">
                Especificación del universo de activos, temporalidades (1m–4h), monitorización de VPS (:5050) y fábrica de crudas.
              </p>
            </div>
          </div>

          <button
            onClick={() => void cargar()}
            disabled={cargando}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[var(--surface-2)] border border-[var(--border)] font-mono text-xs hover:bg-[var(--surface-3)] transition cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${cargando ? "animate-spin" : ""}`} />
            <span>Actualizar</span>
          </button>
        </div>
      </div>

      {/* Navegación Modular M1–M5 */}
      <NavBloques activo="generacion" />

      {/* KPI Strip del Laboratorio */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Estado Servidor SQX</span>
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                sqxOnline ? "bg-[var(--profit)] animate-ping" : "bg-[var(--loss)]"
              }`}
            />
            <span className={`text-base font-bold ${sqxOnline ? "text-[var(--profit)]" : "text-[var(--loss)]"}`}>
              {sqxOnline ? "ONLINE" : "DESCONECTADO"}
            </span>
          </div>
          <span className="text-[11px] text-[var(--text-3)] block truncate">{sqxDetalle}</span>
        </div>

        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Candidatas Estructura</span>
          <div className="text-xl font-bold text-[var(--text-1)]">
            {overview?.pipeline?.structurally_verified ?? 0}
          </div>
          <span className="text-[11px] text-[var(--text-3)] block">Estructuralmente verificadas</span>
        </div>

        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Extraídas a Mejora</span>
          <div className="text-xl font-bold text-[var(--profit)]">
            {overview?.pipeline?.extracted ?? 0}
          </div>
          <span className="text-[11px] text-[var(--text-3)] block">En cola de evaluación M2</span>
        </div>

        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Motor Vigente</span>
          <div className="text-xl font-bold text-[var(--text-1)] truncate">
            {engineVersion || "5.18.0"}
          </div>
          <span className="text-[11px] text-[var(--text-3)] block">Fricción MES $0.60/lado</span>
        </div>
      </div>

      {/* SUBMENÚS DE M1 (Mandato de Emilio: Preconfigurar activos, temporalidades, monitorizar SQX y crudas) */}
      <div className="flex flex-wrap items-center gap-1.5 border-b border-[var(--border)] pb-2 font-mono text-xs">
        <button
          onClick={() => setActiveTab("config_activos")}
          className={`px-3 py-1.5 rounded transition ${
            activeTab === "config_activos"
              ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
              : "text-[var(--text-2)] hover:bg-[var(--surface-2)] border border-transparent"
          }`}
        >
          <div className="flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-[var(--profit)]" />
            <span>1. Universo de Activos & Temporalidades</span>
          </div>
        </button>

        <button
          onClick={() => setActiveTab("monitor_sqx")}
          className={`px-3 py-1.5 rounded transition ${
            activeTab === "monitor_sqx"
              ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
              : "text-[var(--text-2)] hover:bg-[var(--surface-2)] border border-transparent"
          }`}
        >
          <div className="flex items-center gap-1.5">
            <Radio className="w-3.5 h-3.5 text-[var(--profit)]" />
            <span>2. Monitorización en Vivo SQX (:5050)</span>
          </div>
        </button>

        <button
          onClick={() => setActiveTab("crudas_extraidas")}
          className={`px-3 py-1.5 rounded transition ${
            activeTab === "crudas_extraidas"
              ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
              : "text-[var(--text-2)] hover:bg-[var(--surface-2)] border border-transparent"
          }`}
        >
          <div className="flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-[var(--text-2)]" />
            <span>3. Estrategias Crudas del Builder ({extracciones.length})</span>
          </div>
        </button>

        <button
          onClick={() => setActiveTab("tools_puente")}
          className={`px-3 py-1.5 rounded transition ${
            activeTab === "tools_puente"
              ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
              : "text-[var(--text-2)] hover:bg-[var(--surface-2)] border border-transparent"
          }`}
        >
          <div className="flex items-center gap-1.5">
            <Settings className="w-3.5 h-3.5 text-[var(--text-2)]" />
            <span>4. Puente Técnico SQX Tools</span>
          </div>
        </button>
      </div>

      {/* CONTENIDO TAB 1: CONFIGURACIÓN DE ACTIVOS Y TEMPORALIDADES */}
      {activeTab === "config_activos" && (
        <div className="space-y-4">
          {/* Selector de Ruta / Track */}
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border)] pb-3">
              <div>
                <h2 className="text-sm font-bold text-[var(--text-1)] flex items-center gap-2">
                  <span>Preconfiguración del Motor de Minería SQX</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                    REGLA #24
                  </span>
                </h2>
                <p className="text-xs text-[var(--text-3)] font-mono">
                  Especifica a StrategyQuant qué activos, temporalidades y costes modelar para evitar minería estéril.
                </p>
              </div>

              {/* Botones de Track */}
              <div className="flex items-center gap-1.5 font-mono text-xs">
                <button
                  onClick={() => setTrackFiltro("FONDEO")}
                  className={`px-3 py-1 rounded transition ${
                    trackFiltro === "FONDEO"
                      ? "bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)] font-bold"
                      : "bg-[var(--surface-2)] text-[var(--text-3)] border border-[var(--border)]"
                  }`}
                >
                  Ruta Fondeo (CME Futures)
                </button>
                <button
                  onClick={() => setTrackFiltro("ULTRA")}
                  className={`px-3 py-1 rounded transition ${
                    trackFiltro === "ULTRA"
                      ? "bg-[var(--surface-3)] text-[var(--text-1)] border border-[var(--border-strong)] font-bold"
                      : "bg-[var(--surface-2)] text-[var(--text-3)] border border-[var(--border)] opacity-70"
                  }`}
                >
                  Ruta Ultra (Cripto · En Construcción)
                </button>
              </div>
            </div>

            {trackFiltro === "ULTRA" && (
              <div className="p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded text-xs text-[var(--text-2)] font-mono flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[var(--text-3)]" />
                <span>
                  <strong>ESTADO ULTRA: EN CONSTRUCCIÓN.</strong> Los contratos cripto swap están pre-catalogados para cuando se reactive la infraestructura BingX / Cripto sin romper el flujo de Fondeo CME.
                </span>
              </div>
            )}

            {/* Tabla de Activos y Temporalidades */}
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs border-collapse">
                <thead>
                  <tr className="bg-[var(--surface-2)] border-b border-[var(--border)] text-[10.5px] text-[var(--text-3)] uppercase">
                    <th className="p-2.5">Activo & Micro</th>
                    <th className="p-2.5">Nombre Institucional</th>
                    <th className="p-2.5">Clase</th>
                    <th className="p-2.5">Temporalidades Admitidas</th>
                    <th className="p-2.5">Comisión Fija</th>
                    <th className="p-2.5">Tick Size</th>
                    <th className="p-2.5">Cobertura Histórica</th>
                    <th className="p-2.5">Dataset VPS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {activosVigentes.map((act) => (
                    <tr key={act.simbolo} className="hover:bg-[var(--surface-2)] transition">
                      <td className="p-2.5 font-bold text-[var(--text-1)]">
                        <span className="text-[var(--profit)]">{act.simbolo}</span>
                        {act.microsimbolo && (
                          <span className="text-[var(--text-3)] text-[11px] ml-1">({act.microsimbolo})</span>
                        )}
                      </td>
                      <td className="p-2.5 text-[var(--text-2)]">{act.nombre}</td>
                      <td className="p-2.5 text-[11px] text-[var(--text-3)]">{act.clase}</td>
                      <td className="p-2.5">
                        <div className="flex flex-wrap gap-1">
                          {act.timeframes.map((tf) => (
                            <span
                              key={tf}
                              className="px-1.5 py-0.2 rounded bg-[var(--surface-3)] text-[var(--text-1)] text-[10.5px] border border-[var(--border)]"
                            >
                              {tf}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="p-2.5 text-[var(--text-2)]">{act.comision}</td>
                      <td className="p-2.5 text-[var(--text-3)] text-[11px]">{act.tickSize}</td>
                      <td className="p-2.5 text-[var(--text-2)] text-[11px]">{act.rangoFechas}</td>
                      <td className="p-2.5">
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                            act.estadoDataset === "VERIFICADO_SHA256"
                              ? "bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)]"
                              : "bg-[var(--surface-3)] text-[var(--text-3)] border border-[var(--border)]"
                          }`}
                        >
                          {act.estadoDataset === "VERIFICADO_SHA256" ? "SHA-256 OK" : "PENDIENTE"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* CONTENIDO TAB 2: MONITORIZACIÓN EN VIVO SQX */}
      {activeTab === "monitor_sqx" && (
        <div className="space-y-4">
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2 font-sans">
              <h2 className="text-sm font-bold text-[var(--text-1)] flex items-center gap-2">
                <Radio className="w-4 h-4 text-[var(--profit)]" />
                <span>Telemetría en Vivo de StrategyQuant X VPS</span>
              </h2>
              <span className="text-[11px] font-mono text-[var(--text-3)]">Puerto API :5050</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-sans">
              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3 space-y-1">
                <span className="text-[10px] text-[var(--text-3)] uppercase block font-mono">Dirección del Servicio</span>
                <p className="text-sm font-bold text-[var(--text-1)] font-mono">{sqxDetalle}</p>
                <p className="text-[11px] text-[var(--text-3)]">
                  Dirección donde responde StrategyQuant. Hoy contesta la aplicación con ventana; el modo automático (headless) todavía no está disponible.
                </p>
              </div>

              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3 space-y-2">
                <span className="text-[10px] text-[var(--text-3)] uppercase block font-mono">
                  Proyectos que conoce StrategyQuant
                </span>

                {proyectos.length === 0 ? (
                  <p className="text-sm font-mono text-[var(--text-3)]">
                    StrategyQuant no ha devuelto ningún proyecto
                  </p>
                ) : (
                  <div className="space-y-1.5">
                    {proyectosNuestros.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5 items-center">
                        {proyectosNuestros.map((p) => {
                          const esUltra = p.toLowerCase().startsWith("ultra");
                          return (
                            <span
                              key={p}
                              className={`text-xs font-mono px-2 py-0.5 rounded border ${
                                esUltra
                                  ? "bg-[var(--surface-3)] text-[var(--text-3)] border-[var(--border)]"
                                  : "bg-[var(--surface-3)] text-[var(--text-1)] border-[var(--border-strong)]"
                              }`}
                            >
                              {p}
                              {esUltra && (
                                <span className="ml-1.5 text-[9.5px] text-[var(--text-3)] font-sans">
                                  (carril ULTRA, aparcado)
                                </span>
                              )}
                            </span>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="text-xs text-[var(--text-3)] italic">
                        Sin proyectos de usuario registrados
                      </p>
                    )}

                    {herramientasSqx.length > 0 && (
                      <div className="pt-1.5 border-t border-[var(--border)]/60 flex flex-wrap items-center gap-1.5 text-[11px] text-[var(--text-3)]">
                        <span className="text-[10px] uppercase font-mono tracking-wide text-[var(--text-3)]">
                          herramientas de StrategyQuant:
                        </span>
                        <span className="font-mono text-[10.5px]">
                          {herramientasSqx.join(", ")}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                <p className="text-[11px] text-[var(--text-3)] leading-tight">
                  Carpetas de proyecto que devuelve StrategyQuant. No indica cuáles están ejecutándose.
                </p>
              </div>

              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3 space-y-1">
                <span className="text-[10px] text-[var(--text-3)] uppercase block font-mono">Databanks de Salida</span>
                <p className="text-sm font-bold text-[var(--text-1)] font-mono">Results · ToImprove · Success</p>
                <p className="text-[11px] text-[var(--text-3)]">
                  2.035 candidatas crudas en espera de parsing y evaluación en M2.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CONTENIDO TAB 3: ESTRATEGIAS CRUDAS EXTRAÍDAS */}
      {activeTab === "crudas_extraidas" && (
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-2 font-sans">
            <h2 className="text-sm font-bold text-[var(--text-1)]">
              Últimas Candidatas Entregadas por el Builder
            </h2>
            <span className="text-[11px] text-[var(--text-3)] font-mono">
              {extracciones.length} registradas en SQLite
            </span>
          </div>

          {extracciones.length === 0 ? (
            <div className="p-6 text-center text-[var(--text-3)] font-mono">
              Sin extracciones recientes registradas en la base de datos de StrategyLab.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[var(--surface-2)] border-b border-[var(--border)] text-[10px] text-[var(--text-3)] uppercase">
                    <th className="p-2.5">ID Estrategia</th>
                    <th className="p-2.5">Activo</th>
                    <th className="p-2.5">Timeframe</th>
                    <th className="p-2.5">Versión</th>
                    <th className="p-2.5">Estado</th>
                    <th className="p-2.5">Destino</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {extracciones.map((ext) => (
                    <tr key={ext.strategy_id} className="hover:bg-[var(--surface-2)] transition">
                      <td className="p-2.5 font-bold text-[var(--text-1)]">{ext.strategy_id}</td>
                      <td className="p-2.5 text-[var(--text-2)]">{ext.symbol || "ES"}</td>
                      <td className="p-2.5 text-[var(--text-3)]">{ext.timeframe || "5m"}</td>
                      <td className="p-2.5 text-[var(--text-1)]">{ext.strategy_version || "v1"}</td>
                      <td className="p-2.5 text-[var(--profit)] font-bold">
                        {ext.validation_status}
                      </td>
                      <td className="p-2.5">
                        <Link
                          href="/estrategias/mejora"
                          className="text-[10px] px-2 py-0.5 rounded bg-[var(--surface-3)] text-[var(--profit)] border border-[var(--border)] hover:underline"
                        >
                          Enviar a M2 Mejora →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* CONTENIDO TAB 4: HERRAMIENTAS DEL PUENTE SQX */}
      {activeTab === "tools_puente" && (
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3">
          <h2 className="text-sm font-bold text-[var(--text-1)] font-sans">
            Panel de Control Técnico del Puente SQX (Operaciones en Lote)
          </h2>
          <SQXToolsPanel onExtraccion={cargar} />
        </div>
      )}
    </div>
  );
}
