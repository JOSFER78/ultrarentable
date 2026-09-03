"use client";

import React from "react";
import {
  Compass,
  ShieldCheck,
  TrendingUp,
  Award,
  Users,
  CheckCircle2,
  ExternalLink,
  BookOpen,
  DollarSign,
  Tag,
  Zap,
} from "lucide-react";

export default function EcosistemaTradesferaPage() {
  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <Compass className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Ecosistema Tradesfera: Arquitectura & Modelo de Negocio</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] font-mono">
                Módulo M01
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono mt-0.5">
              Ingeniería cuantitativa para operadores de futuros CME · Fundador: Vicente Pons · Libro Mayor Auditado
            </p>
          </div>
        </div>
      </div>

      {/* Grid de 3 Columnas: Tesis, Fundador y Libro Mayor */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
        {/* Card 1: Fundador */}
        <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-2">
          <span className="text-[10px] text-[var(--text-3)] block uppercase">Fundador & Perfil</span>
          <h2 className="text-sm font-bold text-[var(--text-1)]">Vicente Pons Martínez</h2>
          <p className="text-[11px] text-[var(--text-2)] font-sans leading-relaxed">
            Ingeniero de formación. Aplica optimización matemática, análisis de procesos y control estocástico a futuros regulados del CME Group (MES, MNQ, ES, NQ). Posicionamiento cultural anti-gurú con auditoría pública inmutable.
          </p>
        </div>

        {/* Card 2: Tesis Asimétrica */}
        <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-2">
          <span className="text-[10px] text-[var(--text-3)] block uppercase">Tesis Operativa Central</span>
          <h2 className="text-sm font-bold text-[var(--profit)]">Reversión del Riesgo</h2>
          <p className="text-[11px] text-[var(--text-2)] font-sans leading-relaxed">
            El verdadero riesgo no es el saldo simulado ($50,000 o $150,000), sino el coste marginal de adquisición del examen ($30 - $150). La cuenta de fondeo es un pozo petrolífero de extracción rápida de liquidez con vida útil finita.
          </p>
        </div>

        {/* Card 3: Libro Mayor Público */}
        <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-2">
          <span className="text-[10px] text-[var(--text-3)] block uppercase">Evidencia Física Auditada</span>
          <h2 className="text-sm font-bold text-[var(--text-1)]">167.839 € Cobrados</h2>
          <div className="text-[11px] text-[var(--text-2)] space-y-1 pt-1">
            <div className="flex justify-between border-b border-[var(--border)] pb-1">
              <span>Retiros Certificados:</span>
              <span className="font-bold text-[var(--text-1)]">198 retiros</span>
            </div>
            <div className="flex justify-between border-b border-[var(--border)] pb-1">
              <span>Pass Rate Comprobado:</span>
              <span className="font-bold text-[var(--profit)]">26.6%</span>
            </div>
            <div className="flex justify-between">
              <span>Registro Público:</span>
              <span className="text-[var(--text-3)]">Libro Mayor Inmutable</span>
            </div>
          </div>
        </div>
      </div>

      {/* Las 4 Puertas de Tradesfera */}
      <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-3 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
          <span className="font-bold text-[var(--text-1)] uppercase text-xs">
            Arquitectura de las 4 Puertas del Ecosistema
          </span>
          <span className="text-[10px] text-[var(--text-3)]">Estructura Operativa 2026</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Puerta 1 */}
          <div className="p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded-md space-y-1.5">
            <div className="flex items-center gap-2">
              <Tag className="w-3.5 h-3.5 text-[var(--profit)]" />
              <h3 className="font-bold text-[var(--text-1)]">01. Descuentos</h3>
            </div>
            <p className="text-[11px] text-[var(--text-2)] font-sans leading-relaxed">
              Acuerdos directos con las empresas de futuros para maximizar el descuento (40% a 90% OFF), minimizando el CAPEX de entrada del operador.
            </p>
          </div>

          {/* Puerta 2 */}
          <div className="p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded-md space-y-1.5">
            <div className="flex items-center gap-2">
              <Zap className="w-3.5 h-3.5 text-[var(--profit)]" />
              <h3 className="font-bold text-[var(--text-1)]">02. Recompensas</h3>
            </div>
            <p className="text-[11px] text-[var(--text-2)] font-sans leading-relaxed">
              Sistema de fidelización por "Ticks". Cada cuenta adquirida a través del ecosistema genera créditos canjeables por cuentas gratuitas o herramientas.
            </p>
          </div>

          {/* Puerta 3 */}
          <div className="p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded-md space-y-1.5">
            <div className="flex items-center gap-2">
              <Users className="w-3.5 h-3.5 text-[var(--text-1)]" />
              <h3 className="font-bold text-[var(--text-1)]">03. Comunidad</h3>
            </div>
            <p className="text-[11px] text-[var(--text-2)] font-sans leading-relaxed">
              Canal privado de Telegram blindado contra el ruido, debates de microestructura en tiempo real y alertas de cambios en términos y condiciones.
            </p>
          </div>

          {/* Puerta 4 */}
          <div className="p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded-md space-y-1.5">
            <div className="flex items-center gap-2">
              <BookOpen className="w-3.5 h-3.5 text-[var(--text-1)]" />
              <h3 className="font-bold text-[var(--text-1)]">04. Hub & Software</h3>
            </div>
            <p className="text-[11px] text-[var(--text-2)] font-sans leading-relaxed">
              Sala de trading en vivo 24/7, indicadores institucionales para NinjaTrader 8, plantillas ATM y formación cuantitativa continua.
            </p>
          </div>
        </div>
      </div>

      {/* Alianzas Estratégicas */}
      <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-2 font-mono text-xs">
        <span className="font-bold text-[var(--text-1)] uppercase text-[11px] block">
          Alianzas Estratégicas Verificadas
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          <div className="p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded-md space-y-1">
            <div className="font-bold text-[var(--text-1)]">Gerard García (@GerardGarciafx)</div>
            <p className="text-[11px] text-[var(--text-3)] font-sans">
              Especialista en Hard Scalping en MNQ/NQ, apertura de Nueva York (09:30-11:30 EST), PO3 y manipulación institucional.
            </p>
          </div>
          <div className="p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded-md space-y-1">
            <div className="font-bold text-[var(--text-1)]">El Psicólogo del Trading (@Elpsicologodeltrading)</div>
            <p className="text-[11px] text-[var(--text-3)] font-sans">
              Protocolos de gestión emocional, desensibilización al dinero ficticio y blindaje psicológico frente a rachas perdedoras.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
