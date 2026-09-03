"use client";

import React, { useState } from "react";
import {
  Server,
  Cpu,
  Zap,
  Activity,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Monitor,
  Terminal,
  Settings,
} from "lucide-react";

export default function InfraestructuraNinjaTraderPage() {
  const [selectedTech, setSelectedTech] = useState<"NT8" | "RITHMIC" | "TRADOVATE">("NT8");

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <Server className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Infraestructura NinjaTrader 8 & Datafeeds CME</span>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                MÓDULO M09
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono">
              Arquitectura de baja latencia, ruteo de órdenes Rithmic / Tradovate y plantillas de ejecución CME.
            </p>
          </div>
        </div>
      </div>

      {/* Selector de Tecnología */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {[
          {
            id: "NT8" as const,
            name: "NinjaTrader 8 (x64)",
            subtitle: "Motor Gráfico & Chart Trader",
            icon: Monitor,
            badge: "ESTÁNDAR CME",
          },
          {
            id: "RITHMIC" as const,
            name: "Rithmic R | Trader Pro",
            subtitle: "Ruteo de Órdenes & Risk Gateway",
            icon: Terminal,
            badge: "BAJA LATENCIA",
          },
          {
            id: "TRADOVATE" as const,
            name: "Tradovate API Cloud",
            subtitle: "Webhooks & Conectividad Web",
            icon: Zap,
            badge: "CLOUD NATIVO",
          },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setSelectedTech(t.id)}
            className={`p-4 rounded-lg border text-left transition cursor-pointer flex flex-col justify-between ${
              selectedTech === t.id
                ? "bg-[var(--surface-2)] border-[var(--profit)] shadow-md"
                : "bg-[var(--surface-1)] border-[var(--border)] hover:bg-[var(--surface-2)]"
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--surface-3)] text-[var(--profit)] border border-[var(--border)]">
                {t.badge}
              </span>
              <t.icon className="w-4 h-4 text-[var(--text-2)]" />
            </div>
            <div className="text-sm font-bold text-[var(--text-1)]">{t.name}</div>
            <div className="text-xs text-[var(--text-3)] mt-0.5">{t.subtitle}</div>
          </button>
        ))}
      </div>

      {/* Panel Técnico Detallado */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-4">
        {selectedTech === "NT8" && (
          <div className="space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2 font-sans">
              <h2 className="text-sm font-bold text-[var(--text-1)]">
                Configuración Óptima de NinjaTrader 8 para Fondeo CME
              </h2>
              <span className="text-xs text-[var(--profit)] font-mono">Build 8.1.3+ Recomendada</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-sans">
              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3 space-y-1.5">
                <div className="text-xs font-bold text-[var(--text-1)] flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[var(--profit)]" />
                  <span>Aceleración por Hardware & GPU</span>
                </div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Activar Direct2D en Opciones &gt; General &gt; Rendering. Reduce los tirones en gráficos de ticks o volumen alto de NQ.
                </p>
              </div>

              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3 space-y-1.5">
                <div className="text-xs font-bold text-[var(--text-1)] flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[var(--profit)]" />
                  <span>Estrategias ATM (Advanced Trade Management)</span>
                </div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Configurar brackets automáticos OCO (Stop Loss y Take Profit fijos al instante del fill) para blindar la ejecución contra desconexiones.
                </p>
              </div>

              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3 space-y-1.5">
                <div className="text-xs font-bold text-[var(--text-1)] flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[var(--profit)]" />
                  <span>Aislamiento de Cuentas por Conexión</span>
                </div>
                <p className="text-[11px] text-[var(--text-3)]">
                  No mezclar credenciales de diferentes prop firms en una misma conexión para prevenir ruteos cruzados indeseados.
                </p>
              </div>

              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3 space-y-1.5">
                <div className="text-xs font-bold text-[var(--text-1)] flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[var(--profit)]" />
                  <span>Limpieza de Base de Datos Diaria</span>
                </div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Purgar caché de ticks histórica en Tools &gt; Database Repair cada fin de semana para mantener la latencia en &lt; 15 ms.
                </p>
              </div>
            </div>
          </div>
        )}

        {selectedTech === "RITHMIC" && (
          <div className="space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2 font-sans">
              <h2 className="text-sm font-bold text-[var(--text-1)]">
                Protocolo Rithmic R | Trader Pro: Zero-Mocks Gateway
              </h2>
              <span className="text-xs text-[var(--profit)] font-mono">Chicago CME Direct Feed</span>
            </div>

            <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-4 space-y-2 font-sans">
              <div className="text-xs font-bold text-[var(--text-1)]">Regla de Oro: Order Routing Only</div>
              <p className="text-xs text-[var(--text-2)]">
                Al conectar NinjaTrader con Rithmic, activar la casilla{" "}
                <strong className="text-[var(--profit)]">"Order Routing Only"</strong> para no duplicar el consumo de licencias de datos CME y evitar cuotas de mercado adicionales.
              </p>
              <div className="p-2.5 rounded bg-[var(--bg)] border border-[var(--border)] font-mono text-[11px] text-[var(--text-3)]">
                Servidor Recomendado: <span className="text-[var(--text-1)] font-bold">Chicago CME Area (Aurora Data Center)</span> · Latencia estimada: &lt; 2 ms en VPS.
              </div>
            </div>
          </div>
        )}

        {selectedTech === "TRADOVATE" && (
          <div className="space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2 font-sans">
              <h2 className="text-sm font-bold text-[var(--text-1)]">
                Conectividad Tradovate Cloud & Webhooks
              </h2>
              <span className="text-xs text-[var(--profit)] font-mono">REST & WebSocket API</span>
            </div>

            <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-4 space-y-2 font-sans">
              <div className="text-xs font-bold text-[var(--text-1)]">Operativa Móvil & Copiado Cloud</div>
              <p className="text-xs text-[var(--text-2)]">
                Tradovate permite la sincronización de posiciones tanto en aplicación móvil como en web browser nativo sin necesidad de tener NinjaTrader abierto en segundo plano.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
