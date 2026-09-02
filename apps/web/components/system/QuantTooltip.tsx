"use client";

import React, { useState, useRef, useEffect, ReactNode } from "react";
import { HelpCircle, Info, CheckCircle2 } from "lucide-react";
import { QUANT_GLOSSARY, GlossaryTerm } from "@/lib/glossary";

export interface QuantTooltipProps {
  term?: string;
  text?: string;
  title?: string;
  benchmark?: string;
  formula?: string;
  position?: "top" | "bottom" | "left" | "right" | "auto";
  children?: ReactNode;
  variant?: "indigo" | "emerald" | "rose" | "sky" | "amber" | "slate";
  iconSize?: number;
  className?: string;
}

export default function QuantTooltip({
  term,
  text,
  title,
  benchmark,
  formula,
  position = "top",
  children,
  variant,
  iconSize = 14,
  className = "",
}: QuantTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [coords, setCoords] = useState<{ x: number; y: number; actualPos: string }>({
    x: 0,
    y: 0,
    actualPos: position,
  });

  const triggerRef = useRef<HTMLSpanElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const normalizedKey = term ? term.toLowerCase().replace(/[\s\-_()]+/g, "_").replace(/^_+|_+$/g, "") : "";
  const dictionaryEntry: GlossaryTerm | undefined = QUANT_GLOSSARY[normalizedKey] || (term ? QUANT_GLOSSARY[term] : undefined);

  const displayTitle = title || dictionaryEntry?.title || term;
  const displayText = text || dictionaryEntry?.whatIs || "Definición técnica cuantitativa.";
  const displayBenchmark = benchmark || dictionaryEntry?.benchmark;
  const displayFormula = formula || dictionaryEntry?.formula;
  const finalVariant = variant || dictionaryEntry?.colorScheme || "indigo";

  const variantStyles = {
    indigo: {
      accentGlow: "shadow-[0_8px_30px_rgba(255,255,255,0.06)]",
      iconColor: "text-[var(--text-2)] hover:text-[var(--text-1)]",
      borderColor: "border-[var(--border)]",
      pillBg: "bg-[var(--surface-2)] text-[var(--text-1)] border-[var(--border)]",
    },
    emerald: {
      accentGlow: "shadow-[0_8px_30px_rgba(255,255,255,0.06)]",
      iconColor: "text-[var(--profit)] hover:text-[var(--profit)]",
      borderColor: "border-[var(--profit)]",
      pillBg: "bg-[var(--profit-dim)] text-[var(--profit)] border-[var(--profit)]",
    },
    rose: {
      accentGlow: "shadow-[0_8px_30px_rgba(255,255,255,0.06)]",
      iconColor: "text-[var(--loss)] hover:text-[var(--loss)]",
      borderColor: "border-[var(--loss)]",
      pillBg: "bg-[var(--loss-dim)] text-[var(--loss)] border-[var(--loss)]",
    },
    sky: {
      accentGlow: "shadow-[0_8px_30px_rgba(255,255,255,0.06)]",
      iconColor: "text-[var(--text-2)] hover:text-[var(--text-1)]",
      borderColor: "border-[var(--border)]",
      pillBg: "bg-[var(--surface-2)] text-[var(--text-1)] border-[var(--border)]",
    },
    amber: {
      accentGlow: "shadow-[0_8px_30px_rgba(255,255,255,0.06)]",
      iconColor: "text-[var(--text-2)] hover:text-[var(--text-1)]",
      borderColor: "border-[var(--border)]",
      pillBg: "bg-[var(--surface-2)] text-[var(--text-1)] border-[var(--border)]",
    },
    slate: {
      accentGlow: "shadow-[0_8px_30px_rgba(0,0,0,0.4)]",
      iconColor: "text-[var(--text-2)] hover:text-[var(--text-1)]",
      borderColor: "border-[var(--border)]",
      pillBg: "bg-[var(--surface-1)] text-[var(--text-1)] border-[var(--border)]",
    },
  }[finalVariant];

  const handleMouseEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, 100);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setIsVisible(false);
    }, 120);
  };

  useEffect(() => {
    if (isVisible && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      const tooltipWidth = 300;
      let calculatedPos = position;
      let top = 0;
      let left = rect.left + rect.width / 2;

      if (position === "top" || position === "auto") {
        if (rect.top < 180) {
          calculatedPos = "bottom";
          top = rect.bottom + 8;
        } else {
          calculatedPos = "top";
          top = rect.top - 8;
        }
      } else if (position === "bottom") {
        top = rect.bottom + 8;
      }

      if (left - tooltipWidth / 2 < 12) {
        left = 12 + tooltipWidth / 2;
      } else if (left + tooltipWidth / 2 > window.innerWidth - 12) {
        left = window.innerWidth - 12 - tooltipWidth / 2;
      }

      setCoords({ x: left, y: top, actualPos: calculatedPos });
    }
  }, [isVisible, position]);

  return (
    <span
      ref={triggerRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocus={handleMouseEnter}
      onBlur={handleMouseLeave}
      tabIndex={0}
      role="button"
      aria-label={`Información sobre ${displayTitle || "término"}`}
      aria-expanded={isVisible}
      className={`inline-flex items-center gap-1 cursor-help outline-none transition-colors duration-150 ${className}`}
    >
      {children ? (
        <>
          {children}
          <HelpCircle
            style={{ width: iconSize, height: iconSize }}
            className={`inline-block ml-0.5 transition-transform duration-200 ${variantStyles.iconColor} ${
              isVisible ? "scale-110" : "opacity-75"
            }`}
          />
        </>
      ) : (
        <span className="p-0.5 rounded-full hover:bg-[var(--surface-1)] transition">
          <HelpCircle
            style={{ width: iconSize, height: iconSize }}
            className={`transition-all duration-200 ${variantStyles.iconColor} ${
              isVisible ? "scale-110 opacity-100" : "opacity-70"
            }`}
          />
        </span>
      )}

      {isVisible && (
        <div
          ref={tooltipRef}
          role="tooltip"
          style={{
            position: "fixed",
            left: `${coords.x}px`,
            top: `${coords.y}px`,
            transform: coords.actualPos === "top" ? "translate(-50%, -100%)" : "translate(-50%, 0)",
            zIndex: 9999,
          }}
          className={`w-72 max-w-[calc(100vw-24px)] p-3 rounded-xl border ${variantStyles.borderColor} ${variantStyles.accentGlow} bg-[var(--surface-1)] backdrop-blur-xl text-[var(--text-1)] text-xs shadow-2xl animate-in fade-in zoom-in-95 duration-150 pointer-events-auto`}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-white/10">
            <div className="flex items-center gap-1.5 font-bold tracking-wide text-[var(--text-1)] text-xs">
              <Info className="w-3.5 h-3.5 text-[var(--text-2)]" />
              <span>{displayTitle}</span>
            </div>
            {dictionaryEntry?.category && (
              <span className="text-[9px] uppercase font-mono px-1.5 py-0.5 rounded bg-[var(--surface-1)] text-[var(--text-2)] border border-[var(--border)]">
                {dictionaryEntry.category}
              </span>
            )}
          </div>

          <div className="space-y-1.5 text-[var(--text-1)] leading-relaxed text-[11px]">
            <p>{displayText}</p>
            {displayBenchmark && (
              <div className={`p-1.5 rounded-lg border flex items-start gap-1.5 ${variantStyles.pillBg}`}>
                <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-semibold block text-[10px] text-[var(--text-1)]">Objetivo Óptimo:</span>
                  <span className="text-[10px] opacity-90">{displayBenchmark}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </span>
  );
}