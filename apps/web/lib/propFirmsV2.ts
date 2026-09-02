/**
 * Catálogo de Prop Firms V2 — Cliente Tipado Fail-Closed (D6/D7)
 * ZERO-MOCKS · REAL-ONLY · SOURCEREF-PROVENANCE
 */

export type Confidence = "fetch" | "ws_official" | "unverified";

export interface SourceRef {
  confidence: Confidence;
  url: string | null;
  captured_at: string | null;
  note: string;
}

export interface CampoConFuente<T> {
  valor: T | null;
  source: SourceRef;
}

export interface FirmaV2 {
  id: string;
  nombre: string;
  // Parámetros de riesgo
  trailing_dd_tipo: CampoConFuente<string>;
  trailing_dd_valor_50k: CampoConFuente<number>;
  perdida_diaria_limite_50k: CampoConFuente<number>;
  consistencia_pct: CampoConFuente<number>;
  min_dias_trading: CampoConFuente<number>;
  max_micros_50k: CampoConFuente<number>;
  hora_cierre_obligatoria: CampoConFuente<string>;
  // Parámetros económicos
  precio_examen_50k: CampoConFuente<number>;
  coste_activacion_50k: CampoConFuente<number>;
  payout_split_pct: CampoConFuente<number>;
  // Reglas de ejecución / automatización
  vps_permitido: CampoConFuente<boolean>;
}

const BASE_URL = typeof window !== "undefined" ? "" : "http://127.0.0.1:8000";

export async function getPropFirmsV2(): Promise<FirmaV2[]> {
  const endpoint = "/api/v1/prop-firms/v2";
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {}
    throw new Error(`API Request Error (${response.status} ${endpoint}): ${errorDetail}`);
  }

  const text = await response.text();
  if (!text || !text.trim()) {
    throw new Error(`Respuesta vacía de ${endpoint}`);
  }

  try {
    const data = JSON.parse(text);
    if (!Array.isArray(data)) {
      throw new Error(`Estructura inválida de ${endpoint}: se esperaba un array de firmas`);
    }
    return data as FirmaV2[];
  } catch (err: unknown) {
    if (err instanceof Error) {
      throw err;
    }
    throw new Error(`Error al procesar JSON de ${endpoint}`);
  }
}

export async function getPropFirmV2ById(firmId: string): Promise<FirmaV2> {
  const endpoint = `/api/v1/prop-firms/v2/${encodeURIComponent(firmId)}`;
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {}
    throw new Error(`API Request Error (${response.status} ${endpoint}): ${errorDetail}`);
  }

  const text = await response.text();
  if (!text || !text.trim()) {
    throw new Error(`Respuesta vacía de ${endpoint}`);
  }

  try {
    const data = JSON.parse(text);
    if (!data || typeof data !== "object" || !("id" in data)) {
      throw new Error(`Estructura inválida de ${endpoint}`);
    }
    return data as FirmaV2;
  } catch (err: unknown) {
    if (err instanceof Error) {
      throw err;
    }
    throw new Error(`Error al procesar JSON de ${endpoint}`);
  }
}
