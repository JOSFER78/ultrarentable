"use client";

import { useState, useEffect, useCallback } from "react";

interface UseAPIResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useAPI<T>(url: string | null): UseAPIResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(!!url);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    if (!url) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(url, { cache: "no-store" })
      .then(async (res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      })
      .then((json) => {
        if (!cancelled) {
          setData(json);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [url, tick]);

  return { data, loading, error, refetch };
}

interface UseApiMutatorResult<T, Payload = any> {
  mutate: (payload?: Payload) => Promise<T>;
  loading: boolean;
  error: string | null;
  data: T | null;
}

export function useApiMutator<T, Payload = any>(
  url: string,
  method: "POST" | "PUT" | "DELETE" | "PATCH" = "POST"
): UseApiMutatorResult<T, Payload> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mutate = useCallback(
    async (payload?: Payload) => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(url, {
          method,
          headers: {
            "Content-Type": "application/json",
          },
          body: payload ? JSON.stringify(payload) : undefined,
        });

        if (!res.ok) {
          let errText = await res.text();
          try {
            const errJson = JSON.parse(errText);
            errText = errJson.detail?.message || errJson.detail || errJson.message || errText;
          } catch {}
          throw new Error(errText || `${res.status} ${res.statusText}`);
        }

        const json = await res.json();
        setData(json);
        setLoading(false);
        return json;
      } catch (err: any) {
        setError(err.message);
        setLoading(false);
        throw err;
      }
    },
    [url, method]
  );

  return { mutate, loading, error, data };
}

/* ── BingX specific ── */
export function useBingX<T>(endpoint: string, params?: Record<string, string>) {
  const qs = new URLSearchParams({ endpoint, ...params }).toString();
  return useAPI<T>(`/api/bingx?${qs}`);
}
