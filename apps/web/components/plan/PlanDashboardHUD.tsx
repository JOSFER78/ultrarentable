"use client";

import React from "react";
import {
  Cpu,
  Server,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Flame,
  ShieldCheck,
  RefreshCw,
  Clock,
} from "lucide-react";
import type { HudStatus } from "@/app/api/plan/route";

interface PlanDashboardHUDProps {
  hud: HudStatus;
  generatedAt?: string;
  autoRefresh: boolean;
  onToggleAutoRefresh: () => void;
  onRefresh: () => void;
  loading: boolean;
}

export default function PlanDashboardHUD({
  hud,
  generatedAt,
  autoRefresh,
  onToggleAutoRefresh,
  onRefresh,
  loading,
}: PlanDashboardHUDProps) {
  const syncTime = generatedAt
    ? new Date(generatedAt).toLocaleTimeString("es-ES")
    : null;

  return (
    <div className="space-y-3 font-mono text-xs">
      {/* 1. Barra Superior con Identidad y Controles */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="p-1.5 rounded-md bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
              <Cpu className="w-4 h-4" />
            </span>
            <h1 className="text-base sm:text-lg font-bold text-[var(--text-1)] tracking-tight">
              Centro de Control & Plan Maestro del Proyecto
            </h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-[var(--surface-2)] border border-[var(--border-strong)] text-[var(--profit)] font-bold">
              MOTOR {hud.motor_version}
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)]">
              CME FUTUROS
            </span>
          </div>
          <p className="text-[11px] text-[var(--text-3)] font-sans">
            Gobernanza centralizada de la fábrica de trading: orquestación de agentes, minería en VPS y seguimiento documental.
          </p>
        </div>

        {/* Controles en Vivo */}
        <div className="flex items-center gap-2.5 shrink-0">
          {syncTime && (
            <span className="text-[11px] text-[var(--text-3)] hidden sm:inline">
              Sincronizado {syncTime}
            </span>
          )}
          <button
            onClick={onToggleAutoRefresh}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border text-[11px] font-semibold transition cursor-pointer ${
              autoRefresh
                ? "bg-[var(--profit-dim)] border-[var(--profit)] text-[var(--profit)]"
                : "bg-[var(--surface-2)] border-[var(--border)] text-[var(--text-3)] hover:text-[var(--text-2)]"
            }`}
            title="Auto-refrescar cada 30 segundos mientras los agentes trabajan"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                autoRefresh ? "bg-[var(--profit)] animate-pulse" : "bg-[var(--text-3)]"
              }`}
            />
            <span>En vivo {autoRefresh ? "30s" : "Off"}</span>
          </button>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[var(--border)] bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-[11px] text-[var(--text-1)] font-semibold transition cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refrescar</span>
          </button>
        </div>
      </div>

      {/* 2. Grid de Telemetría Operativa en Tiempo Real */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
        {/* Tarjeta 1: Fondeo Certificadas */}
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[10px] text-[var(--text-3)] uppercase font-semibold">
            <span>Estrategias Fondeo</span>
            <ShieldCheck className="w-3.5 h-3.5 text-[var(--profit)]" />
          </div>
          <div className="my-1.5">
            <span className="text-xl font-bold text-[var(--text-1)]">
              {hud.certificadas_fondeo}
            </span>
            <span className="text-[11px] text-[var(--text-3)] ml-1.5">certificadas</span>
          </div>
          <div className="text-[10px] text-[var(--text-3)] truncate" title={hud.criterio_sellado}>
            {hud.criterio_sellado}
          </div>
        </div>

        {/* Tarjeta 2: Meta-Estrategias */}
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[10px] text-[var(--text-3)] uppercase font-semibold">
            <span>Meta-Estrategias</span>
            <Cpu className="w-3.5 h-3.5 text-[var(--text-2)]" />
          </div>
          <div className="my-1.5">
            <span className="text-xl font-bold text-[var(--text-1)]">
              {hud.meta_estrategias}
            </span>
            <span className="text-[11px] text-[var(--text-3)] ml-1.5">ensambladas</span>
          </div>
          <div className="text-[10px] text-[var(--text-3)]">
            Requiere ≥2 válidas certificadas
          </div>
        </div>

        {/* Tarjeta 3: Campaña de Minería Activa */}
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[10px] text-[var(--text-3)] uppercase font-semibold">
            <span>Campaña Minería</span>
            <Flame className="w-3.5 h-3.5 text-[var(--profit)]" />
          </div>
          <div className="my-1.5">
            <span className="text-sm font-bold text-[var(--text-1)] block truncate">
              {hud.campana_activa}
            </span>
          </div>
          <div className="text-[10px] text-[var(--profit)] truncate" title={hud.campana_estado}>
            {hud.campana_estado}
          </div>
        </div>

        {/* Tarjeta 4: Carril ULTRA */}
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[10px] text-[var(--text-3)] uppercase font-semibold">
            <span>Carril ULTRA</span>
            <Lock className="w-3.5 h-3.5 text-[var(--text-3)]" />
          </div>
          <div className="my-1.5">
            <span className="text-xs font-bold text-[var(--text-2)] uppercase flex items-center gap-1">
              APARCADO / CONGELADO
            </span>
          </div>
          <div className="text-[10px] text-[var(--text-3)]">
            Envolvente de balas (F05/F06)
          </div>
        </div>
      </div>

      {/* 3. Panel Visual de Alertas & Últimos Hallazgos */}
      <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded-lg p-3 sm:p-3.5 space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border)] pb-2">
          <div className="flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-[var(--profit)] shrink-0" />
            <span className="text-[10px] uppercase font-bold text-[var(--text-2)] tracking-wider whitespace-nowrap">
              Último Hallazgo Auditado (Telemetría E2)
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            {hud.alertas_activas.map((alerta, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-[var(--surface-1)] border border-[var(--border)] text-[var(--text-2)] whitespace-nowrap"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--profit)]" />
                <span>{alerta}</span>
              </span>
            ))}
          </div>
        </div>
        <p className="text-[11px] text-[var(--text-1)] font-sans leading-relaxed">
          {hud.ultimo_hallazgo}
        </p>
      </div>
    </div>
  );
}
