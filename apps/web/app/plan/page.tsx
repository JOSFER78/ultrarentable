"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Layers,
  Zap,
  ShieldCheck,
  FileText,
  Cpu,
  Terminal,
  Activity,
  AlertCircle,
  RefreshCw,
  MessageSquare,
} from "lucide-react";
import PlanDashboardHUD from "@/components/plan/PlanDashboardHUD";
import PipelineEstrategiasM1M4 from "@/components/plan/PipelineEstrategiasM1M4";
import DoctrinaVisualView from "@/components/plan/DoctrinaVisualView";
import EspecificacionWebVisual from "@/components/plan/EspecificacionWebVisual";
import PlanGraph, { type PlanBloque } from "@/components/plan/PlanGraph";
import DocViewer from "@/components/plan/DocViewer";
import TableroAgentes from "@/components/plan/TableroAgentes";
import Comentarios from "@/components/plan/Comentarios";
import type { PlanApiResponse } from "@/app/api/plan/route";

type TabId = "fases" | "agy" | "pipeline" | "doctrina" | "especificacion" | "doble_track" | "seguimiento" | "comentarios";

import type { TableroApi } from "@/components/plan/TableroAgentes";

interface ActiveDoc {
  title: string;
  filename: string;
  content: string;
  lastModified?: string;
  sizeBytes?: number;
}

export default function PlanPage() {
  const [activeTab, setActiveTab] = useState<TabId>("fases");
  const [data, setData] = useState<PlanApiResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  // En vivo por defecto (Emilio, 2026-09-03: "la pagina de plan que sea automaticamente
  // actualizada con los MD de dentro"). Las dos rutas leen el disco en cada peticion, asi que
  // refrescar es releer los ficheros: lo que se ve es siempre lo que hay escrito.
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  const [tablero, setTablero] = useState<TableroApi | null>(null);

  const loadTablero = useCallback(async () => {
    try {
      const res = await fetch("/api/tablero", { cache: "no-store" });
      if (!res.ok) throw new Error(String(res.status));
      setTablero((await res.json()) as TableroApi);
    } catch {
      setTablero(null); // sin datos se dice; nunca un tablero de ejemplo
    }
  }, []);

  // Visor de documento Markdown dedicado
  const [activeDoc, setActiveDoc] = useState<ActiveDoc | null>(null);
  const [loadingDoc, setLoadingDoc] = useState<boolean>(false);

  const loadPlan = useCallback(async () => {
    try {
      const res = await fetch("/api/plan", { cache: "no-store" });
      if (!res.ok) throw new Error(`/api/plan respondió ${res.status}`);
      const json: PlanApiResponse = await res.json();
      setData(json);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar /api/plan");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDocument = useCallback(async (docName: string, fallbackTitle?: string) => {
    setLoadingDoc(true);
    try {
      const res = await fetch(`/api/plan/doc?name=${encodeURIComponent(docName)}`, { cache: "no-store" });
      if (!res.ok) throw new Error(`Documento no disponible (${res.status})`);
      const json = await res.json();
      setActiveDoc({
        title: json.title || fallbackTitle || docName,
        filename: json.filename || docName,
        content: json.content,
        lastModified: json.lastModified,
        sizeBytes: json.sizeBytes,
      });
    } catch (err) {
      setActiveDoc({
        title: fallbackTitle || docName,
        filename: docName,
        content: `Error al cargar documento ${docName}: ${err instanceof Error ? err.message : String(err)}`,
      });
    } finally {
      setLoadingDoc(false);
    }
  }, []);

  useEffect(() => {
    void loadPlan();
    void loadTablero();
  }, [loadPlan, loadTablero]);

  // Intervalo de auto-refresco opcional
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      void loadPlan();
      void loadTablero();
    }, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh, loadPlan, loadTablero]);

  const handleSelectBloque = (bloque: PlanBloque) => {
    setActiveDoc({
      title: `${bloque.id} — ${bloque.titulo}`,
      filename: bloque.archivo,
      content: bloque.content || `Fase ${bloque.id} en estado ${bloque.estado}.`,
      lastModified: bloque.actualizado,
    });
  };

  const hud = data?.hud ?? {
    motor_version: "5.18.0",
    certificadas_fondeo: 0,
    meta_estrategias: 0,
    campana_activa: "E2 (ES 5m/15m) B03/B04",
    campana_estado: "5m terminada; 15m en curso",
    criterio_sellado: "Criterio 1.1 Sellado",
    vps_status: "OPERATIVO",
    api_status: "ACTIVA",
    alertas_activas: [],
    ultimo_hallazgo: "E2 5m: 400 sin ventaja bruta, 20 coste; ninguna por falta de trades.",
  };

  const bloques = data?.bloques ?? [];
  const doctrina = data?.doctrina ?? [];
  const pipeline = data?.pipeline ?? [];
  const rutasWeb = data?.rutas_web ?? [];

  // Tareas para AGY: el bloque F10 del plan es el tablero. /api/plan ya cuenta sus filas de tarea
  // (tareas_totales / tareas_completadas); aqui solo se resta. null = todavia no hay datos, y
  // entonces el boton no inventa un numero.
  // Tablero de orquestacion: la fuente es orchestration/tablero/*.md via /api/tablero. El estado
  // de cada tarea es EXACTAMENTE el que pone su fichero; aqui no se deduce ninguno.
  const agyPendientes = tablero ? tablero.sin_verificar : null;

  return (
    <div className="w-full max-w-[1240px] mx-auto space-y-4 font-sans pb-16">
      {/* 1. HUD Visual de Telemetría (Erradica el volcado de texto) */}
      <PlanDashboardHUD
        hud={hud}
        generatedAt={data?.generatedAt}
        autoRefresh={autoRefresh}
        onToggleAutoRefresh={() => setAutoRefresh(!autoRefresh)}
        onRefresh={() => void loadPlan()}
        loading={loading}
      />

      {/* 2. Barra de Pestañas del Dashboard Visual */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-[var(--border)] text-xs font-mono">
        <button
          onClick={() => { setActiveTab("fases"); setActiveDoc(null); }}
          className={`px-3 py-2 rounded-t-md font-medium transition cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === "fases"
              ? "bg-[var(--surface-2)] text-[var(--text-1)] border-b-2 border-[var(--profit)]"
              : "text-[var(--text-3)] hover:text-[var(--text-1)] hover:bg-[var(--surface-1)]"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Fases del plan ({bloques.length})</span>
        </button>

        {/* Tablero de tareas para los agentes de Emilio (AGY). Vive en
            orchestration/state/plan/bloques/F10_operaciones_infra.md y se abre en el visor:
            el agente escribe alli su parte de entrega y el orquestador lo verifica. */}
        <button
          onClick={() => { setActiveTab("agy"); setActiveDoc(null); void loadTablero(); }}
          title="Tareas pendientes para los agentes: seguridad del servidor, infraestructura y traslado de StrategyQuant"
          className={`px-3 py-2 rounded-t-md font-medium transition cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === "agy"
              ? "bg-[var(--surface-2)] text-[var(--text-1)] border-b-2 border-[var(--profit)]"
              : "text-[var(--text-3)] hover:text-[var(--text-1)] hover:bg-[var(--surface-1)]"
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          <span>Tareas AGY{agyPendientes !== null ? ` (${agyPendientes} sin verificar)` : ""}</span>
        </button>

        <button
          onClick={() => { setActiveTab("pipeline"); setActiveDoc(null); }}
          className={`px-3 py-2 rounded-t-md font-medium transition cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === "pipeline"
              ? "bg-[var(--surface-2)] text-[var(--text-1)] border-b-2 border-[var(--profit)]"
              : "text-[var(--text-3)] hover:text-[var(--text-1)] hover:bg-[var(--surface-1)]"
          }`}
        >
          <Zap className="w-3.5 h-3.5 text-[var(--profit)]" />
          <span>Pipeline M1–M4 (StrategyQuant X)</span>
        </button>

        <button
          onClick={() => { setActiveTab("doctrina"); setActiveDoc(null); }}
          className={`px-3 py-2 rounded-t-md font-medium transition cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === "doctrina"
              ? "bg-[var(--surface-2)] text-[var(--text-1)] border-b-2 border-[var(--profit)]"
              : "text-[var(--text-3)] hover:text-[var(--text-1)] hover:bg-[var(--surface-1)]"
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5 text-[var(--profit)]" />
          <span>Doctrina & Leyes Invariantes</span>
        </button>

        <button
          onClick={() => { setActiveTab("especificacion"); setActiveDoc(null); }}
          className={`px-3 py-2 rounded-t-md font-medium transition cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === "especificacion"
              ? "bg-[var(--surface-2)] text-[var(--text-1)] border-b-2 border-[var(--profit)]"
              : "text-[var(--text-3)] hover:text-[var(--text-1)] hover:bg-[var(--surface-1)]"
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Especificación Web</span>
        </button>

        <button
          onClick={() => { setActiveTab("doble_track"); setActiveDoc(null); }}
          className={`px-3 py-2 rounded-t-md font-medium transition cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === "doble_track"
              ? "bg-[var(--surface-2)] text-[var(--text-1)] border-b-2 border-[var(--profit)]"
              : "text-[var(--text-3)] hover:text-[var(--text-1)] hover:bg-[var(--surface-1)]"
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>Doble Track: FONDEO vs ULTRA</span>
        </button>

        <button
          onClick={() => { setActiveTab("seguimiento"); }}
          className={`px-3 py-2 rounded-t-md font-medium transition cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === "seguimiento"
              ? "bg-[var(--surface-2)] text-[var(--text-1)] border-b-2 border-[var(--profit)]"
              : "text-[var(--text-3)] hover:text-[var(--text-1)] hover:bg-[var(--surface-1)]"
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          <span>Bitácora & Traspasos MD</span>
        </button>

        <button
          onClick={() => { setActiveTab("comentarios"); setActiveDoc(null); }}
          className={`px-3 py-2 rounded-t-md font-medium transition cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === "comentarios"
              ? "bg-[var(--surface-2)] text-[var(--text-1)] border-b-2 border-[var(--profit)]"
              : "text-[var(--text-3)] hover:text-[var(--text-1)] hover:bg-[var(--surface-1)]"
          }`}
        >
          <MessageSquare className="w-3.5 h-3.5" />
          <span>Comentarios</span>
        </button>
      </div>

      {/* 3. Visor de Markdown Dedicado (si está activo) */}
      {activeDoc && (
        <div className="space-y-2">
          <DocViewer
            title={activeDoc.title}
            filename={activeDoc.filename}
            content={activeDoc.content}
            lastModified={activeDoc.lastModified}
            sizeBytes={activeDoc.sizeBytes}
            onClose={() => setActiveDoc(null)}
          />
        </div>
      )}

      {/* 4. Contenido Principal según Pestaña (solo cuando activeDoc no cubre la pantalla completa) */}
      {!activeDoc && (
        <>
          {/* PESTAÑA 1: FASES F00-F09 */}
          {activeTab === "fases" && (
            <div className="space-y-4">
              {/* Franja de acceso al Plan Completo (A09) */}
              <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5">
                <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-[var(--border)]">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-[var(--profit)]" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-1)]">
                      Plan Completo del Proyecto
                    </span>
                  </div>
                  <span className="text-[11px] text-[var(--text-3)] font-mono">
                    4 documentos fuente
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                  <button
                    onClick={() => void loadDocument("plan_local_fondeo", "Plan de ejecución FONDEO")}
                    className="flex flex-col text-left p-2.5 rounded border border-[var(--border)] bg-[var(--surface-2)]/40 hover:bg-[var(--surface-2)] hover:border-[var(--profit)]/40 transition group cursor-pointer"
                  >
                    <span className="font-medium text-[var(--text-1)] group-hover:text-[var(--profit)] transition">
                      Plan de ejecución FONDEO — 41 tareas con su criterio de aceptación
                    </span>
                    <span className="text-[11px] text-[var(--text-3)] mt-0.5">
                      41 tareas de ejecución con criterio de aceptación auditable
                    </span>
                  </button>

                  <button
                    onClick={() => void loadDocument("plan_investigacion", "Plan de investigación profunda")}
                    className="flex flex-col text-left p-2.5 rounded border border-[var(--border)] bg-[var(--surface-2)]/40 hover:bg-[var(--surface-2)] hover:border-[var(--profit)]/40 transition group cursor-pointer"
                  >
                    <span className="font-medium text-[var(--text-1)] group-hover:text-[var(--profit)] transition">
                      Plan de investigación profunda — I1 a I7, empezando por StrategyQuant X al 100 %
                    </span>
                    <span className="text-[11px] text-[var(--text-3)] mt-0.5">
                      Siete investigaciones clave, con I1 centrada en rendimiento y caudal de SQX
                    </span>
                  </button>

                  <button
                    onClick={() => void loadDocument("plan_maestro_original", "Plan maestro original (histórico)")}
                    className="flex flex-col text-left p-2.5 rounded border border-[var(--border)] bg-[var(--surface-2)]/40 hover:bg-[var(--surface-2)] hover:border-[var(--profit)]/40 transition group cursor-pointer"
                  >
                    <span className="font-medium text-[var(--text-1)] group-hover:text-[var(--profit)] transition">
                      Plan maestro original (histórico) — antes de partirlo en fases
                    </span>
                    <span className="text-[11px] text-[var(--text-3)] mt-0.5">
                      Versión monolítica v4 fundacional previa a la división en 11 fases
                    </span>
                  </button>

                  <button
                    onClick={() => void loadDocument("especificacion_web", "Especificación de la web")}
                    className="flex flex-col text-left p-2.5 rounded border border-[var(--border)] bg-[var(--surface-2)]/40 hover:bg-[var(--surface-2)] hover:border-[var(--profit)]/40 transition group cursor-pointer"
                  >
                    <span className="font-medium text-[var(--text-1)] group-hover:text-[var(--profit)] transition">
                      Especificación de la web — qué debe hacer cada página
                    </span>
                    <span className="text-[11px] text-[var(--text-3)] mt-0.5">
                      Definición de rutas, contratos de datos y directivas de interfaz
                    </span>
                  </button>
                </div>
              </div>

              {loading && bloques.length === 0 && (
                <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-8 text-center font-mono text-xs">
                  <RefreshCw className="w-5 h-5 mx-auto mb-2 text-[var(--text-3)] animate-spin" />
                  <p className="text-[var(--text-3)]">Leyendo fases en disco…</p>
                </div>
              )}

              {error && (
                <div className="bg-[var(--surface-1)] border border-[var(--loss)] rounded-lg p-6 text-center font-mono text-xs">
                  <AlertCircle className="w-5 h-5 mx-auto mb-2 text-[var(--loss)]" />
                  <h2 className="font-bold text-[var(--text-1)] uppercase">Error al leer /api/plan</h2>
                  <p className="mt-1.5 text-[var(--text-3)]">{error}</p>
                </div>
              )}

              {bloques.length > 0 && (
                <PlanGraph bloques={bloques} onSelectBloque={handleSelectBloque} />
              )}
            </div>
          )}

          {/* PESTAÑA 2: TABLERO DE TAREAS AGY (A05) */}
          {activeTab === "agy" && (
            <TableroAgentes
              onSelectTarea={(id, titulo) => void loadDocument(id, `Tarea ${id}: ${titulo}`)}
              onOpenDoc={(docName, title) => void loadDocument(docName, title)}
              tableroData={tablero}
              onRefresh={() => void loadTablero()}
            />
          )}

          {activeTab === "pipeline" && (
            <PipelineEstrategiasM1M4 modulos={pipeline} />
          )}

          {/* PESTAÑA 3: DOCTRINA & LEYES INVARIANTES */}
          {activeTab === "doctrina" && (
            <DoctrinaVisualView
              doctrina={doctrina}
              onOpenDoc={(docName, title) => void loadDocument(docName, title)}
            />
          )}

          {/* PESTAÑA 4: ESPECIFICACIÓN WEB */}
          {activeTab === "especificacion" && (
            <EspecificacionWebVisual
              rutas={rutasWeb}
              onOpenDoc={(docName, title) => void loadDocument(docName, title)}
            />
          )}

          {/* PESTAÑA 5: DOBLE TRACK: FONDEO VS ULTRA */}
          {activeTab === "doble_track" && (
            <div className="space-y-4 font-sans text-xs">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Carril Activo: FONDEO */}
                <div className="bg-[var(--surface-1)] border border-[var(--profit)] rounded-lg p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-1 rounded-full bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)] text-[11px] font-mono uppercase font-bold">
                      CARRIL ACTIVO · 100% ESFUERZO
                    </span>
                    <span className="text-[11px] font-mono text-[var(--text-3)]">Mandato Emilio (2026-09-01)</span>
                  </div>
                  <h2 className="text-lg font-bold text-[var(--text-1)]">Fondeo CME & StrategyQuant X</h2>
                  <p className="text-[12px] text-[var(--text-2)] leading-relaxed font-sans">
                    El 100% del cómputo y del equipo de agentes está volcado en **explotar StrategyQuant X (SQX) al 100% en el VPS** y en la minería de futuros CME regulados (ES/NQ 5m y 15m) para aprobar exámenes de prop firms.
                  </p>
                  <div className="space-y-2 text-xs font-mono text-[var(--text-2)] border-t border-[var(--border)] pt-3">
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--profit)]" />
                      <span><strong>M1 Generación:</strong> SQX headless (sqcli) en VPS (:5050).</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--profit)]" />
                      <span><strong>M2 Mejora:</strong> Bucle de validación, telemetría de embudos.</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--profit)]" />
                      <span><strong>M3 Examen:</strong> 11 gates del Criterio 1.1 sellado (≥200 ops OOS, PF ≥1.25).</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--profit)]" />
                      <span><strong>M4 Meta:</strong> Combinaciones multi-estrategia para reducir drawdown.</span>
                    </div>
                  </div>
                  <div className="pt-2">
                    <a
                      href="/estrategias"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border border-[var(--border)] text-xs text-[var(--text-1)] font-mono transition"
                    >
                      <span>Ir a la Maestra de Estrategias</span>
                    </a>
                  </div>
                </div>

                {/* Carril Aparcado: ULTRA */}
                <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-4 opacity-85 hover:opacity-100 transition">
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-1 rounded-full bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] text-[11px] font-mono uppercase font-bold">
                      EN CONSTRUCCIÓN / APARCADO
                    </span>
                    <span className="text-[11px] font-mono text-[var(--text-3)]">PUNTO_GUARDADO_ULTRA.md</span>
                  </div>
                  <h2 className="text-lg font-bold text-[var(--text-1)]">Envolvente ULTRA (Miles de %)</h2>
                  <p className="text-[12px] text-[var(--text-2)] leading-relaxed font-sans">
                    La tesis de la envolvente de balas: la convexidad de miles de % no nace de señales mágicas, sino de **balas de 1R que piramidan sobre ganadoras y toleran hasta un 80% de drawdown flotante**.
                  </p>
                  <div className="space-y-2 text-xs font-mono text-[var(--text-2)] border-t border-[var(--border)] pt-3">
                    <div className="flex items-center gap-2 text-[var(--text-3)]">
                      <span>›</span>
                      <span><strong>Fase F05:</strong> Envolvente ULTRA (congelada a propósito).</span>
                    </div>
                    <div className="flex items-center gap-2 text-[var(--text-3)]">
                      <span>›</span>
                      <span><strong>Fase F06:</strong> Router de meta-estrategias ULTRA.</span>
                    </div>
                    <div className="flex items-center gap-2 text-[var(--text-3)]">
                      <span>›</span>
                      <span><strong>Condición de desbloqueo:</strong> Disponer de estrategias fondeo certificadas.</span>
                    </div>
                  </div>
                  <div className="pt-2">
                    <button
                      onClick={() => void loadDocument("punto_guardado_ultra", "Punto de Guardado ULTRA")}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border border-[var(--border)] text-xs text-[var(--text-1)] font-mono transition cursor-pointer"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Leer PUNTO_GUARDADO_ULTRA.md</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* PESTAÑA 6: BITÁCORA & TRASPASOS MD */}
          {activeTab === "seguimiento" && (
            <div className="space-y-4 font-mono text-xs">
              <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3">
                <div className="text-xs font-bold text-[var(--text-1)] uppercase">
                  Documentos de Seguimiento Directos de la Orquestación
                </div>
                <p className="text-[11px] text-[var(--text-3)] font-sans">
                  Selecciona cualquiera de los informes Markdown en disco para inspeccionar el registro crudo y completo de los agentes:
                </p>
                <div className="flex flex-wrap items-center gap-2 pt-1">
                  <button
                    onClick={() => void loadDocument("current_phase", "Seguimiento en Vivo (Current Phase)")}
                    className="px-3 py-1.5 rounded-md border border-[var(--border)] bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-[var(--text-1)] transition cursor-pointer flex items-center gap-1.5"
                  >
                    <Activity className="w-3.5 h-3.5 text-[var(--profit)]" />
                    <span>current_phase.md (En vivo)</span>
                  </button>
                  <button
                    onClick={() => void loadDocument("traspaso_vps", "Informe de Traspaso VPS")}
                    className="px-3 py-1.5 rounded-md border border-[var(--border)] bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-[var(--text-1)] transition cursor-pointer flex items-center gap-1.5"
                  >
                    <Terminal className="w-3.5 h-3.5 text-[var(--profit)]" />
                    <span>TRASPASO_VPS.md</span>
                  </button>
                  <button
                    onClick={() => void loadDocument("traspaso_pc", "Informe de Traspaso PC Noche")}
                    className="px-3 py-1.5 rounded-md border border-[var(--border)] bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-[var(--text-1)] transition cursor-pointer flex items-center gap-1.5"
                  >
                    <Terminal className="w-3.5 h-3.5 text-[var(--profit)]" />
                    <span>TRASPASO_PC_noche.md</span>
                  </button>
                  <button
                    onClick={() => void loadDocument("ventana_emilio", "Ventana de Decisiones (Emilio)")}
                    className="px-3 py-1.5 rounded-md border border-[var(--border)] bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-[var(--text-1)] transition cursor-pointer flex items-center gap-1.5"
                  >
                    <FileText className="w-3.5 h-3.5 text-[var(--profit)]" />
                    <span>VENTANA_EMILIO.md</span>
                  </button>
                  <button
                    onClick={() => void loadDocument("plan_maestro", "Plan Maestro v4")}
                    className="px-3 py-1.5 rounded-md border border-[var(--border)] bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-[var(--text-1)] transition cursor-pointer flex items-center gap-1.5"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>plan_maestro.md</span>
                  </button>
                </div>
              </div>

              {loadingDoc && (
                <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-8 text-center">
                  <RefreshCw className="w-5 h-5 mx-auto mb-2 text-[var(--text-3)] animate-spin" />
                  <p className="text-[var(--text-3)]">Cargando documento Markdown…</p>
                </div>
              )}
            </div>
          )}

          {/* PESTAÑA 8: COMENTARIOS DE EMILIO */}
          {activeTab === "comentarios" && (
            <Comentarios />
          )}
        </>
      )}
    </div>
  );
}
