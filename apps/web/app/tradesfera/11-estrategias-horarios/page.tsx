"use client";

import React, { useState, useEffect } from "react";
import {
  Clock,
  Zap,
  TrendingUp,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  Layers,
  ArrowRight,
} from "lucide-react";

interface Killzone {
  name: string;
  timeEst: string;
  timeMadrid: string;
  importance: "ALTA" | "CRÍTICA" | "MEDIA" | "PRECAUCIÓN";
  description: string;
  tactics: string[];
}

const KILLZONES: Killzone[] = [
  {
    name: "Pre-Mercado NY & Noticias Macro",
    timeEst: "08:30 - 09:30 EST",
    timeMadrid: "14:30 - 15:30 Madrid",
    importance: "PRECAUCIÓN",
    description: "Publicación de datos macroeconómicos de alta volatilidad (CPI, PPI, NFP, Jobless Claims a las 08:30 EST).",
    tactics: [
      "NO abrir posiciones 2 minutos antes ni después de noticias de alto impacto.",
      "Identificar los extremos del rango nocturno (Asia/Londres).",
      "Marcar los Fair Value Gaps (FVG) no mitigados en temporalidades de 15m y 1h.",
    ],
  },
  {
    name: "Apertura Cash Open (NYSE)",
    timeEst: "09:30 - 10:00 EST",
    timeMadrid: "15:30 - 16:00 Madrid",
    importance: "ALTA",
    description: "Campana de apertura de la bolsa de Nueva York. Inyección masiva de volumen algorítmico y descubrimiento de liquidez.",
    tactics: [
      "Tolerar el latigazo inicial de los primeros 5-10 minutos sin perseguir velas.",
      "Observar si el precio barre el máximo o mínimo del pre-mercado para provocar el quiebre de estructura.",
      "Identificar el Opening Range (OR) de los primeros 15 minutos.",
    ],
  },
  {
    name: "La Vela Clave de las 10:00 AM & Judas Swing",
    timeEst: "10:00 - 10:15 EST",
    timeMadrid: "16:00 - 16:15 Madrid",
    importance: "CRÍTICA",
    description: "La vela algorítmica más importante de la sesión. Frecuente Judas Swing (falsa ruptura en contra de la tendencia real para cazar stops institucionales).",
    tactics: [
      "Modelo PO3 (Power of 3): Acumulación en apertura, Manipulación a las 10:00 AM y posterior Distribución.",
      "Buscar reversión cuando el precio barre liquidez previa y deja un FVG en 1m o 2m.",
      "Entrada de Hard Scalping con Stop Loss ceñido detrás del swing de manipulación.",
    ],
  },
  {
    name: "Morning Silver Bullet",
    timeEst: "10:00 - 11:00 EST",
    timeMadrid: "16:00 - 17:00 Madrid",
    importance: "ALTA",
    description: "Ventana de entrega algorítmica de mayor pureza y mejor ratio Riesgo/Beneficio de toda la sesión americana.",
    tactics: [
      "Objetivo de ganancia de 15 a 30 puntos en NQ/MNQ.",
      "Una vez alcanzado el target o sufrida la pérdida máxima, cerrar NinjaTrader y apagar.",
      "No sobreoperar en la pausa del mediodía.",
    ],
  },
  {
    name: "Cierre de Londres (London Close)",
    timeEst: "11:30 - 12:00 EST",
    timeMadrid: "17:30 - 18:00 Madrid",
    importance: "MEDIA",
    description: "Cierre de los libros de órdenes en Europa. Frecuente desaceleración del flujo o reversión intradía.",
    tactics: [
      "Tomar beneficios parciales de las posiciones matutinas.",
      "Evitar nuevas entradas direccionales pesadas.",
    ],
  },
];

export default function EstrategiasHorariosPage() {
  const [currentTimeEst, setCurrentTimeEst] = useState<string>("");
  const [currentTimeMadrid, setCurrentTimeMadrid] = useState<string>("");

  useEffect(() => {
    const updateTimes = () => {
      const now = new Date();
      setCurrentTimeEst(
        now.toLocaleTimeString("es-ES", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", second: "2-digit" })
      );
      setCurrentTimeMadrid(
        now.toLocaleTimeString("es-ES", { timeZone: "Europe/Madrid", hour: "2-digit", minute: "2-digit", second: "2-digit" })
      );
    };
    updateTimes();
    const interval = setInterval(updateTimes, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <Clock className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>El Reloj Institucional & Killzones de Nueva York</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] font-mono">
                Módulo M11 · Gerard García
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono mt-0.5">
              Hard Scalping en Futuros CME (MNQ/NQ) · Manipulación PO3, Vela de las 10:00 AM EST y Silver Bullet
            </p>
          </div>
        </div>
      </div>

      {/* Reloj en Vivo de los Mercados */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
        <div className="p-3.5 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg flex items-center justify-between">
          <div>
            <span className="text-[10px] text-[var(--text-3)] uppercase block">Hora Oficial Wall Street</span>
            <span className="text-base font-bold text-[var(--text-1)]">Nueva York (EST / EDT)</span>
          </div>
          <span className="text-2xl font-bold text-[var(--profit)] tracking-tight">
            {currentTimeEst || "10:00:00"}
          </span>
        </div>

        <div className="p-3.5 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg flex items-center justify-between">
          <div>
            <span className="text-[10px] text-[var(--text-3)] uppercase block">Hora Oficial Europa</span>
            <span className="text-base font-bold text-[var(--text-1)]">Madrid / París (CET)</span>
          </div>
          <span className="text-2xl font-bold text-[var(--text-1)] tracking-tight">
            {currentTimeMadrid || "16:00:00"}
          </span>
        </div>
      </div>

      {/* Killzones Interactivas */}
      <div className="space-y-3 font-mono text-xs">
        <div className="p-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg flex items-center justify-between">
          <span className="font-bold text-[var(--text-1)] uppercase text-[11px]">
            Matriz Horaria Maestra de Ejecución (Gerard García)
          </span>
          <span className="text-[10px] text-[var(--text-3)]">5 Killzones Algorítmicas</span>
        </div>

        <div className="space-y-3">
          {KILLZONES.map((kz, idx) => (
            <div
              key={idx}
              className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-2.5"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border)] pb-2">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-[var(--surface-2)] border border-[var(--border)] text-[10px] flex items-center justify-center font-bold text-[var(--text-1)]">
                    {idx + 1}
                  </span>
                  <h3 className="text-sm font-bold text-[var(--text-1)]">{kz.name}</h3>
                </div>

                <div className="flex items-center gap-2 text-[11px]">
                  <span className="text-[var(--profit)] font-bold">{kz.timeEst}</span>
                  <span className="text-[var(--text-3)]">({kz.timeMadrid})</span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      kz.importance === "CRÍTICA"
                        ? "bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)]"
                        : kz.importance === "ALTA"
                        ? "bg-[var(--surface-2)] text-[var(--text-1)] border border-[var(--border)]"
                        : "bg-[var(--surface-2)] text-[var(--text-3)]"
                    }`}
                  >
                    {kz.importance}
                  </span>
                </div>
              </div>

              <p className="text-[11px] text-[var(--text-2)] font-sans leading-relaxed">
                {kz.description}
              </p>

              {/* Tácticas */}
              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded-md p-3 space-y-1.5 font-sans text-[11px]">
                <span className="font-mono text-[10px] font-bold text-[var(--text-3)] uppercase block">
                  Reglas Tácticas de Entrada:
                </span>
                {kz.tactics.map((t, tidx) => (
                  <div key={tidx} className="flex items-start gap-2 text-[var(--text-2)]">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[var(--profit)] shrink-0 mt-0.5" />
                    <span>{t}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
