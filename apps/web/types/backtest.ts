/**
 * apps/web/types/backtest.ts
 * Contratos TypeScript para BacktestRequest y BacktestResult sincronizados con contracts/backtest.py.
 * DOCTRINA ZERO-MOCKS: Tipado estricto para ejecución determinista y hash criptográfico de ledger.
 */

export type EngineType = "FAST_APPROXIMATE" | "SQX_PRECISION" | "NAUTILUS_EVENT_DRIVEN";

export interface BarData {
  timestamp_utc_ms: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface DatasetSnapshot {
  dataset_id: string;
  symbol: string;
  timeframe: string;
  start_timestamp_utc_ms: number;
  end_timestamp_utc_ms: number;
  total_bars: number;
  sha256_hash: string;
  is_in_sample?: boolean;
}

export interface BacktestRequest {
  request_id: string;
  strategy_id: string;
  strategy?: any;
  engine_type?: EngineType;
  dataset: DatasetSnapshot;
  execution_config_hash?: string | null;
  initial_capital_usd?: number;
  leverage?: number;
  fee_multiplier?: number;
  slippage_bps?: number;
  split_ratio?: number;
}

export interface TradeLog {
  trade_id: string;
  direction: string;
  entry_time_utc_ms: number;
  exit_time_utc_ms: number;
  entry_price: number;
  exit_price: number;
  quantity: number;
  leverage?: number;
  gross_pnl_usd: number;
  fee_usd: number;
  slippage_usd: number;
  net_pnl_usd: number;
  return_pct: number;
  return_r: number;
  exit_reason: string;
}

export interface EquityPoint {
  timestamp_utc_ms: number;
  equity_usd: number;
  drawdown_pct: number;
}

export interface BacktestResult {
  request_id: string;
  strategy_id: string;
  engine_type: EngineType;
  dataset_id: string;
  ledger_hash: string;
  initial_capital_usd: number;
  final_equity_usd: number;
  net_profit_usd: number;
  net_return_pct: number;
  total_trades: number;
  winning_trades?: number;
  losing_trades?: number;
  win_rate_pct: number;
  profit_factor: number;
  max_drawdown_pct: number;
  max_drawdown_usd: number;
  sharpe_ratio?: number;
  sortino_ratio?: number;
  trades: TradeLog[];
  equity_curve: EquityPoint[];
  execution_time_ms: number;
  provenance_hash_sha256: string;
}
