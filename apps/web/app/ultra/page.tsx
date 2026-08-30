"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Zap,
  ShieldCheck,
  TrendingUp,
  Flame,
  ArrowRight,
  Layers,
  Sparkles,
  Calculator,
  Activity,
  CheckCircle2,
  Lock,
  ChevronRight,
} from "lucide-react";

export default function UltraPage() {
  const [bulletSize, setBulletSize] = useState<number>(500);
  const [targetRMultiple, setTargetRMultiple] = useState<number>(10);
  const [pyramidLayers, setPyramidLayers] = useState<number>(2);

  // Convex calculations
  // Max loss is strictly 1R (bulletSize)
  const maxRiskUsd = bulletSize;
  // With 40% House Money pyramiding on 2 layers:
  // Layer 1: at +1.5R adds 0.4R risk from profit
  // Layer 2: at +3.0R adds 0.4R risk from profit
  const baseRewardUsd = bulletSize * targetRMultiple;
  const pyramidedBonusMultiplier = pyramidLayers === 0 ? 1.0 : pyramidLayers === 1 ? 1.4 : 1.96;
  const grossConvexRewardUsd = baseRewardUsd * pyramidedBonusMultiplier;
  const netAsymmetricGainUsd = grossConvexRewardUsd;
  const convexAsymmetryRatio = (grossConvexRewardUsd / maxRiskUsd).toFixed(1);

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6 pb-24 text-slate-100">
      {/* 1. TOP HEADER */}
      <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 md:p-8 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 mb-1">
              <Link href="/" className="text-xs text-slate-400 hover:text-white transition">
                ← Command Center
              </Link>
              <span className="text-slate-600">/</span>
              <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">
                DOCTRINA ULTRA · EXPLOTACIÓN ASIMÉTRICA CONVEXA
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
              Mecanismo de Explotación Ultra & Bóveda Ratchet
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-3xl leading-relaxed">
              Arquitectura de trading en margen aislado (1R). Piramidación al 40% financiada exclusivamente con ganancias flotantes (House Money) y garantía matemática de protección Free-Risk.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 text-right">
              <span className="text-[10px] text-slate-500 font-mono block uppercase">Estado del Motor</span>
              <span className="text-xs font-mono font-black text-slate-400">
                0 BOTS ACTIVOS (EN REPOSO)
              </span>
            </div>
            <Link
              href="/bifurcacion"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-mono font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition shadow-lg shadow-emerald-500/20"
            >
              <Zap className="w-4 h-4" />
              <span>Bifurcación QVF</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 2. CICLO DE VIDA DE 6 ESTADOS (FSM FINITE STATE MACHINE) */}
      <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 shadow-xl space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-base font-black text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            <span>Ciclo de Vida de la Bala de Margen Aislado (FSM 6 Estados)</span>
          </h3>
          <span className="text-xs font-mono text-slate-400">Garantía Zero-Risk Post +1R</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          <div className="bg-slate-950/80 border border-emerald-500/30 rounded-xl p-4 space-y-2 hover:border-emerald-500/60 transition">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-xs font-black font-mono">
                1
              </span>
              <span className="text-xs font-bold text-emerald-300">INICIO (1R)</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-snug">
              Disparo con margen aislado: riesgo máximo acotado estrictamente a 1R.
            </p>
          </div>

          <div className="bg-slate-950/80 border border-sky-500/30 rounded-xl p-4 space-y-2 hover:border-sky-500/60 transition">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-sky-500/10 text-sky-400 flex items-center justify-center text-xs font-black font-mono">
                2
              </span>
              <span className="text-xs font-bold text-sky-300">CONFIRMACIÓN</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-snug">
              Al alcanzar +1.0R flotante, Stop Loss se traslada de inmediato a Break-Even ($0 riesgo).
            </p>
          </div>

          <div className="bg-slate-950/80 border border-purple-500/30 rounded-xl p-4 space-y-2 hover:border-purple-500/60 transition">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center text-xs font-black font-mono">
                3
              </span>
              <span className="text-xs font-bold text-purple-300">CRECIMIENTO</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-snug">
              Piramidación del 40% financiada con House Money asegurando profit residual ≥ +0.5R.
            </p>
          </div>

          <div className="bg-slate-950/80 border border-emerald-500/30 rounded-xl p-4 space-y-2 hover:border-emerald-500/60 transition">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-xs font-black font-mono">
                4
              </span>
              <span className="text-xs font-bold text-emerald-300">COSECHA RATCHET</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-snug">
              Hitos 2x, 3x, 5x, 10x donde el 50% de ganancia se bloquea físicamente en Bóveda.
            </p>
          </div>

          <div className="bg-slate-950/80 border border-amber-500/30 rounded-xl p-4 space-y-2 hover:border-amber-500/60 transition">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center text-xs font-black font-mono">
                5
              </span>
              <span className="text-xs font-bold text-amber-300">PROTECCIÓN BE</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-snug">
              Trailing stop dinámico por Chandelier Exit para exprimir colas estadísticas extremas.
            </p>
          </div>

          <div className="bg-slate-950/80 border border-rose-500/30 rounded-xl p-4 space-y-2 hover:border-rose-500/60 transition">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center text-xs font-black font-mono">
                6
              </span>
              <span className="text-xs font-bold text-rose-300">CIERRE</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-snug">
              Liquidación ordenada y liberación de slot para el siguiente disparo del radar.
            </p>
          </div>
        </div>
      </div>

      {/* 3. ASYMMETRIC CONVEX SIMULATOR */}
      <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 md:p-8 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Calculator className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-black text-white tracking-tight">
                Simulador de Asimetría Convexa & Retorno R-Múltiple
              </h2>
              <p className="text-xs text-slate-400">
                Calcula la convexidad matemática de arriesgar 1R con piramidación House Money en trades de cola.
              </p>
            </div>
          </div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-bold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Convexidad: {convexAsymmetryRatio} : 1</span>
          </div>
        </div>

        {/* Sliders */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="flex justify-between items-center text-[11px] font-mono font-bold text-slate-400 uppercase">
              <span>Tamaño de Bala (1R):</span>
              <span className="text-emerald-400 font-bold">${bulletSize} USD</span>
            </div>
            <input
              type="range"
              min={100}
              max={2000}
              step={50}
              value={bulletSize}
              onChange={(e) => setBulletSize(Number(e.target.value))}
              className="w-full accent-emerald-400 cursor-pointer"
            />
            <span className="text-[10px] text-slate-500 block font-mono">Pérdida máxima acotada en caso de fallo</span>
          </div>

          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="flex justify-between items-center text-[11px] font-mono font-bold text-slate-400 uppercase">
              <span>Objetivo de Cola (R):</span>
              <span className="text-sky-400 font-bold">{targetRMultiple}R</span>
            </div>
            <input
              type="range"
              min={3}
              max={30}
              step={1}
              value={targetRMultiple}
              onChange={(e) => setTargetRMultiple(Number(e.target.value))}
              className="w-full accent-sky-400 cursor-pointer"
            />
            <span className="text-[10px] text-slate-500 block font-mono">Múltiplo de expansión de tendencia</span>
          </div>

          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="flex justify-between items-center text-[11px] font-mono font-bold text-slate-400 uppercase">
              <span>Capas de Piramidación HM:</span>
              <span className="text-purple-400 font-bold">{pyramidLayers} {pyramidLayers === 1 ? "capa" : "capas"}</span>
            </div>
            <input
              type="range"
              min={0}
              max={2}
              step={1}
              value={pyramidLayers}
              onChange={(e) => setPyramidLayers(Number(e.target.value))}
              className="w-full accent-purple-400 cursor-pointer"
            />
            <span className="text-[10px] text-slate-500 block font-mono">Piramidación financiada con flotante</span>
          </div>
        </div>

        {/* Results Bar */}
        <div className="bg-slate-950/90 border border-slate-800 rounded-2xl p-5 grid grid-cols-2 md:grid-cols-4 gap-4 font-mono">
          <div>
            <span className="text-[10px] text-slate-500 uppercase block">Riesgo Máx. Absoluto (1R)</span>
            <div className="text-2xl font-black text-rose-400 tabular-nums">
              -${maxRiskUsd.toLocaleString()} USD
            </div>
            <span className="text-[10px] text-slate-500 block">Margen Aislado Fijo</span>
          </div>

          <div>
            <span className="text-[10px] text-slate-500 uppercase block">Retorno Bruto Estimado</span>
            <div className="text-2xl font-black text-emerald-400 tabular-nums">
              +${grossConvexRewardUsd.toLocaleString("en-US", { maximumFractionDigits: 0 })} USD
            </div>
            <span className="text-[10px] text-slate-500 block">Con Piramidación HM</span>
          </div>

          <div>
            <span className="text-[10px] text-slate-500 uppercase block">Cosecha Bóveda (50%)</span>
            <div className="text-2xl font-black text-amber-400 tabular-nums">
              ${(grossConvexRewardUsd * 0.5).toLocaleString("en-US", { maximumFractionDigits: 0 })} USD
            </div>
            <span className="text-[10px] text-slate-500 block">Intocable Monotónico</span>
          </div>

          <div>
            <span className="text-[10px] text-slate-500 uppercase block">Ratio Asimetría PnL</span>
            <div className="text-2xl font-black text-sky-400 tabular-nums">
              {convexAsymmetryRatio}x
            </div>
            <span className="text-[10px] text-slate-500 block">Retorno por cada $1 arriesgado</span>
          </div>
        </div>
      </div>

      {/* 4. ESPECIFICACIÓN CANÓNICA: RUTA ULTRA VS RUTA FONDEO */}
      <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h4 className="text-sm font-black text-white font-mono uppercase tracking-wider flex items-center gap-2">
            <Zap className="w-4 h-4 text-emerald-400" />
            <span>Matriz Canónica: Ruta ULTRA (BingX Sub-Cuenta) vs Ruta FONDEO (CME Prop Firms)</span>
          </h4>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] text-slate-400 uppercase font-bold tracking-wider">
                <th className="py-3 px-3">Parámetro</th>
                <th className="py-3 px-3 text-emerald-400">Ruta ULTRA (Asimétrica)</th>
                <th className="py-3 px-3 text-sky-400">Ruta FONDEO (Prop Firms)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              <tr className="hover:bg-slate-900/40">
                <td className="py-3 px-3 font-bold text-white">Capital Base Inicial</td>
                <td className="py-3 px-3 text-emerald-400">$1.000 USD (Bala Sacrificable)</td>
                <td className="py-3 px-3 text-sky-400">$50.000 USD (Cuenta Institucional)</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-3 px-3 font-bold text-white">Riesgo Base por Trade</td>
                <td className="py-3 px-3 text-emerald-400">7.5% de Equidad Disponible</td>
                <td className="py-3 px-3 text-sky-400">0.5% - 1.0% ($250 - $500 USD)</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-3 px-3 font-bold text-white">Interés Compuesto</td>
                <td className="py-3 px-3 text-emerald-400">Compounding Dinámico Activo</td>
                <td className="py-3 px-3 text-sky-400">Contratos Fijos Micro/E-mini CME</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-3 px-3 font-bold text-white">Piramidación</td>
                <td className="py-3 px-3 text-emerald-400">1 a 3 niveles en flotante ≥ +1.5R</td>
                <td className="py-3 px-3 text-rose-400 font-bold">Prohibida (Exposición fija)</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-3 px-3 font-bold text-white">Drawdown Permitido</td>
                <td className="py-3 px-3 text-emerald-400">Hasta 80% (Quiebra de bala en 85-100%)</td>
                <td className="py-3 px-3 text-rose-400 font-bold">Máximo 4.0% - 4.5% ($2.000 - $2.500 USD)</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-3 px-3 font-bold text-white">Cosecha a Bóveda</td>
                <td className="py-3 px-3 text-emerald-400">50% cosechado al superar +200%</td>
                <td className="py-3 px-3 text-slate-400">Retiros gestionados por Prop Firm</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-3 px-3 font-bold text-white">Universo de Activos</td>
                <td className="py-3 px-3 text-emerald-400">23 Activos Globales (BTC, ETH, SOL, SUI, DOGE, AVAX, BNB, NQ, ES, GC, etc.)</td>
                <td className="py-3 px-3 text-sky-400">Futuros CME (NQ, ES, YM, GC, CL, 6E)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. CALL TO ACTION FOOTER */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-6 text-center space-y-3">
        <p className="text-xs text-slate-400">
          Para activar este motor en vivo, selecciona una cartera validada con Gate 11 en el Command Center o en la Bifurcación QVF.
        </p>
        <div className="flex justify-center gap-3">
          <Link
            href="/bifurcacion"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition shadow-lg shadow-emerald-500/20"
          >
            <span>Evaluar en Bifurcación QVF</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <Link
            href="/prop-firms"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-bold bg-slate-900 hover:bg-slate-800 text-white border border-slate-700 transition"
          >
            <span>Ver 70 Prop Firms CME</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
