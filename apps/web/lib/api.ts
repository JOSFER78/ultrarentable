/**
 * Ultrarentable v5.3.0 Canonical API Client
 * ZERO-MOCK · REAL-ONLY · PROVENANCE-LOCKED
 */
export interface BacktestParams { strategy_id: string; symbol: string; timeframe: string; dataset_id?: string; initial_capital?: number; slippage_ticks?: number; commission_per_order?: number; start_timestamp_utc_ms?: number; end_timestamp_utc_ms?: number; ast?: Record<string, unknown>; parameters?: Record<string, unknown>; }
export interface TradeRecord { trade_id: string; entry_timestamp_ms: number; exit_timestamp_ms: number; side: "BUY" | "SELL"; entry_price: number; exit_price: number; quantity: number; pnl_gross: number; commission: number; slippage: number; pnl_net: number; exit_reason: string; is_out_of_sample: boolean; }
export interface BacktestResult { run_id: string; strategy_id: string; strategy_hash: string; dataset_hash: string; execution_config_hash: string; ledger_hash: string; evidence_bundle_hash: string; engine_version: string; execution_time_ms: number; total_trades: number; winning_trades: number; losing_trades: number; win_rate_pct: number; profit_factor: number; sharpe_ratio: number; sortino_ratio: number; max_drawdown_pct: number; max_drawdown_usd: number; total_net_pnl: number; initial_capital: number; final_equity: number; oos_trades: number; oos_profit_factor: number; oos_win_rate_pct: number; oos_max_drawdown_pct: number; oos_start_timestamp_ms: number | null; oos_end_timestamp_ms: number | null; oos_days: number | null; oos_months: number | null; monthly_return: number | null; annual_return: number | null; cagr: number | null; equity_curve: Array<{ timestamp_ms: number; equity: number; drawdown_pct: number }>; trades: TradeRecord[]; }
export interface GateVerificationDetail { gate_id?: string; name?: string; gate_name?: string; passed: boolean; threshold_value?: string | number; observed_value?: string | number; metric_value?: string | number; score?: number; details?: string; evidence_path?: string; evidence_hash?: string; }
export interface CertifiedStrategy { strategy_id: string; name: string; symbol: string; timeframe: string; family: string; route?: string; wfo_pass_pct?: number; status: string; engine_version: string; strategy_hash: string; dataset_hash: string; ledger_hash: string; evidence_bundle_hash: string; all_gates_pass: boolean; ledger_verified: boolean; total_trades: number; win_rate_pct: number; profit_factor: number; sharpe_ratio: any; max_drawdown_pct: number; oos_profit_factor: number; oos_start_timestamp_ms: number | null; oos_end_timestamp_ms: number | null; oos_months: number | null; monthly_return: number | null; annual_return: number | null; cagr: number | null; certified_at_utc: string; gates: Record<string, GateVerificationDetail>; equity_curve: Array<{ timestamp_ms: number; equity: number; drawdown_pct: number }>; }
export interface PortfolioComponent { strategy_id: string; name: string; symbol: string; timeframe: string; weight: number; engine_version: string; status: "APPROVED_CURRENT_ENGINE" | "APPROVED_LEGACY" | "REVALIDATION_REQUIRED" | "ANOMALY_REVIEW"; strategy_hash: string; ledger_hash: string; }
export interface CertifiedMetaStrategy { meta_strategy_id: string; name: string; engine_version: string; portfolio_hash: string; combined_ledger_hash: string; status: "APPROVED_CURRENT_ENGINE" | "APPROVED_LEGACY" | "REVALIDATION_REQUIRED"; all_components_approved_current: boolean; correlation_matrix_verified: boolean; components: PortfolioComponent[]; combined_profit_factor: number; combined_sharpe_ratio: number; combined_max_drawdown_pct: number; combined_cagr: number | null; combined_annual_return: number | null; monthly_return?: number | null; route?: string; target_route?: string; portfolio_ledger_verified: boolean; certified_at_utc: string; equity_curve: Array<{ timestamp_ms: number; equity: number; drawdown_pct: number }>; }
export interface CandidateStrategy { id: string; name: string; symbol: string; timeframe: string; family: string; engine_version: string; status: string; profit_factor: number; sharpe_ratio: number; max_drawdown_pct: number; win_rate_pct: number; total_trades: number; oos_profit_factor: number; oos_months: number | null; monthly_return: number | null; annual_return: number | null; cagr: number | null; strategy_hash?: string; dataset_hash?: string; ledger_hash?: string; }
/**
 * Catálogo CANÓNICO de candidatas (tabla `candidates` de la base real).
 * Verificado el 2026-08-31 contra la BD: 578 filas, misma distribución de estados en API y SQLite.
 * Es la fuente de verdad del producto, distinta de /api/v2/strategy-lab (extracciones crudas de SQX).
 */
export interface CandidatoCanonico {
  candidate_id: string;
  name: string;
  route: string;
  symbol: string;
  timeframe: string;
  status: string;
  status_reason?: string | null;
  tier?: string | null;
  tier_label?: string | null;
  gates_passed_count?: number | null;
  market_category?: string | null;
  icon?: string | null;
  prop_firm_eligible?: boolean | null;
  prop_firm_venues?: string | null;
  archetype?: string | null;
  strategy_sha256?: string | null;
  dataset_id?: string | null;
  profit_factor_oos?: number | null;
  max_dd_oos_pct?: number | null;
  net_profit_oos?: number | null;
  trades_oos?: number | null;
  win_rate_pct?: number | null;
  created_at?: string | null;
  /** Metricas del backtest canonico.
   *
   *  `roi_source` dice de donde salen `monthly_roi_pct` / `annualized_roi_pct`:
   *  "SCORECARD" = los declara el scorecard de la candidata (cifras en USD del motor);
   *  "NO_EVIDENCE" = no hay ROI declarado y los dos campos vienen a null. NO se derivan de
   *  `net_profit_usd`, porque la columna `candidates.net_profit_oos` de la que sale tiene
   *  unidades mixtas segun que pipeline la escribiera (unas filas en USD, otras como suma de
   *  fracciones), y derivarlo daba cifras falsas e incluso con el signo cambiado.
   *
   *  `oos_months_source` es independiente: dice si la duracion OOS es REAL o ESTIMADO. */
  metrics?: {
    out_of_sample?: {
      roi_pct?: number | null;
      monthly_roi_pct?: number | null;
      annualized_roi_pct?: number | null;
      roi_source?: "SCORECARD" | "NO_EVIDENCE" | null;
      oos_months?: number | null;
      oos_months_source?: "REAL" | "ESTIMADO" | null;
    } | null;
  } | null;
}

export async function getCandidatosCanonicos(limit = 1000): Promise<CandidatoCanonico[]> {
  const r = await fetchJson<CandidatoCanonico[] | { candidates: CandidatoCanonico[] }>(
    `/api/v1/candidates?limit=${encodeURIComponent(limit)}&include_rejected=true`
  );
  return Array.isArray(r) ? r : r.candidates ?? [];
}

export interface DiscoveryStatus { status: string; active_workers: number; total_trials: number; sqx_bridge_connected: boolean; telemetry_active: boolean; current_engine_version: string; }
export interface StrategyLabOverview { status: string; as_of_utc: string; pipeline: { extracted: number; structurally_verified: number; backtest_verified: number; certified_current: number; approved_datasets: number; }; evidence_policy: string; }
export interface StrategyLabRecord { strategy_id: string; name: string; strategy_version: string; strategy_hash: string; validation_status: string; source_engine: string | null; source_project: string | null; source_databank: string | null; source_strategy_name: string | null; symbol: string | null; timeframe: string | null; dataset_id: string | null; dataset_hash: string | null; source_artifact_sha256?: string | null; source_payload?: unknown; raw_stats: Record<string, unknown>; created_at: string | null; }
export interface StrategyLabListResponse { status: string; count: number; strategies: StrategyLabRecord[]; }
export interface StrategyLabSQXStatus { status: string; source: string; result?: unknown; error?: string; }
export interface StrategyLabExtractionResult { status: string; project: string; databank: string; found: number; named?: number; inserted: number; unchanged: number; quarantined: number; next_step: string; }
export interface ApprovedDataset { datasetId: string; symbol: string; interval: string; recordCount: number; status: string; venue: string; startTime?: number; endTime?: number; gapCount?: number; }
export interface LegacyStrategy { strategyId: string; name: string; [key: string]: unknown; }
export interface LegacyBacktestResult { backtestId: string; strategyId: string; datasetId: string; engineType: string; initialCapital: number; leverage: number; finalEquity: number; netReturnPct: number; maxDrawdownPct: number; winRate: number; tradesCount: number; profitFactor: number; checksum: string; status: string; createdAt: string; }
export interface Campaign { campaignId: string; name: string; symbol: string; interval: string; populationSize: number; generationsCount: number; currentGeneration: number; seed: number; status: string; mode?: string; targetMultiplier?: number; createdAt: string; }
export interface CampaignCreateResponse extends Campaign { message?: string; }
export interface LeaderboardItem { rank: number; backtestId: string; strategyId: string; engine: string; returnPct: number; maxDrawdownPct: number; winRate: number; tradesCount: number; profitFactor: number; checksum: string; date: string; }
export interface SQXProject { name: string; }
export interface SQXStatus { status: string; base_url?: string; session_id?: string; server_info?: { name: string; version: string }; error?: string; }
export interface SQXDatabank { name: string; [key: string]: unknown; }
export interface PrepareEthResponse { datasets: unknown[]; sourcePages: number; [key: string]: unknown; }

export interface PiezaSaludM1 {
  descripcion?: string;
  ok: boolean;
  detalle: string;
}

export interface SaludM1Response {
  schema?: string;
  medido?: string;
  todo_en_pie: boolean;
  piezas: Record<string, PiezaSaludM1>;
  ultimas_acciones?: Array<{ cuando: string; que: string; rc: number }>;
  disponible?: boolean;
  origen?: string;
}

const BASE_URL = typeof window !== "undefined" ? "" : (process.env.BACKEND_URL || process.env.ULTRARENTABLE_API_URL || "http://127.0.0.1:8000");

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

async function fetchJson<T>(endpoint: string, options: RequestInit = {}, maxRetries = 2): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          ...(options.headers || {})
        }
      });

      if (!response.ok) {
        let errorDetail = response.statusText;
        try {
          const errJson = await response.json();
          errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
        } catch {}
        throw new Error(`El servicio no responde correctamente (${response.status}): ${errorDetail}`);
      }

      const text = await response.text();
      if (!text || !text.trim()) {
        throw new Error(`Respuesta vacía o JSON inválido de ${endpoint}`);
      }

      return JSON.parse(text) as T;
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
      if (attempt < maxRetries) {
        await sleep(350 * Math.pow(2, attempt));
      }
    }
  }

  throw lastError || new Error(`El servicio no responde ahora mismo. Se está reintentando solo.`);
}

export async function getM1Salud(): Promise<SaludM1Response> {
  return fetchJson<SaludM1Response>("/api/v2/m1/salud");
}

export interface VigiaLocalResponse {
  disponible: boolean;
  motivo?: string;
  schema?: string;
  medido?: string;
  worktree?: string;
  api?: {
    puerto: number;
    http: number;
    ok: boolean;
  };
  web?: {
    puerto: number;
    http: number;
    ok: boolean;
  };
  build_integro?: boolean;
  acciones?: string[];
  todo_en_pie?: boolean;
}

export async function getVigiaLocal(): Promise<VigiaLocalResponse> {
  return fetchJson<VigiaLocalResponse>("/api/v2/system/vigia-local");
}

export interface CeldaRejillaM1 {
  celda: string;
  simbolo: string;
  contrato_grande?: string | null;
  nombre: string;
  tf: string;
  tf_etiqueta: string;
  proyecto: string;
  proyecto_en_sqx: boolean;
  datos?: {
    tf_base: string;
    desde: string;
    hasta: string;
    dias: number;
    velas_base: number;
  } | null;
  estado: "SIN_EMPEZAR" | "PENDIENTE" | "EN_CURSO" | "HECHA" | string;
  rondas_hechas?: number;
  generadas?: number | null;
  en_banco?: number | null;
  por_hora?: string | number | null;
  aceptado_pct?: string | number | null;
  tiempo?: string | null;
  csv_filas?: number | null;
  csv_sha256?: string | null;
  costes?: {
    spread?: number;
    slippage?: number;
    comision?: number;
  } | null;
}

export interface RejillaM1Response {
  schema?: string;
  medido?: string;
  disponible: boolean;
  motivo_no_disponible?: string;
  bucle?: {
    activo: boolean;
    celda_en_curso: string | null;
    ronda: number;
    horas_por_celda: number;
  };
  resumen?: {
    celdas: number;
    con_datos: number;
    con_proyecto: number;
    con_al_menos_una_ronda: number;
    estrategias_en_bancos: number;
  };
  celdas: CeldaRejillaM1[];
  origen?: string;
}

export async function getM1Rejilla(): Promise<RejillaM1Response> {
  return fetchJson<RejillaM1Response>("/api/v2/m1/rejilla");
}

export interface IAProveedorConfig {
  configurado: boolean;
  nombre: string;
  endpoint: string;
  modelo: string;
  tiene_clave: boolean;
  origen_almacenamiento?: string;
}

export interface IAProveedorGuardar {
  nombre: string;
  endpoint: string;
  modelo: string;
  api_key?: string;
}

export interface IAProbarResultado {
  ok: boolean;
  status_code: number;
  detalle: string;
}

export interface IACompletarRespuesta {
  respuesta: string;
  modelo: string;
  proveedor: string;
}

export async function getIAProveedor(): Promise<IAProveedorConfig> {
  return fetchJson<IAProveedorConfig>("/api/v2/ia/proveedor");
}

export async function saveIAProveedor(config: IAProveedorGuardar): Promise<IAProveedorConfig> {
  return fetchJson<IAProveedorConfig>("/api/v2/ia/proveedor", {
    method: "POST",
    body: JSON.stringify(config),
  });
}

export async function probarIAProveedor(): Promise<IAProbarResultado> {
  return fetchJson<IAProbarResultado>("/api/v2/ia/probar", {
    method: "POST",
  });
}

export async function completarIA(prompt: string): Promise<IACompletarRespuesta> {
  return fetchJson<IACompletarRespuesta>("/api/v2/ia/completar", {
    method: "POST",
    body: JSON.stringify({ prompt }),
  });
}

export async function executeBacktest(params: BacktestParams): Promise<BacktestResult> { if (!params.dataset_id?.trim()) throw new Error("REAL_ONLY_DATASET_REQUIRED: executeBacktest requires an existing canonical dataset_id"); const payload: Record<string, unknown> = { strategy_id: params.strategy_id, dataset_id: params.dataset_id }; if (params.initial_capital !== undefined) payload.initial_capital = params.initial_capital; if (params.slippage_ticks !== undefined) payload.slippage_ticks = params.slippage_ticks; if (params.commission_per_order !== undefined) payload.commission_per_order = params.commission_per_order; if (params.start_timestamp_utc_ms !== undefined) payload.start_timestamp_utc_ms = params.start_timestamp_utc_ms; if (params.end_timestamp_utc_ms !== undefined) payload.end_timestamp_utc_ms = params.end_timestamp_utc_ms; if (params.ast !== undefined) payload.ast = params.ast; if (params.parameters !== undefined) payload.parameters = params.parameters; return fetchJson<BacktestResult>("/api/v1/backtest", { method: "POST", body: JSON.stringify(payload) }); }
export async function getCertifiedStrategies(): Promise<CertifiedStrategy[]> { return fetchJson<CertifiedStrategy[]>("/api/v2/certified/strategies"); }
export async function getCertifiedMetaStrategies(): Promise<CertifiedMetaStrategy[]> { return fetchJson<CertifiedMetaStrategy[]>("/api/v2/certified/meta-strategies"); }
export async function getCandidates(params?: { limit?: number; include_rejected?: boolean }): Promise<CandidateStrategy[]> { const query = new URLSearchParams(); if (params?.limit) query.set("limit", params.limit.toString()); if (params?.include_rejected !== undefined) query.set("include_rejected", params.include_rejected.toString()); const qs = query.toString(); return fetchJson<CandidateStrategy[]>(`/api/v1/candidates${qs ? `?${qs}` : ""}`); }
export async function getStrategyLabOverview(): Promise<StrategyLabOverview> { return fetchJson<StrategyLabOverview>("/api/v2/strategy-lab/overview"); }
export async function getStrategyLabStrategies(limit = 100): Promise<StrategyLabListResponse> { return fetchJson<StrategyLabListResponse>(`/api/v2/strategy-lab/strategies?limit=${encodeURIComponent(limit)}`); }
export async function getStrategyLabSQXStatus(): Promise<StrategyLabSQXStatus> { return fetchJson<StrategyLabSQXStatus>("/api/v2/strategy-lab/sqx/status"); }
export async function extractStrategyLabProject(projectName: string, databank?: string): Promise<StrategyLabExtractionResult> { if (!projectName.trim()) throw new Error("PROJECT_NAME_REQUIRED"); const qs = databank ? `?databank=${encodeURIComponent(databank)}` : ""; return fetchJson<StrategyLabExtractionResult>(`/api/v2/strategy-lab/extract/${encodeURIComponent(projectName)}${qs}`, { method: "POST" }); }
export async function getDiscoveryStatus(): Promise<DiscoveryStatus> { return fetchJson<DiscoveryStatus>("/api/v1/discovery/status"); }
export interface CertificationRecord { strategy_id: string; version: string; strategy_hash: string; dataset_id: string; dataset_checksum_sha256: string; engine_version: string; codebase_fingerprint: string; metrics_snapshot: Record<string, number>; route: string; status: string; scorecard: Record<string, unknown>; certified_at_utc: string; certificate_hash: string; }
export interface LineageTreeResponse { root_strategy_id: string; total_nodes: number; max_generation: number; nodes: Record<string, { strategy_id: string; version: string; parents: string[]; children: string[]; generation: number; mutation_history: string[]; is_certified: boolean; certificate_hash: string | null; }>; }
export interface PolicyImpactRequest { target_route?: string; cohort_ids?: string[]; new_max_drawdown_pct?: number; new_min_profit_factor?: number; new_min_calmar?: number; new_min_trades?: number; new_min_net_return_pct?: number; }
export interface PolicyImpactResult { analysis_id: string; target_route: string; analyzed_at_utc: string; total_cohort_size: number; baseline_policy: Record<string, number>; new_policy: Record<string, number>; baseline_passed_count: number; new_policy_passed_count: number; pass_rate_baseline_pct: number; pass_rate_new_pct: number; pass_rate_delta_pct: number; transition_summary: { CONSISTENT_PASS: number; CONSISTENT_FAIL: number; REVOKED: number; NEWLY_QUALIFIED: number; }; revoked_count: number; newly_qualified_count: number; recommendation: string; }
export interface ResearchDebateResponse { debate_id: string; strategy_id: string; blind_scope: string; hypotheses: Array<{ role: string; finding: string; suggested_action: string; confidence: number; target_node: string; evidence_citations: string[]; }>; disagreement_level: number; consensus_hypothesis: string; recommended_mutations: string[]; created_at_utc: string; }
export interface ResearchSynthesisResponse { proposal_id: string; experiment_id: string; mutation_id: string; strategy_id: string; parent_hash: string; mutated_hash: string; consensus_summary: string; mutated_dsl: Record<string, unknown>; validation_status: string; created_at_utc: string; }
export interface DurableJob { job_id: string; job_type: string; payload: Record<string, unknown>; priority: number; status: string; attempts: number; max_attempts: number; error_message: string | null; created_at_utc: string; updated_at_utc: string; completed_at_utc: string | null; }
export interface ForwardSufficiencyRequest { strategy_id: string; route: string; forward_days: number; forward_trades: number; forward_net_profit_pct: number; forward_max_dd_pct: number; is_expected_return_pct?: number; is_max_dd_pct?: number; }
export interface ForwardSufficiencyResult { strategy_id: string; route: string; verdict: "INSUFFICIENT_DATA" | "FORWARD_ACCUMULATING" | "FORWARD_CERTIFIED" | "FORWARD_DEGRADED_ABORT"; forward_days_completed: number; required_forward_days: number; forward_trades_completed: number; required_forward_trades: number; drawdown_consumption_pct: number; forward_to_is_return_ratio: number; is_certified_ready: boolean; diagnostics: string[]; evaluated_at_utc: string; }
export async function getLineageTree(strategyId: string): Promise<LineageTreeResponse> { return fetchJson<LineageTreeResponse>(`/api/v1/lineage/${strategyId}`); }
export async function verifyCertificate(certificate: CertificationRecord): Promise<{ is_valid: boolean; tampering_detected: boolean }> { return fetchJson("/api/v1/lineage/verify-certificate", { method: "POST", body: JSON.stringify(certificate) }); }
export async function runPolicyImpactAnalysis(request: PolicyImpactRequest): Promise<PolicyImpactResult> { return fetchJson<PolicyImpactResult>("/api/v1/policy/impact-analysis", { method: "POST", body: JSON.stringify(request) }); }
export async function triggerResearchDebate(strategyId: string): Promise<ResearchDebateResponse> { return fetchJson<ResearchDebateResponse>(`/api/v1/research-lab/debate/${strategyId}`, { method: "POST" }); }
export async function synthesizeStrategyMutation(strategyId: string, debateId: string): Promise<ResearchSynthesisResponse> { return fetchJson<ResearchSynthesisResponse>("/api/v1/research-lab/synthesize", { method: "POST", body: JSON.stringify({ strategy_id: strategyId, debate_id: debateId }) }); }
export async function enqueueDurableJob(jobType: string, payload: Record<string, unknown>, priority = 5): Promise<DurableJob> { return fetchJson<DurableJob>("/api/v1/jobs/enqueue", { method: "POST", body: JSON.stringify({ job_type: jobType, payload, priority }) }); }
export async function getDurableJobs(status?: string): Promise<DurableJob[]> { return fetchJson<DurableJob[]>(`/api/v1/jobs${status ? `?status=${encodeURIComponent(status)}` : ""}`); }
export async function evaluateForwardSufficiency(request: ForwardSufficiencyRequest): Promise<ForwardSufficiencyResult> { return fetchJson<ForwardSufficiencyResult>("/api/v1/forward/evaluate", { method: "POST", body: JSON.stringify(request) }); }
export function getApiUrl(path = ""): string { return `${BASE_URL}${path ? (path.startsWith("/") ? path : `/${path}`) : ""}`; }
export function getExportCsvUrl(route?: string): string {
  const qs = route && route !== "ALL" ? `?route=${encodeURIComponent(route)}` : "";
  return `/api/v2/certified/export/csv${qs}`;
}
export function getExportXlsxUrl(route?: string): string {
  const qs = route && route !== "ALL" ? `?route=${encodeURIComponent(route)}` : "";
  return `/api/v2/certified/export/xlsx${qs}`;
}
export const api = {
  get: <T = unknown>(endpoint: string) => fetchJson<T>(endpoint), post: <T = unknown>(endpoint: string, data?: unknown) => fetchJson<T>(endpoint, { method: "POST", body: data === undefined ? undefined : JSON.stringify(data) }), put: <T = unknown>(endpoint: string, data?: unknown) => fetchJson<T>(endpoint, { method: "PUT", body: data === undefined ? undefined : JSON.stringify(data) }), delete: <T = unknown>(endpoint: string) => fetchJson<T>(endpoint, { method: "DELETE", body: undefined }),
  getDatasets: (): Promise<ApprovedDataset[]> => fetchJson<ApprovedDataset[]>("/api/v1/datasets"),
  prepareEthResearch: (days: number): Promise<PrepareEthResponse> => fetchJson<PrepareEthResponse>("/api/v1/datasets/prepare-eth", { method: "POST", body: JSON.stringify({ days }) }),
  getSQXStatus: (): Promise<SQXStatus> => fetchJson<SQXStatus>("/api/v1/sqx/status"),
  getSQXProjects: (): Promise<{ projects: SQXProject[] }> => fetchJson<{ projects: SQXProject[] }>("/api/v1/sqx/projects"),
  getSQXDatabanks: (projectName?: string): Promise<{ databanks: SQXDatabank[] }> => fetchJson<{ databanks: SQXDatabank[] }>(`/api/v1/sqx/databanks${projectName ? `?project=${encodeURIComponent(projectName)}` : ""}`),
  getStrategies: (): Promise<LegacyStrategy[]> => fetchJson<LegacyStrategy[]>("/api/v1/strategies"),
  getBacktests: (): Promise<LegacyBacktestResult[]> => fetchJson<LegacyBacktestResult[]>("/api/v1/backtests"),
  getBacktestTrades: (backtestId: string): Promise<unknown[]> => fetchJson<unknown[]>(`/api/v1/backtest/${encodeURIComponent(backtestId)}/trades`),
  runFastBacktest: (strategyId: string, datasetId: string, capital?: number): Promise<unknown> => { if (!datasetId?.trim()) throw new Error("REAL_ONLY_DATASET_REQUIRED"); const payload: Record<string, unknown> = { strategy_id: strategyId, dataset_id: datasetId }; if (capital !== undefined) payload.initial_capital = capital; return fetchJson<unknown>("/api/v1/backtest", { method: "POST", body: JSON.stringify(payload) }); },
  getLeaderboard: (): Promise<LeaderboardItem[]> => fetchJson<LeaderboardItem[]>("/api/v1/leaderboard"),
  getCampaigns: (): Promise<Campaign[]> => fetchJson<Campaign[]>("/api/v1/campaigns"),
  createAutonomousCampaign: (payload: unknown): Promise<CampaignCreateResponse> => fetchJson<CampaignCreateResponse>("/api/v1/campaigns", { method: "POST", body: JSON.stringify(payload) }),
  startCampaign: (campaignId: string): Promise<unknown> => fetchJson<unknown>(`/api/v1/campaigns/${encodeURIComponent(campaignId)}/start`, { method: "POST" }),
  getExecutionSessions: (): Promise<unknown[]> => fetchJson<unknown[]>("/api/v1/execution/sessions"),
  getCandidates, getCandidatosCanonicos, getCertifiedStrategies, getCertifiedMetaStrategies, getDiscoveryStatus, getStrategyLabOverview, getStrategyLabStrategies, getStrategyLabSQXStatus, extractStrategyLabProject, getLineageTree, verifyCertificate, runPolicyImpactAnalysis, triggerResearchDebate, synthesizeStrategyMutation, enqueueDurableJob, getDurableJobs, evaluateForwardSufficiency, executeBacktest, getExportCsvUrl, getExportXlsxUrl,
};

