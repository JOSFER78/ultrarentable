/**
 * apps/web/hooks/useAPI.ts
 * Hook universal de consumo de APIs REST físicas con tipado estricto y Zero Mocks.
 */
"use client";

import { useState, useEffect, useCallback } from "react";

export interface UseAPIOptions<T> extends RequestInit {
  initialData?: T;
  skip?: boolean;
}

export interface UseAPIResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useAPI<T = unknown>(
  endpoint: string | null,
  options: UseAPIOptions<T> = {}
): UseAPIResult<T> {
  const { initialData = null, skip = false, ...fetchOptions } = options;
  const [data, setData] = useState<T | null>(initialData);
  const [loading, setLoading] = useState<boolean>(!skip && Boolean(endpoint));
  const [error, setError] = useState<string | null>(null);

  const executeFetch = useCallback(async () => {
    if (!endpoint || skip) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(endpoint, {
        ...fetchOptions,
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          ...(fetchOptions.headers || {}),
        },
      });

      if (!res.ok) {
        let errDetail = res.statusText;
        try {
          const json = await res.json();
          errDetail = json.detail || json.message || JSON.stringify(json);
        } catch {
          // ignore non-json error responses
        }
        throw new Error(`HTTP ${res.status} (${endpoint}): ${errDetail}`);
      }

      const parsed: T = await res.json();
      setData(parsed);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error de comunicación con el backend.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [endpoint, skip]);

  useEffect(() => {
    executeFetch();
  }, [executeFetch]);

  return {
    data,
    loading,
    error,
    refetch: executeFetch,
  };
}
