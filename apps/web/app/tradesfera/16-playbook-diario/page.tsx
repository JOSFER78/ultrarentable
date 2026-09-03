"use client";

import React, { useState } from "react";
import {
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertTriangle,
  Flame,
  FileText,
  Award,
} from "lucide-react";

interface PlaybookStep {
  id: string;
  phase: "PRE" | "LIVE" | "POST";
  timeWindow: string;
  title: string;
  instruction: string;
}

const PLAYBOOK_STEPS: PlaybookStep[] = [
  // FASE 1
  {
    id: "pre_calendar",
    phase: "PRE",
    timeWindow: "14:30 - 14:45 CET",
    title: "Auditoría de Calendario Económico ForexFactory / Investing",
    instruction: "Comprobar noticias de alto impacto (rojas). Si hay CPI/PPI a las 14:30 o FOMC a las 20:00, marcar alerta de no operar 5 min antes ni después.",
  },
  {
    id: "pre_killswitch",
    phase: "PRE",
    timeWindow: "14:45 - 15:00 CET",
    title: "Activación del Kill Switch en Rithmic / Tradovate",
    instruction: "Fijar pérdida máxima diaria (DLL) en el broker. Si tu cuenta de 50K tiene $1,000 de DLL, programa el auto-bloqueo al alcanzar -$350 de flotante.",
  },
  {
    id: "pre_levels",
    phase: "PRE",
    timeWindow: "15:00 - 15:25 CET",
    title: "Marcado de Niveles Institucionales (FVG & Liquidez previa)",
    instruction: "Trazar en NinjaTrader 8 los máximos/mínimos de la sesión asiática y europea, y los Fair Value Gaps de 15m pendientes de rellenar.",
  },

  // FASE 2
  {
    id: "live_open",
    phase: "LIVE",
    timeWindow: "15:30 - 15:45 CET",
    title: "Filtro de Apertura (Cero Órdenes los primeros 10 min)",
    instruction: "Dejar que el mercado absorba el desbalance de la campana sin precipitarse. Esperar a que se defina el rango de apertura (Opening Range).",
  },
  {
    id: "live_judas",
    phase: "LIVE",
    timeWindow: "16:00 - 16:15 CET",
    title: "Vela de las 10:00 AM EST (Detección de Judas Swing)",
    instruction: "Buscar la falsa ruptura que barre liquidez externa. Si hay confirmación con FVG en 1m/2m, entrar con Stop Loss detrás del extremo.",
  },
  {
    id: "live_twoloss",
    phase: "LIVE",
    timeWindow: "15:30 - 17:30 CET",
    title: "Regla Inquebrantable de 2 Pérdidas Consecutivas",
    instruction: "Si se acumulan 2 pérdidas seguidas en la misma sesión, cerrar NinjaTrader y apagar el ordenador inmediatamente sin excepciones.",
  },

  // FASE 3
  {
    id: "post_journal",
    phase: "POST",
    timeWindow: "17:35 - 17:50 CET",
    title: "Registro Forense en Trading Journal",
    instruction: "Guardar captura de pantalla de cada ejecución, registrar ratio R/R obtenido, ticks recorridos y apego al plan de trading.",
  },
  {
    id: "post_disconnect",
    phase: "POST",
    timeWindow: "18:00 CET",
    title: "Desconexión Digital & Blindaje Mental",
    instruction: "Prohibido volver a mirar gráficos o canales de Telegram por la tarde. Mantener la mente fresca para la siguiente sesión.",
  },
];

export default function PlaybookDiarioPage() {
  const [completedSteps, setCompletedSteps] = useState<Record<string, boolean>>({});

  const toggleStep = (id: string) => {
    setCompletedSteps((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const totalSteps = PLAYBOOK_STEPS.length;
  const countCompleted = Object.values(completedSteps).filter(Boolean).length;
  const disciplineScorePct = Math.round((countCompleted / totalSteps) * 100);

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Playbook Operativo Diario & Checklist de Ejecución</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] font-mono">
                Módulo M16
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono mt-0.5">
              Protocolo en 3 fases (Pre-Mercado, Ejecución en Vivo, Post-Mercado) · Disciplina algorítmica de cumplimiento
            </p>
          </div>
        </div>
      </div>

      {/* Monitor de Disciplina */}
      <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 font-mono text-xs">
        <div>
          <span className="text-[10px] text-[var(--text-3)] uppercase block">Índice de Cumplimiento Diario</span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-[var(--profit)]">{disciplineScorePct}%</span>
            <span className="text-[11px] text-[var(--text-2)]">({countCompleted} de {totalSteps} pasos completados)</span>
          </div>
        </div>

        <div className="w-full sm:w-60 h-2.5 bg-[var(--surface-2)] rounded-full overflow-hidden border border-[var(--border)]">
          <div
            className="h-full bg-[var(--profit)] transition-all duration-300 rounded-full"
            style={{ width: `${disciplineScorePct}%` }}
          />
        </div>
      </div>

      {/* Lista de Fases del Playbook */}
      <div className="space-y-3 font-mono text-xs">
        {(["PRE", "LIVE", "POST"] as const).map((phase) => {
          const phaseTitle = {
            PRE: "FASE 1: PRE-MERCADO & AUDITORÍA DE RIESGO (14:30 - 15:25 CET)",
            LIVE: "FASE 2: EJECUCIÓN EN VIVO & HARD SCALPING (15:30 - 17:30 CET)",
            POST: "FASE 3: POST-MERCADO & DESCONEXIÓN OBLIGATORIA (17:35 - 18:00 CET)",
          }[phase];

          const stepsInPhase = PLAYBOOK_STEPS.filter((s) => s.phase === phase);

          return (
            <div key={phase} className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-3">
              <span className="font-bold text-[var(--text-1)] uppercase text-xs block border-b border-[var(--border)] pb-2">
                {phaseTitle}
              </span>

              <div className="space-y-2">
                {stepsInPhase.map((step) => (
                  <div
                    key={step.id}
                    onClick={() => toggleStep(step.id)}
                    className={`p-3 rounded-md border transition cursor-pointer flex items-start gap-3 ${
                      completedSteps[step.id]
                        ? "bg-[var(--surface-2)] border-[var(--border-strong)] text-[var(--text-1)]"
                        : "bg-[var(--surface-1)] border-[var(--border)] text-[var(--text-2)] hover:bg-[var(--surface-2)]"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={Boolean(completedSteps[step.id])}
                      onChange={() => {}}
                      className="mt-0.5 accent-[var(--profit)] cursor-pointer"
                    />
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-[var(--profit)] font-bold">{step.timeWindow}</span>
                        <span className="text-xs font-bold text-[var(--text-1)]">{step.title}</span>
                      </div>
                      <p className="text-[11px] text-[var(--text-2)] font-sans leading-relaxed">
                        {step.instruction}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
