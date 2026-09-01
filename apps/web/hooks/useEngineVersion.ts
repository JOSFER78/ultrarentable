/**
 * apps/web/hooks/useEngineVersion.ts
 * Versión REAL del motor, leída de la API canónica (nunca hardcodeada, nunca con valor
 * por defecto numérico). Reescrito 2026-09-01 (AG-11, T3 — W5.4: "la versión del motor deja
 * de mentir"). Fuente única: getDiscoveryStatus().current_engine_version (lib/api.ts).
 *
 * Si la API no responde, `version` queda en `null` y `error` describe el fallo: la UI debe
 * mostrar "MOTOR: NO DISPONIBLE" en gris, JAMÁS un número de versión por defecto — esa es la
 * violación REAL-ONLY (el badge de versión fija que este hook sustituye) que había hardcodeada.
 */
"use client";

import { useState, useEffect, useCallback } from "react";
import { getDiscoveryStatus } from "@/lib/api";

export interface EngineVersionInfo {
  /** Versión real reportada por la API, o null si aún no se cargó / falló la conexión. */
  version: string | null;
  loading: boolean;
  /** Mensaje de fallo legible, o null si la última carga fue correcta. */
  error: string | null;
  refetch: () => Promise<void>;
}

export function useEngineVersion(): EngineVersionInfo {
  const [version, setVersion] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchVersion = useCallback(async () => {
    setLoading(true);
    try {
      const status = await getDiscoveryStatus();
      if (status?.current_engine_version) {
        setVersion(status.current_engine_version);
        setError(null);
      } else {
        setVersion(null);
        setError("La API de discovery no reportó current_engine_version.");
      }
    } catch (err: unknown) {
      setVersion(null);
      setError(err instanceof Error ? err.message : "Sin conexión con la API canónica.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchVersion();
  }, [fetchVersion]);

  return { version, loading, error, refetch: fetchVersion };
}
