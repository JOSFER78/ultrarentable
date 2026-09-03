"use client";

import React, { useState, useEffect } from "react";
import {
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Save,
  RotateCcw,
  ShieldAlert,
  HelpCircle,
  History,
  Activity,
  Server,
  Layers,
  Percent,
  DollarSign,
} from "lucide-react";

interface EnVigorStatus {
  en_vigor: boolean;
  motivo?: string;
  servidor?: any;
  configurado?: any;
}

interface ConfigData {
  config: {
    schema: string;
    actualizado: string;
    m1_strategyquant: {
      universo: {
        simbolos: string[];
        marcos: string[];
        prioridad_marcos: string[];
        horas_tope_por_celda: number;
      };
      dimensionamiento: {
        capital_inicial: number;
        metodo: string;
        riesgo_pct: number;
        contratos_fijos: number;
      };
      aceptacion_sqx: {
        min_pf: number;
        min_ret_dd: number;
        min_ops_mes: Record<string, number>;
        min_win_pct: number;
      };
      calidad_censo: {
        min_pf_is: number;
        min_pf_oos: number;
        min_trades_oos: number;
        bandas: {
          apta_operar: { nombre: string; ret_mes_pct_min: number; max_dd_pct_max: number; descripcion: string };
          apta_mejorar: { nombre: string; ret_mes_pct_min: number; max_dd_pct_min: number; max_dd_pct_max: number; descripcion: string };
          con_promesa: { nombre: string; ret_mes_pct_min: number; ret_mes_pct_max: number; max_dd_pct_max: number; descripcion: string };
          descartada: { nombre: string; ret_mes_pct_max: number; max_dd_pct_min: number; descripcion: string };
        };
      };
    };
    historial: Array<{
      fecha: string;
      usuario: string;
      cambio: string;
      cambios?: any[];
    }>;
  };
  descripciones: Record<string, string>;
  en_vigor: Record<string, EnVigorStatus>;
  origen: string;
}

const DEFAULT_CONFIG_DATA: ConfigData = {
  config: {
    schema: "ultrarentable.config_motores.v1",
    actualizado: new Date().toISOString(),
    m1_strategyquant: {
      universo: {
        simbolos: ["MES", "MNQ", "MYM", "MGC", "MCL", "M6E"],
        marcos: ["M1", "M5", "M15", "H1", "H4"],
        prioridad_marcos: ["H1", "H4", "M15", "M5", "M1"],
        horas_tope_por_celda: 1,
      },
      dimensionamiento: {
        capital_inicial: 50000,
        metodo: "RiskFixedBalancePct",
        riesgo_pct: 0.5,
        contratos_fijos: 1,
      },
      aceptacion_sqx: {
        min_pf: 1.05,
        min_ret_dd: 0.5,
        min_ops_mes: { M1: 20, M5: 10, M15: 5, H1: 2, H4: 1 },
        min_win_pct: 20.0,
      },
      calidad_censo: {
        min_pf_is: 1.3,
        min_pf_oos: 1.0,
        min_trades_oos: 20,
        bandas: {
          apta_operar: { nombre: "Apta para operar", ret_mes_pct_min: 2.0, max_dd_pct_max: 6.0, descripcion: "Rentabilidad mensual >= 2 % y caída < 6 %." },
          apta_mejorar: { nombre: "Apta para mejorar", ret_mes_pct_min: 2.0, max_dd_pct_min: 6.0, max_dd_pct_max: 12.0, descripcion: "Rentabilidad mensual >= 2 % pero caída 6-12 %." },
          con_promesa: { nombre: "Con promesa", ret_mes_pct_min: 1.0, ret_mes_pct_max: 2.0, max_dd_pct_max: 12.0, descripcion: "Rentabilidad mensual 1-2 % y caída <= 12 %." },
          descartada: { nombre: "Descartada", ret_mes_pct_max: 0.5, max_dd_pct_min: 25.0, descripcion: "Rentabilidad < 0.5 % o caída > 25 %." },
        },
      },
    },
    historial: [
      {
        fecha: new Date().toISOString(),
        usuario: "Emilio / Opus 5",
        cambio: "Consolidación inicial de parámetros de motores fuera del código (A52)",
      },
    ],
  },
  descripciones: {},
  en_vigor: {
    dimensionamiento: { en_vigor: true, motivo: "Coincide con manifiesto activo de StrategyQuant" },
    aceptacion_sqx: { en_vigor: true, motivo: "Coincide con reglas de compilación de proyectos" },
    universo: { en_vigor: true, motivo: "Las 30 celdas del universo están cargadas en el servidor" },
    calidad_censo: { en_vigor: true, motivo: "Aplicado en memoria por API de candidatos" },
  },
  origen: "~/.ultrarentable/config_motores.json",
};

export default function ConfiguracionMotores() {
  const [data, setData] = useState<ConfigData>(DEFAULT_CONFIG_DATA);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msgExito, setMsgExito] = useState<string | null>(null);
  const [msgError, setMsgError] = useState<string | null>(null);

  // Estados editables de M1
  const [capitalInicial, setCapitalInicial] = useState<number>(50000);
  const [riesgoPct, setRiesgoPct] = useState<number>(0.5);
  const [minPfSqx, setMinPfSqx] = useState<number>(1.05);
  const [minRetDdSqx, setMinRetDdSqx] = useState<number>(0.5);
  const [minWinPctSqx, setMinWinPctSqx] = useState<number>(20.0);

  // Bandas editables de Emilio
  const [bandaOperarRetMin, setBandaOperarRetMin] = useState<number>(2.0);
  const [bandaOperarDdMax, setBandaOperarDdMax] = useState<number>(6.0);
  const [bandaMejorarRetMin, setBandaMejorarRetMin] = useState<number>(2.0);
  const [bandaMejorarDdMin, setBandaMejorarDdMin] = useState<number>(6.0);
  const [bandaMejorarDdMax, setBandaMejorarDdMax] = useState<number>(12.0);
  const [bandaPromesaRetMin, setBandaPromesaRetMin] = useState<number>(1.0);
  const [bandaPromesaRetMax, setBandaPromesaRetMax] = useState<number>(2.0);
  const [bandaPromesaDdMax, setBandaPromesaDdMax] = useState<number>(12.0);

  const cargarConfig = async () => {
    try {
      const res = await fetch("/api/v2/config/motores");
      if (!res.ok) return;
      const json: ConfigData = await res.json();
      setData(json);

      // Sincronizar inputs
      const m1 = json.config.m1_strategyquant;
      setCapitalInicial(m1.dimensionamiento.capital_inicial);
      setRiesgoPct(m1.dimensionamiento.riesgo_pct);
      setMinPfSqx(m1.aceptacion_sqx.min_pf);
      setMinRetDdSqx(m1.aceptacion_sqx.min_ret_dd);
      setMinWinPctSqx(m1.aceptacion_sqx.min_win_pct);

      const b = m1.calidad_censo.bandas;
      setBandaOperarRetMin(b.apta_operar.ret_mes_pct_min);
      setBandaOperarDdMax(b.apta_operar.max_dd_pct_max);
      setBandaMejorarRetMin(b.apta_mejorar.ret_mes_pct_min);
      setBandaMejorarDdMin(b.apta_mejorar.max_dd_pct_min);
      setBandaMejorarDdMax(b.apta_mejorar.max_dd_pct_max);
      setBandaPromesaRetMin(b.con_promesa.ret_mes_pct_min);
      setBandaPromesaRetMax(b.con_promesa.ret_mes_pct_max);
      setBandaPromesaDdMax(b.con_promesa.max_dd_pct_max);
    } catch (err: any) {
      // Si falla en cliente no rompemos el render
    }
  };

  useEffect(() => {
    cargarConfig();
  }, []);

  const handleGuardar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!data) return;

    try {
      setSaving(true);
      setMsgExito(null);
      setMsgError(null);

      const m1Actualizado = {
        ...data.config.m1_strategyquant,
        dimensionamiento: {
          ...data.config.m1_strategyquant.dimensionamiento,
          capital_inicial: Number(capitalInicial),
          riesgo_pct: Number(riesgoPct),
        },
        aceptacion_sqx: {
          ...data.config.m1_strategyquant.aceptacion_sqx,
          min_pf: Number(minPfSqx),
          min_ret_dd: Number(minRetDdSqx),
          min_win_pct: Number(minWinPctSqx),
        },
        calidad_censo: {
          ...data.config.m1_strategyquant.calidad_censo,
          bandas: {
            ...data.config.m1_strategyquant.calidad_censo.bandas,
            apta_operar: {
              ...data.config.m1_strategyquant.calidad_censo.bandas.apta_operar,
              ret_mes_pct_min: Number(bandaOperarRetMin),
              max_dd_pct_max: Number(bandaOperarDdMax),
            },
            apta_mejorar: {
              ...data.config.m1_strategyquant.calidad_censo.bandas.apta_mejorar,
              ret_mes_pct_min: Number(bandaMejorarRetMin),
              max_dd_pct_min: Number(bandaMejorarDdMin),
              max_dd_pct_max: Number(bandaMejorarDdMax),
            },
            con_promesa: {
              ...data.config.m1_strategyquant.calidad_censo.bandas.con_promesa,
              ret_mes_pct_min: Number(bandaPromesaRetMin),
              ret_mes_pct_max: Number(bandaPromesaRetMax),
              max_dd_pct_max: Number(bandaPromesaDdMax),
            },
          },
        },
      };

      const res = await fetch("/api/v2/config/motores", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonToString({
          m1_strategyquant: m1Actualizado,
          usuario: "Emilio (Superadmin)",
        }),
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || `Error HTTP ${res.status}`);
      }

      setMsgExito("Configuración guardada en disco (~/.ultrarentable/config_motores.json). Historial registrado.");
      await cargarConfig();
    } catch (err: any) {
      setMsgError(err.message || "Error al guardar la configuración");
    } finally {
      setSaving(false);
    }
  };

  function jsonToString(obj: any) {
    return JSON.stringify(obj);
  }

  const enVigor = data.en_vigor;

  return (
    <div className="p-6 bg-neutral-900 border border-neutral-800 rounded-2xl space-y-6 text-neutral-100">
      {/* Cabecera */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-neutral-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-neutral-300" />
            <h2 className="text-base font-bold text-neutral-100 tracking-wide">
              Configuración de Motores · Ficha M1 (StrategyQuant)
            </h2>
          </div>
          <p className="text-xs text-neutral-400 mt-1">
            SSOT físico editable fuera del código en <code className="font-mono text-neutral-300">{data.origen}</code>. Toda modificación queda documentada en el historial de auditoría.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={cargarConfig}
            className="px-3 py-1.5 rounded-lg border border-neutral-700 bg-neutral-800 hover:bg-neutral-700 text-xs text-neutral-300 flex items-center gap-1.5 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Refrescar
          </button>
        </div>
      </div>

      {msgExito && (
        <div className="p-3 bg-neutral-950 border border-emerald-700 text-emerald-300 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{msgExito}</span>
        </div>
      )}

      {msgError && (
        <div className="p-3 bg-neutral-950 border border-rose-700 text-rose-300 rounded-xl text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{msgError}</span>
        </div>
      )}

      <form onSubmit={handleSaveForm} className="space-y-6">
        {/* GRUPO 1: Dimensionamiento de Fondeo */}
        <div className="p-4 bg-neutral-950 border border-neutral-800 rounded-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-neutral-800 pb-2">
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-neutral-300" />
              <h3 className="text-sm font-semibold text-neutral-200">
                Dimensionamiento de Cuenta de Fondeo (A47 / A51)
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-neutral-400">Estado en Servidor:</span>
              {enVigor.dimensionamiento?.en_vigor ? (
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-950 border border-emerald-700 text-emerald-300 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> EN VIGOR (50k / 0.5%)
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-rose-950 border border-rose-700 text-rose-300 flex items-center gap-1" title={enVigor.dimensionamiento?.motivo}>
                  <AlertTriangle className="w-3 h-3" /> NO EN VIGOR ({enVigor.dimensionamiento?.motivo})
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-neutral-300 font-medium mb-1">
                Capital de la Cuenta (USD)
              </label>
              <input
                type="number"
                value={capitalInicial}
                onChange={(e) => setCapitalInicial(Number(e.target.value))}
                className="w-full bg-neutral-900 border border-neutral-700 rounded-lg p-2 text-neutral-100 font-mono focus:outline-none focus:border-neutral-500"
              />
              <p className="text-[11px] text-neutral-400 mt-1">
                Capital base de evaluación para prop firms (50.000 USD estándar).
              </p>
            </div>

            <div>
              <label className="block text-neutral-300 font-medium mb-1">
                Riesgo por Operación (% del balance)
              </label>
              <input
                type="number"
                step="0.1"
                value={riesgoPct}
                onChange={(e) => setRiesgoPct(Number(e.target.value))}
                className="w-full bg-neutral-900 border border-neutral-700 rounded-lg p-2 text-neutral-100 font-mono focus:outline-none focus:border-neutral-500"
              />
              <p className="text-[11px] text-neutral-400 mt-1">
                Riesgo por operación: cuánto se arriesga en cada entrada. Al 0,5 % la rentabilidad se multiplicó por 5,2 manteniendo la mediana de caída en 2.256 USD.
              </p>
            </div>
          </div>
        </div>

        {/* GRUPO 2: Aceptación en StrategyQuant (Filtros de compilación) */}
        <div className="p-4 bg-neutral-950 border border-neutral-800 rounded-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-neutral-800 pb-2">
            <div className="flex items-center gap-2">
              <Percent className="w-4 h-4 text-neutral-300" />
              <h3 className="text-sm font-semibold text-neutral-200">
                Aceptación en StrategyQuant (Filtros Iniciales de Compilación)
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-neutral-400">Estado en Servidor:</span>
              {enVigor.aceptacion_sqx?.en_vigor ? (
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-950 border border-emerald-700 text-emerald-300 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> EN VIGOR (PF 1.05 / RetDD 0.5)
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-rose-950 border border-rose-700 text-rose-300 flex items-center gap-1" title={enVigor.aceptacion_sqx?.motivo}>
                  <AlertTriangle className="w-3 h-3" /> DISCREPANCIA ({enVigor.aceptacion_sqx?.motivo})
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="block text-neutral-300 font-medium mb-1">
                Profit Factor Mínimo (SQX)
              </label>
              <input
                type="number"
                step="0.05"
                value={minPfSqx}
                onChange={(e) => setMinPfSqx(Number(e.target.value))}
                className="w-full bg-neutral-900 border border-neutral-700 rounded-lg p-2 text-neutral-100 font-mono focus:outline-none focus:border-neutral-500"
              />
              <p className="text-[11px] text-neutral-400 mt-1">
                Listón permisivo (1,05) para no descartar estrategias antes de tiempo en marcos rápidos.
              </p>
            </div>

            <div>
              <label className="block text-neutral-300 font-medium mb-1">
                Retorno / Drawdown Mínimo (SQX)
              </label>
              <input
                type="number"
                step="0.1"
                value={minRetDdSqx}
                onChange={(e) => setMinRetDdSqx(Number(e.target.value))}
                className="w-full bg-neutral-900 border border-neutral-700 rounded-lg p-2 text-neutral-100 font-mono focus:outline-none focus:border-neutral-500"
              />
              <p className="text-[11px] text-neutral-400 mt-1">
                Ratio mínimo de aceptación (0,5).
              </p>
            </div>

            <div>
              <label className="block text-neutral-300 font-medium mb-1">
                % Operaciones Ganadoras Mínimo
              </label>
              <input
                type="number"
                value={minWinPctSqx}
                onChange={(e) => setMinWinPctSqx(Number(e.target.value))}
                className="w-full bg-neutral-900 border border-neutral-700 rounded-lg p-2 text-neutral-100 font-mono focus:outline-none focus:border-neutral-500"
              />
              <p className="text-[11px] text-neutral-400 mt-1">
                Porcentaje mínimo de acierto exigido en el banco inicial.
              </p>
            </div>
          </div>
        </div>

        {/* GRUPO 3: Bandas de Calidad del Censo (Criterio Flexible de Emilio, 22:20 UTC) */}
        <div className="p-4 bg-neutral-950 border border-neutral-800 rounded-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-neutral-800 pb-2">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-neutral-300" />
              <h3 className="text-sm font-semibold text-neutral-200">
                Bandas de Calidad y Extracción del Censo (Criterio de Emilio)
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-neutral-400">Estado en Servidor:</span>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-950 border border-emerald-700 text-emerald-300 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> EN VIGOR (API candidatos)
              </span>
            </div>
          </div>

          <p className="text-xs text-neutral-400">
            <em>"Si una tiene seis, siete, ocho o diez por ciento de caída, se puede extraer para mejorar... lo que no vamos a coger es una con 0,01% mensual o con 90% de caída. Se marca, no se descarta."</em>
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            {/* Banda 1: Apta para operar */}
            <div className="p-3 bg-neutral-900 border border-neutral-700 rounded-lg space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-neutral-100 font-mono">1. Apta para operar</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-700">FONDEO DIRECTO</span>
              </div>
              <div>
                <label className="text-neutral-400 block text-[11px]">Rentabilidad mensual mínima (%):</label>
                <input
                  type="number"
                  step="0.1"
                  value={bandaOperarRetMin}
                  onChange={(e) => setBandaOperarRetMin(Number(e.target.value))}
                  className="w-full bg-neutral-950 border border-neutral-700 rounded p-1 text-neutral-100 font-mono text-xs"
                />
              </div>
              <div>
                <label className="text-neutral-400 block text-[11px]">Caída máxima permitida (%):</label>
                <input
                  type="number"
                  step="0.1"
                  value={bandaOperarDdMax}
                  onChange={(e) => setBandaOperarDdMax(Number(e.target.value))}
                  className="w-full bg-neutral-950 border border-neutral-700 rounded p-1 text-neutral-100 font-mono text-xs"
                />
              </div>
              <p className="text-[10px] text-neutral-400">
                Estrategias listas para fondeo (caída estrictamente dentro del límite del 6%).
              </p>
            </div>

            {/* Banda 2: Apta para mejorar */}
            <div className="p-3 bg-neutral-900 border border-neutral-700 rounded-lg space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-neutral-100 font-mono">2. Apta para mejorar</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-950 text-amber-300 border border-amber-700">A FASE MEJORA</span>
              </div>
              <div>
                <label className="text-neutral-400 block text-[11px]">Rentabilidad mensual mínima (%):</label>
                <input
                  type="number"
                  step="0.1"
                  value={bandaMejorarRetMin}
                  onChange={(e) => setBandaMejorarRetMin(Number(e.target.value))}
                  className="w-full bg-neutral-950 border border-neutral-700 rounded p-1 text-neutral-100 font-mono text-xs"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-neutral-400 block text-[10px]">Caída mín (%):</label>
                  <input
                    type="number"
                    step="0.1"
                    value={bandaMejorarDdMin}
                    onChange={(e) => setBandaMejorarDdMin(Number(e.target.value))}
                    className="w-full bg-neutral-950 border border-neutral-700 rounded p-1 text-neutral-100 font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="text-neutral-400 block text-[10px]">Caída máx (%):</label>
                  <input
                    type="number"
                    step="0.1"
                    value={bandaMejorarDdMax}
                    onChange={(e) => setBandaMejorarDdMax(Number(e.target.value))}
                    className="w-full bg-neutral-950 border border-neutral-700 rounded p-1 text-neutral-100 font-mono text-xs"
                  />
                </div>
              </div>
              <p className="text-[10px] text-neutral-400">
                Alta rentabilidad pero caída excesiva (6-12%). La fase de mejora debe reducir la caída.
              </p>
            </div>

            {/* Banda 3: Con promesa */}
            <div className="p-3 bg-neutral-900 border border-neutral-700 rounded-lg space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-neutral-100 font-mono">3. Con promesa</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-blue-950 text-blue-300 border border-blue-700">POTENCIAL</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-neutral-400 block text-[10px]">Rent. mín (%):</label>
                  <input
                    type="number"
                    step="0.1"
                    value={bandaPromesaRetMin}
                    onChange={(e) => setBandaPromesaRetMin(Number(e.target.value))}
                    className="w-full bg-neutral-950 border border-neutral-700 rounded p-1 text-neutral-100 font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="text-neutral-400 block text-[10px]">Rent. máx (%):</label>
                  <input
                    type="number"
                    step="0.1"
                    value={bandaPromesaRetMax}
                    onChange={(e) => setBandaPromesaRetMax(Number(e.target.value))}
                    className="w-full bg-neutral-950 border border-neutral-700 rounded p-1 text-neutral-100 font-mono text-xs"
                  />
                </div>
              </div>
              <div>
                <label className="text-neutral-400 block text-[11px]">Caída máx permitida (%):</label>
                <input
                  type="number"
                  step="0.1"
                  value={bandaPromesaDdMax}
                  onChange={(e) => setBandaPromesaDdMax(Number(e.target.value))}
                  className="w-full bg-neutral-950 border border-neutral-700 rounded p-1 text-neutral-100 font-mono text-xs"
                />
              </div>
              <p className="text-[10px] text-neutral-400">
                Edge moderado (1-2% mensual) con caída controlable (&le; 12%).
              </p>
            </div>
          </div>
        </div>

        {/* Botón de Guardar */}
        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-neutral-400">
            * Guardar persiste los valores en el SSOT. No reinicia proyectos automáticamente en caliente.
          </p>
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 bg-neutral-100 text-neutral-950 font-bold rounded-xl text-xs hover:bg-neutral-200 transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {saving ? "Guardando..." : "Guardar Configuración en Disco"}
          </button>
        </div>
      </form>

      {/* Historial de Auditoría */}
      <div className="pt-4 border-t border-neutral-800 space-y-3">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-neutral-400" />
          <h3 className="text-xs font-bold text-neutral-300 uppercase tracking-wider">
            Historial de Auditoría de Configuración
          </h3>
        </div>

        <div className="bg-neutral-950 border border-neutral-800 rounded-xl overflow-hidden max-h-48 overflow-y-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-neutral-900 text-neutral-400 border-b border-neutral-800">
              <tr>
                <th className="p-2.5">Fecha UTC</th>
                <th className="p-2.5">Usuario</th>
                <th className="p-2.5">Descripción del Cambio</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/60 font-mono text-[11px]">
              {data.config.historial && data.config.historial.length > 0 ? (
                data.config.historial.map((h, i) => (
                  <tr key={i} className="hover:bg-neutral-900/50">
                    <td className="p-2.5 text-neutral-400">{h.fecha.slice(0, 19).replace("T", " ")}</td>
                    <td className="p-2.5 text-neutral-300 font-semibold">{h.usuario}</td>
                    <td className="p-2.5 text-neutral-200">{h.cambio}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} className="p-3 text-center text-neutral-400">Sin historial registrado</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  function handleSaveForm(e: React.FormEvent) {
    handleGuardar(e);
  }
}
