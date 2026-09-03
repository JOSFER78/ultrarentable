"use client";

import React, { useState } from "react";
import {
  Zap,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Flame,
  Calculator,
  Info,
} from "lucide-react";

export default function HacksReglasRapidasPage() {
  const [profitTarget, setProfitTarget] = useState<number>(3000);
  const [consistencyRulePct, setConsistencyRulePct] = useState<number>(40); // 40% en MFFU / Apex

  // Cálculo de techo máximo de beneficio por día
  const maxDayProfitAllowed = profitTarget * (consistencyRulePct / 100);

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Hacks, Reglas Rápidas & Trampas Ocultas de Fondeo</span>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                MÓDULO M14
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono">
              Auditoría de letra pequeña, cálculo de regla de consistencia y hacks mecánicos de pase.
            </p>
          </div>
        </div>
      </div>

      {/* Calculadora de Regla de Consistencia */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-4">
        <div className="border-b border-[var(--border)] pb-2">
          <h2 className="text-sm font-bold text-[var(--text-1)]">
            Calculadora de Techo Diario de Beneficio (Regla de Consistencia)
          </h2>
          <p className="text-xs text-[var(--text-3)] font-mono">
            Evita que un día excesivamente bueno bloquee tu cuenta por exceder el porcentaje máximo permitido.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3 font-mono text-xs">
            <div>
              <label className="text-[var(--text-2)] block mb-1">Target Total de Beneficio ($):</label>
              <input
                type="number"
                value={profitTarget}
                onChange={(e) => setProfitTarget(Number(e.target.value) || 0)}
                className="w-full bg-[var(--surface-2)] border border-[var(--border)] rounded px-3 py-1.5 text-[var(--text-1)]"
              />
            </div>

            <div>
              <label className="text-[var(--text-2)] block mb-1">
                Porcentaje de Consistencia Máximo ({consistencyRulePct}%):
              </label>
              <div className="flex gap-2">
                {[30, 40, 50].map((pct) => (
                  <button
                    key={pct}
                    onClick={() => setConsistencyRulePct(pct)}
                    className={`flex-1 py-1 rounded border transition cursor-pointer ${
                      consistencyRulePct === pct
                        ? "bg-[var(--surface-3)] border-[var(--profit)] text-[var(--profit)] font-bold"
                        : "bg-[var(--surface-2)] border-[var(--border)] text-[var(--text-3)]"
                    }`}
                  >
                    {pct}% ({pct === 40 ? "MFFU/Apex" : pct === 50 ? "Topstep" : "Otros"})
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded-lg p-4 space-y-2 font-mono flex flex-col justify-center">
            <span className="text-[10px] text-[var(--text-3)] uppercase">
              Máximo Beneficio Permitido en un Solo Día
            </span>
            <div className="text-2xl font-bold text-[var(--profit)]">
              ${maxDayProfitAllowed.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD
            </div>
            <p className="text-[11px] text-[var(--text-2)] font-sans">
              ⚠️ Si ganas más de este importe en una sola jornada, estarás obligado a seguir operando días adicionales para elevar el denominador total y reducir el peso de ese día por debajo del {consistencyRulePct}%.
            </p>
          </div>
        </div>
      </div>

      {/* 4 Hacks Operativos Comprobados */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-[var(--text-1)]">
            <Clock className="w-4 h-4 text-[var(--profit)]" />
            <span>El Hack de los Días Mínimos de Trading</span>
          </div>
          <p className="text-xs text-[var(--text-3)]">
            Si ya alcanzaste el profit target en 2 días pero la prop firm exige 5 días mínimos, abre 1 micro contrato (1 MNQ) en horario de bajo spread y ciérralo tras 5 segundos con +1 o -1 tick. Cuenta como día hábil sin arriesgar el pase.
          </p>
        </div>

        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-[var(--text-1)]">
            <AlertTriangle className="w-4 h-4 text-[var(--loss)]" />
            <span>Trampa del Cierre de Sesión CME (16:59 EST)</span>
          </div>
          <p className="text-xs text-[var(--text-3)]">
            El mercado de futuros cierra a las 17:00 EST para el mantenimiento diario. Si dejas una posición abierta a las 16:59:01 EST, el sistema de la prop firm la liquidará a mercado y te aplicará un hard breach instantáneo. Cierra siempre a las 16:50 EST.
          </p>
        </div>

        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-[var(--text-1)]">
            <Flame className="w-4 h-4 text-[var(--profit)]" />
            <span>Escalado de Contratos Inverso</span>
          </div>
          <p className="text-xs text-[var(--text-3)]">
            Nunca comiences un examen usando el máximo de contratos permitidos (ej. 5 Minis). Empieza con 2 Micros. Solo cuando acumules $1,000 de colchón sobre el trailing drawdown puedes considerar escalar a 1 Mini.
          </p>
        </div>

        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-[var(--text-1)]">
            <ShieldCheck className="w-4 h-4 text-[var(--profit)]" />
            <span>Desconexión en Noticias de Nivel 3 (FOMC/NFP)</span>
          </div>
          <p className="text-xs text-[var(--text-3)]">
            Aunque la empresa "permita noticias", el spread de los contratos E-mini se amplía de 0.25 a 8 puntos en 2 milisegundos durante el dato. Tu stop loss será saltado con slippage monstruoso. No operes 5 min antes ni 5 min después.
          </p>
        </div>
      </div>
    </div>
  );
}
