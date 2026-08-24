import { BacktestRequest, BacktestResult } from "@/types/backtest";

// Base URL del API. La web Next.js (puerto 3000) proxea /api/* -> 127.0.0.1:8000
const API_PORT = process.env.NEXT_PUBLIC_API_PORT || "8000";
const explicitUrl = process.env.NEXT_PUBLIC_API_URL;

export function getApiUrl(endpoint: string): string {
  const clean = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  if (explicitUrl) return `${explicitUrl.replace(/\/$/, "")}${clean}`;
  if (typeof window === "undefined") {
    return `http://127.0.0.1:${API_PORT}${clean}`;
  }
  if (window.location.pathname.startsWith("/pro/ultrarentable")) {
    return `/pro/ultrarentable${clean}`;
  }
  return clean;
}

export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = getApiUrl(endpoint);
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let errorDetail = "SERVICE_UNAVAILABLE";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail?.message || errJson.detail || JSON.stringify(errJson);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail || `HTTP_${response.status}`);
  }

  return response.json();
}

export const api = {
  // ── Version & System ──
  getVersion: () => request<any>("/api/v1/version"),
  getVersions: () => request<any>("/api/v1/versions"),

  // ── Autopilot (proceso de búsqueda en vivo) ──
  getAutopilotStatus: () => request<any>("/api/v1/autopilot/status"),
  getAutopilotDecisions: () => request<any[]>("/api/v1/autopilot/decisions"),
  startAutopilot: () => request<any>("/api/v1/autopilot/start", { method: "POST", body: JSON.stringify({}) }),
  pauseAutopilot: () => request<any>("/api/v1/autopilot/pause", { method: "POST", body: JSON.stringify({}) }),
  resumeAutopilot: () => request<any>("/api/v1/autopilot/resume", { method: "POST", body: JSON.stringify({}) }),
  stopAutopilot: () => request<any>("/api/v1/autopilot/stop", { method: "POST", body: JSON.stringify({}) }),

  // ── Ingestion & Datasets ──
  getContracts: () => request<any[]>("/api/v1/ingestion/contracts"),
  getDatasets: () => request<any[]>("/api/v1/datasets"),
  prepareEthResearch: (days = 160) =>
    request<any>(`/api/v1/ingestion/eth-research?days=${days}`, { method: "POST" }),
  approveDataset: (id: string) => request<any>(`/api/v1/datasets/${id}/approve`, { method: "POST" }),
  rejectDataset: (id: string) => request<any>(`/api/v1/datasets/${id}/reject`, { method: "POST" }),

  // ── Strategies ──
  getStrategies: () => request<any[]>("/api/v1/strategies"),
  getStrategy: (id: string) => request<any>(`/api/v1/strategies/${id}`),

  // ── Backtesting ──
  getBacktests: () => request<any[]>("/api/v1/backtests"),
  getBacktest: (id: string) => request<any>(`/api/v1/backtests/${id}`),
  getBacktestTrades: (id: string) => request<any[]>(`/api/v1/backtests/${id}/trades`),
  runFastBacktest: (strategyId: string, datasetId: string, initialCapital: number) =>
    request<any>("/api/v1/backtests/fast", {
      method: "POST",
      body: JSON.stringify({ strategyId, datasetId, initialCapital }),
    }),
  executeBacktest: (payload: BacktestRequest) =>
    request<BacktestResult>("/api/v1/backtest", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // ── Campaigns ──
  getCampaigns: () => request<any[]>("/api/v1/campaigns"),
  createAutonomousCampaign: (payload: any) =>
    request<any>("/api/v1/campaigns/autonomous", { method: "POST", body: JSON.stringify(payload) }),
  startCampaign: (id: string) => request<any>(`/api/v1/campaigns/${id}/start`, { method: "POST" }),

  // ── Leaderboard ──
  getLeaderboard: () => request<any[]>("/api/v1/leaderboard"),

  // ── Research ──
  getResearch: () => request<any[]>("/api/v1/research"),
  createResearch: (payload: any) => request<any>("/api/v1/research", { method: "POST", body: JSON.stringify(payload) }),

  // ── StrategyQuant X MCP (núcleo de búsqueda de estrategias) ──
  getSQXStatus: () => request<any>("/api/v1/sqx/status"),
  getSQXTools: () => request<any>("/api/v1/sqx/tools"),
  getSQXProjects: () => request<any>("/api/v1/sqx/projects"),
  getSQXDatabanks: (projectName: string) =>
    request<any>(`/api/v1/sqx/projects/${encodeURIComponent(projectName)}/databanks`),
  getSQXStrategies: (projectName: string, databankName: string) =>
    request<any>(`/api/v1/sqx/projects/${encodeURIComponent(projectName)}/databanks/${encodeURIComponent(databankName)}/strategies`),
  getSQXStrategyStats: (projectName: string, databankName: string, strategyName: string) =>
    request<any>(`/api/v1/sqx/projects/${encodeURIComponent(projectName)}/databanks/${encodeURIComponent(databankName)}/strategies/${encodeURIComponent(strategyName)}`),
  runSQXProject: (projectName: string) =>
    request<any>(`/api/v1/sqx/projects/${encodeURIComponent(projectName)}/run`, { method: "POST", body: JSON.stringify({}) }),
  stopSQXProject: (projectName: string) =>
    request<any>(`/api/v1/sqx/projects/${encodeURIComponent(projectName)}/stop`, { method: "POST", body: JSON.stringify({}) }),
  ingestSQXProject: (projectName: string) =>
    request<any>(`/api/v1/sqx/projects/${encodeURIComponent(projectName)}/ingest`, { method: "POST", body: JSON.stringify({}) }),
  getSQXRentable: (limit = 10, mode = "ultra") =>
    request<any>(`/api/v1/sqx/rentable?limit=${limit}&mode=${encodeURIComponent(mode)}`),
  getSQXCandidates: (mode = "ultra") =>
    request<any[]>(`/api/v1/autopilot/candidates?mode=${encodeURIComponent(mode)}`),

  // ── Search Configurator ──
  listSearchConfigs: () => request<any[]>("/api/v1/search-configs"),
  createSearchConfig: (payload: any) =>
    request<any>("/api/v1/search-configs", { method: "POST", body: JSON.stringify(payload) }),
  runSearchConfig: (configId: string) =>
    request<any>(`/api/v1/search-configs/${encodeURIComponent(configId)}/run`, { method: "POST", body: JSON.stringify({}) }),

  // ── Execution Sessions ──
  getExecutionSessions: () => request<any[]>("/api/v1/execution/sessions"),
};
