"use client";

import React, { useState } from "react";
import {
  Brain,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Activity,
  Award,
  Clock,
  Zap,
} from "lucide-react";

interface BiasItem {
  id: string;
  name: string;
  danger: string;
  trigger: string;
  antidote: string;
}

const PSYCHOLOGICAL_BIASES: BiasItem[] = [
  {
    id: "FOMO",
    name: "FOMO (Miedo a Perderse el Movimiento)",
    danger: "Entrar tarde en velas de ruptura ya extendidas, aumentando el stop loss y destruyendo el R:R.",
    trigger: "Ver velas verdes gigantes en NQ o leer capturas de ganancias en Telegram.",
    antidote: "Regla del pullback obligatorio: Si el precio no vuelve al nivel de gatillo, el trade no existe.",
  },
  {
    id: "REVENGE",
    name: "Revenge Trading (Operar por Venganza)",
    danger: "Duplicar lotaje tras una pérdida para 'recuperar rápido', quemando la cuenta en 15 minutos.",
    trigger: "Stop loss tocado por 1 tick antes de que el precio vaya a target.",
    antidote: "Kill-Switch automático tras 2 pérdidas consecutivas en la misma sesión. Desconexión forzosa 3 horas.",
  },
  {
    id: "SUNK_COST",
    name: "Falacia del Coste Hundido",
    danger: "Mantener una posición perdedora moviendo el stop porque 'ya voy perdiendo $500 y tiene que rebotar'.",
    trigger: "Apego al capital ya arriesgado en la operación.",
    antidote: "El mercado no sabe cuánto vas perdiendo. Tratar cada tick como una nueva decisión independiente.",
  },
  {
    id: "OVERCONFIDENCE",
    name: "Efecto Dios (Exceso de Confianza)",
    danger: "Aumentar bruscamente contratos tras una racha ganadora, entregando el 100% de beneficios.",
    trigger: "3 o 4 días seguidos en positivo pasando evaluaciones con facilidad.",
    antidote: "Regla de perfil bajo: Mantener el tamaño de posición idéntico sin importar la racha ganadora.",
  },
];

export default function PsicologiaFondeoPage() {
  const [selectedBias, setSelectedBias] = useState<string>("FOMO");
  const [protocolChecks, setProtocolChecks] = useState<Record<string, boolean>>({
    sleep: false,
    noNews: false,
    killSwitchReady: false,
    targetSet: false,
    journalOpen: false,
  });

  const toggleCheck = (id: string) => {
    setProtocolChecks((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const activeBias = PSYCHOLOGICAL_BIASES.find((b) => b.id === selectedBias) || PSYCHOLOGICAL_BIASES[0];

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Psicología del Fondeo & Sesgos Operativos</span>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                MÓDULO M07
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono">
              Tratado conductual de Víctor Corrales (@Elpsicologodeltrading) & Gerard García para cuentas de fondeo CME.
            </p>
          </div>
        </div>
      </div>

      {/* Grid de 4 Pilares del Psicotrading */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono text-[var(--text-3)] uppercase font-semibold">
            <span>Regla de Oro</span>
            <ShieldCheck className="w-3.5 h-3.5 text-[var(--profit)]" />
          </div>
          <div className="text-sm font-bold text-[var(--text-1)]">Preservar el Cortisol</div>
          <p className="text-[11px] text-[var(--text-3)]">
            Operar con estrés biológico reduce un 40% la agudeza visual del gráfico.
          </p>
        </div>

        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono text-[var(--text-3)] uppercase font-semibold">
            <span>Límite de Sesión</span>
            <Flame className="w-3.5 h-3.5 text-[var(--loss)]" />
          </div>
          <div className="text-sm font-bold text-[var(--text-1)]">Máx. 2 Stops / Día</div>
          <p className="text-[11px] text-[var(--text-3)]">
            El 92% de las cuentas quemadas ocurren tras el tercer trade impulsivo.
          </p>
        </div>

        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono text-[var(--text-3)] uppercase font-semibold">
            <span>Micro Lotes</span>
            <Zap className="w-3.5 h-3.5 text-[var(--profit)]" />
          </div>
          <div className="text-sm font-bold text-[var(--text-1)]">Micro-Contratos (MNQ/MES)</div>
          <p className="text-[11px] text-[var(--text-3)]">
            El tamaño en micros disuelve el dolor emocional de la pérdida.
          </p>
        </div>

        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono text-[var(--text-3)] uppercase font-semibold">
            <span>Mentalidad</span>
            <Award className="w-3.5 h-3.5 text-[var(--text-2)]" />
          </div>
          <div className="text-sm font-bold text-[var(--text-1)]">Extracción Silenciosa</div>
          <p className="text-[11px] text-[var(--text-3)]">
            Cero capturas en redes. Operar en perfil bajo garantiza disciplina a largo plazo.
          </p>
        </div>
      </div>

      {/* Matriz de Sesgos Cognitivos & Antídotos */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border)] pb-3">
          <div>
            <h2 className="text-sm font-bold text-[var(--text-1)]">
              Matriz Forense de Sesgos Cognitivos en Prop Trading
            </h2>
            <p className="text-xs text-[var(--text-3)] font-mono">
              Selecciona un sesgo para inspeccionar su detonante y el antídoto mecánico del protocolo.
            </p>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[var(--surface-2)] text-[var(--profit)] border border-[var(--border)]">
            Protocolo Clínico V2
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
          {PSYCHOLOGICAL_BIASES.map((b) => (
            <button
              key={b.id}
              onClick={() => setSelectedBias(b.id)}
              className={`p-3 rounded-lg border text-left transition cursor-pointer flex flex-col justify-between ${
                selectedBias === b.id
                  ? "bg-[var(--surface-2)] border-[var(--profit)] shadow-md"
                  : "bg-[var(--surface-1)] border-[var(--border)] hover:bg-[var(--surface-2)]"
              }`}
            >
              <span className="text-xs font-bold text-[var(--text-1)]">{b.id}</span>
              <span className="text-[11px] text-[var(--text-3)] truncate mt-1">{b.name}</span>
            </button>
          ))}
        </div>

        {/* Detalle del Sesgo Seleccionado */}
        <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded-lg p-4 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between">
            <span className="text-sm font-bold text-[var(--text-1)] font-sans">{activeBias.name}</span>
            <span className="text-[10px] text-[var(--loss)] uppercase font-bold">Riesgo Crítico</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-sans">
            <div className="space-y-1">
              <span className="text-[10px] font-mono uppercase text-[var(--text-3)]">Peligro Operativo</span>
              <p className="text-xs text-[var(--text-2)]">{activeBias.danger}</p>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] font-mono uppercase text-[var(--text-3)]">Detonante Mental</span>
              <p className="text-xs text-[var(--text-2)]">{activeBias.trigger}</p>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] font-mono uppercase text-[var(--profit)] font-bold">Antídoto Mecánico</span>
              <p className="text-xs text-[var(--text-1)] font-semibold">{activeBias.antidote}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Checklist Pre-Mercado de Regulación Emocional */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-3 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
          <span className="text-xs font-bold text-[var(--text-1)] uppercase">
            Checklist Pre-Mercado del Psicólogo del Trading (Víctor Corrales)
          </span>
          <span className="text-[11px] text-[var(--profit)]">
            {Object.values(protocolChecks).filter(Boolean).length}/5 Verificaciones
          </span>
        </div>

        <div className="space-y-2 font-sans text-xs">
          {[
            { id: "sleep", label: "Descanso óptimo: Al menos 7 horas de sueño y nivel de energía mental > 7/10." },
            { id: "noNews", label: "Calendario económico auditado: Sin noticias de alto impacto (FOMC/CPI/NFP) en la ventana." },
            { id: "killSwitchReady", label: "Kill-Switch configurado: Límite diario de pérdida activo en NinjaTrader / Rithmic." },
            { id: "targetSet", label: "Objetivo de cosecha claro: Máximo 1 o 2 trades con ratio ≥ 1:1.5; no sobreoperar." },
            { id: "journalOpen", label: "Bitácora operativa abierta: Registro de emoción previa antes del primer clic." },
          ].map((item) => (
            <label
              key={item.id}
              onClick={() => toggleCheck(item.id)}
              className="flex items-center gap-2.5 p-2 rounded-md bg-[var(--surface-2)] border border-[var(--border)] cursor-pointer hover:bg-[var(--surface-3)] transition"
            >
              <input
                type="checkbox"
                checked={Boolean(protocolChecks[item.id])}
                onChange={() => {}}
                className="rounded border-[var(--border)] text-[var(--profit)] focus:ring-0"
              />
              <span className={protocolChecks[item.id] ? "text-[var(--text-1)] font-semibold" : "text-[var(--text-3)]"}>
                {item.label}
              </span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
