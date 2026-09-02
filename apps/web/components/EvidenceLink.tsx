"use client";

import React from "react";
import { ShieldCheck } from "lucide-react";

export interface EvidenceLinkProps {
  strategyHash?: string | null;
  datasetHash?: string | null;
  engineVersion?: string | null;
  commitSha?: string | null;
  children?: React.ReactNode;
}

/**
 * Tooltip de provenance (contrato 03_CONTRATOS/evidence_link.schema.json).
 * Solo renderiza valores entregados por el backend; campo ausente = NO EVIDENCE.
 * No genera ni deriva ningun valor (REAL-ONLY / EVIDENCE-GATED).
 */
export default function EvidenceLink({ strategyHash, datasetHash, engineVersion, commitSha, children }: EvidenceLinkProps) {
  const rows: Array<[string, string | null | undefined]> = [
    ["strategy_hash", strategyHash],
    ["dataset_hash", datasetHash],
    ["engine_version", engineVersion],
    ["commit_sha", commitSha],
  ];

  const presentCount = rows.filter(([, value]) => typeof value === "string" && value.trim() !== "").length;

  return (
    <span className="group relative inline-flex items-center gap-1">
      {children}
      <span
        className={`inline-flex items-center gap-0.5 rounded border px-1 py-0.5 text-[9px] font-mono leading-none ${
          presentCount > 0
            ? "border-[var(--profit)] bg-[var(--profit-dim)] text-[var(--profit)]"
            : "border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-3)]"
        }`}
      >
        <ShieldCheck className="h-2.5 w-2.5" />
        EV
      </span>

      <span className="pointer-events-none absolute bottom-full left-0 z-30 mb-2 hidden w-72 rounded-lg border border-[var(--border)] bg-[var(--surface-1)] p-3 shadow-2xl group-hover:block">
        <span className="mb-2 block text-[10px] font-bold uppercase tracking-wider text-[var(--text-2)]">
          evidence_link · provenance
        </span>
        {rows.map(([label, value]) => {
          const has = typeof value === "string" && value.trim() !== "";
          return (
            <span key={label} className="mb-1 block font-mono text-[10px] leading-snug">
              <span className="text-[var(--text-3)]">{label}: </span>
              {has ? (
                <span className="break-all text-[var(--text-1)]">{value}</span>
              ) : (
                <span className="font-bold text-[var(--text-2)]">NO EVIDENCE</span>
              )}
            </span>
          );
        })}
        <span className="mt-1 block text-[9px] leading-snug text-[var(--text-3)]">
          commit_sha no lo entrega el backend hoy: nunca se fabrica.
        </span>
      </span>
    </span>
  );
}
