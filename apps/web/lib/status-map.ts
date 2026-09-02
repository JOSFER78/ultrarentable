// ÚNICA fuente de verdad para el mapeo estado-API → chip UI.
// La API real (services/api/app/api/strategy_lab_router.py) devuelve
// validation_status sobre este ciclo de vida documentado:
//   EXTRACTED_UNVERIFIED -> SOURCE_RULES_AVAILABLE -> STRUCTURALLY_VERIFIED
//   -> BACKTEST_VERIFIED -> CERTIFIED_CURRENT
// Cualquier valor fuera de este registro cae en UNKNOWN (chip gris neutral),
// nunca en un estado inventado. NO DATA / NO EVIDENCE nunca se traduce a 0.
export type ValidationStatus =
  | "EXTRACTED_UNVERIFIED"
  | "SOURCE_RULES_AVAILABLE"
  | "STRUCTURALLY_VERIFIED"
  | "BACKTEST_VERIFIED"
  | "CERTIFIED_CURRENT"
  | "CERTIFIED_LEGACY"
  | "UNKNOWN";

export const STATUS_ORDER: readonly ValidationStatus[] = [
  "CERTIFIED_CURRENT",
  "CERTIFIED_LEGACY",
  "BACKTEST_VERIFIED",
  "STRUCTURALLY_VERIFIED",
  "SOURCE_RULES_AVAILABLE",
  "EXTRACTED_UNVERIFIED",
] as const;

export const STATUS_LABEL: Record<ValidationStatus, string> = {
  CERTIFIED_CURRENT: "CERTIFICADA ACTUAL",
  CERTIFIED_LEGACY: "CERTIFICADA LEGACY",
  BACKTEST_VERIFIED: "BACKTEST VERIFICADO",
  STRUCTURALLY_VERIFIED: "ESTRUCTURA VERIFICADA",
  SOURCE_RULES_AVAILABLE: "REGLAS DISPONIBLES",
  EXTRACTED_UNVERIFIED: "EXTRAÍDA SIN VERIFICAR",
  UNKNOWN: "ESTADO DESCONOCIDO",
};

// docs/19_UI_STYLE_SPEC.md: los chips de estado NUNCA son multicolor. Verde solo para
// certificada en motor vigente; todo lo demas en gris, con la jerarquia dada por el tono
// del texto, no por el color (2026-09-02, mandato de Emilio: toda la web en grises).
export const STATUS_TONE: Record<ValidationStatus, string> = {
  CERTIFIED_CURRENT: "text-[var(--profit)] border-[var(--profit)] bg-[var(--profit-dim)]",
  CERTIFIED_LEGACY: "text-[var(--text-2)] border-[var(--border-strong)] bg-[var(--surface-2)]",
  BACKTEST_VERIFIED: "text-[var(--text-1)] border-[var(--border-strong)] bg-[var(--surface-2)]",
  STRUCTURALLY_VERIFIED: "text-[var(--text-2)] border-[var(--border)] bg-[var(--surface-1)]",
  SOURCE_RULES_AVAILABLE: "text-[var(--text-2)] border-[var(--border)] bg-[var(--surface-1)]",
  EXTRACTED_UNVERIFIED: "text-[var(--text-3)] border-[var(--border)] bg-[var(--surface-1)]",
  UNKNOWN: "text-[var(--text-3)] border-[var(--border)] bg-[var(--surface-1)]",
};

/** Normaliza cualquier valor crudo de la API a una clave conocida del mapa. */
export function normalizeStatus(raw: string | null | undefined): ValidationStatus {
  if (!raw) return "UNKNOWN";
  const v = String(raw).trim().toUpperCase();
  if ((STATUS_LABEL as Record<string, string>)[v]) return v as ValidationStatus;
  // Compatibilidad: variantes históricas que pueden llegar de la API.
  if (v === "EXTRACTED" || v === "EXTRACTED_UNVERIFIED") return "EXTRACTED_UNVERIFIED";
  return "UNKNOWN";
}

export const statusLabel = (raw: string | null | undefined) => STATUS_LABEL[normalizeStatus(raw)];

export const statusTone = (raw: string | null | undefined) => STATUS_TONE[normalizeStatus(raw)];

/** Orden canónico para ordenar listados; UNKNOWN al final. */
export function statusRank(raw: string | null | undefined): number {
  const s = normalizeStatus(raw);
  const i = (STATUS_ORDER as readonly string[]).indexOf(s);
  return i === -1 ? STATUS_ORDER.length : i;
}
