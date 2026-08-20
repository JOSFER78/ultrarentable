import os
from sqlalchemy import create_engine, event, Column, Integer, String, Float, Text, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from pathlib import Path

from services.api.app.config import DATA_DIR, STATE_DB_PATH

for folder in ["state", "raw", "normalized", "catalogs", "artifacts", "quarantine", "logs"]:
    (Path(DATA_DIR) / folder).mkdir(parents=True, exist_ok=True)

DB_PATH = str(STATE_DB_PATH)
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30}
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class InstrumentModel(Base):
    __tablename__ = "instruments"
    symbol = Column(String, primary_key=True, index=True)
    asset = Column(String)
    currency = Column(String)
    maker_fee_rate = Column(Float, nullable=True)
    taker_fee_rate = Column(Float, nullable=True)
    price_precision = Column(Integer, nullable=True)
    quantity_precision = Column(Integer, nullable=True)
    trade_min_quantity = Column(Float, nullable=True)
    trade_min_usdt = Column(Float, nullable=True)
    status = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow)

class DatasetModel(Base):
    __tablename__ = "datasets"
    dataset_id = Column(String, primary_key=True, index=True)
    venue = Column(String, default="BINGX")
    symbol = Column(String, index=True)
    feed_type = Column(String)
    interval = Column(String, nullable=True)
    start_time = Column(Integer)
    end_time = Column(Integer)
    record_count = Column(Integer)
    gap_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    out_of_order_count = Column(Integer, default=0)
    coverage_pct = Column(Float, default=100.0)
    checksum_sha256 = Column(String)
    status = Column(String, default="VALIDATING") # QUARANTINED, VALIDATING, APPROVED, REJECTED
    file_path = Column(String)
    manifest_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class RawIngestLogModel(Base):
    __tablename__ = "raw_ingest_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint = Column(String)
    params_json = Column(Text)
    raw_body_path = Column(String)
    sha256_raw = Column(String)
    exchange_start_time = Column(Integer, nullable=True)
    exchange_end_time = Column(Integer, nullable=True)
    receive_time = Column(Integer)
    status_code = Column(Integer, default=200)
    client_version = Column(String, default="v2.0.0")
    transformer_version = Column(String, default="v1.0.0")

class StrategyModel(Base):
    __tablename__ = "strategies"
    strategy_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    version = Column(String, default="1.0.0")
    family = Column(String, default="breakout")
    author = Column(String, default="User")
    canonical_hash = Column(String, index=True)
    parent_id = Column(String, nullable=True)
    generation = Column(Integer, default=0)
    seed = Column(Integer, nullable=True)
    dsl_json = Column(Text)
    validation_status = Column(String, default="DRAFT") # DRAFT, STRUCTURALLY_VALID, SEMANTICALLY_VALID, COMPILED, REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)

class StrategyCompilationModel(Base):
    __tablename__ = "strategy_compilations"
    compilation_id = Column(String, primary_key=True, index=True)
    strategy_id = Column(String, index=True)
    dsl_hash = Column(String, index=True)
    ir_hash = Column(String, index=True)
    compiler_version = Column(String, default="1.0.0")
    dsl_version = Column(String, default="1.0.0")
    instruction_count = Column(Integer)
    max_lookback = Column(Integer)
    required_series_json = Column(Text)
    artifact_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ValidationErrorLogModel(Base):
    __tablename__ = "validation_errors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String, nullable=True, index=True)
    error_code = Column(String)
    error_path = Column(String)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class BacktestModel(Base):
    __tablename__ = "backtests"
    backtest_id = Column(String, primary_key=True, index=True)
    strategy_id = Column(String, index=True)
    dataset_id = Column(String, index=True)
    engine_type = Column(String) # FAST_APPROXIMATE, CANONICAL
    initial_capital = Column(Float, default=10000.0)
    leverage = Column(Integer, default=1)
    final_equity = Column(Float)
    net_return_pct = Column(Float)
    max_drawdown_pct = Column(Float)
    win_rate = Column(Float)
    trades_count = Column(Integer)
    profit_factor = Column(Float)
    checksum = Column(String)
    ledger_path = Column(String, nullable=True)
    artifacts_path = Column(String, nullable=True)
    status = Column(String) # COMPLETED, FAILED, DISPUTED
    created_at = Column(DateTime, default=datetime.utcnow)
    # --- Out-of-sample (OOS) generalization metrics (added 2026-08-09) ---
    pf_os = Column(Float, nullable=True)                 # Profit factor (OOS) — the real anti-overfit gate
    net_return_os_pct = Column(Float, nullable=True)     # Net return (OOS) as %
    max_drawdown_os_pct = Column(Float, nullable=True)   # Max drawdown (OOS) as % of equity
    trades_os = Column(Integer, nullable=True)           # Trades count (OOS)
    ret_dd_ratio = Column(Float, nullable=True)          # SQX Ret/DD Ratio (IS): NetProfit / MaxDrawdownUSD

class CampaignModel(Base):
    __tablename__ = "campaigns"
    campaign_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    symbol = Column(String)
    interval = Column(String)
    population_size = Column(Integer, default=50)
    generations_count = Column(Integer, default=20)
    current_generation = Column(Integer, default=0)
    seed = Column(Integer, default=42)
    status = Column(String) # IDLE, CREATED, GENERATING, FAST_EVALUATING, TUNING, PAUSED, COMPLETED, FAILED
    checkpoints_path = Column(String, nullable=True)
    mode = Column(String, default="EXPLORE") # EXPLORE, IMPROVE, REGIME_SEARCH
    target_multiplier = Column(Float, default=11.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class CampaignEventModel(Base):
    __tablename__ = "campaign_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String, index=True)
    event_type = Column(String)
    message = Column(Text)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CampaignTrialModel(Base):
    __tablename__ = "campaign_trials"
    trial_id = Column(String, primary_key=True, index=True)
    campaign_id = Column(String, index=True)
    strategy_id = Column(String, index=True)
    generation = Column(Integer)
    status = Column(String)
    fitness = Column(Float, nullable=True)
    net_return_pct = Column(Float, nullable=True)
    final_equity = Column(Float, nullable=True)
    failure_code = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ResearchSourceModel(Base):
    __tablename__ = "research_sources"
    source_id = Column(String, primary_key=True, index=True)
    title = Column(String)
    url = Column(String)
    author = Column(String, nullable=True)
    fetch_date = Column(DateTime, default=datetime.utcnow)
    raw_content = Column(Text)
    sha256_hash = Column(String)
    license_info = Column(String, nullable=True)
    hypothesis_text = Column(Text)
    associated_backtest_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class InstrumentRuleSnapshotModel(Base):
    __tablename__ = "instrument_rule_snapshots"
    snapshot_id = Column(String, primary_key=True, index=True)
    symbol = Column(String, index=True)
    captured_at = Column(DateTime, default=datetime.utcnow)
    source_endpoint = Column(String)
    raw_path = Column(String)
    raw_sha256 = Column(String)
    max_leverage = Column(Integer)
    maintenance_margin_rate = Column(Float)
    maintenance_tiers_json = Column(Text, nullable=True)
    price_precision = Column(Integer, default=4)
    quantity_precision = Column(Integer, default=4)
    min_quantity = Column(Float, default=0.001)
    min_notional = Column(Float, default=5.0)
    max_quantity = Column(Float, default=1000.0)
    contract_status = Column(String, default="ONLINE")

class AccountFeeSnapshotModel(Base):
    __tablename__ = "account_fee_snapshots"
    snapshot_id = Column(String, primary_key=True, index=True)
    account_hash = Column(String, index=True)
    symbol = Column(String, nullable=True)
    maker_fee = Column(Float, default=0.0002)
    taker_fee = Column(Float, default=0.0005)
    captured_at = Column(DateTime, default=datetime.utcnow)
    source_endpoint = Column(String)
    raw_path = Column(String)
    raw_sha256 = Column(String)

class SearchConfigModel(Base):
    __tablename__ = "search_configs"
    config_id = Column(String, primary_key=True, index=True)
    name = Column(String, default="default")
    mode = Column(String, default="ultra")  # ultra | fondeo
    project = Column(String, default="Ultra_Auto_Pilot")
    databank = Column(String, default="Results")
    symbol = Column(String, nullable=True)
    interval = Column(String, nullable=True)
    population = Column(Integer, nullable=True)
    target_multiplier = Column(Float, nullable=True)
    max_drawdown_pct = Column(Float, nullable=True)
    consistency_target = Column(Float, nullable=True)
    techniques_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)



class SearchLogModel(Base):
    __tablename__ = "search_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(String)
    level = Column(String)
    stage = Column(String, nullable=True)
    message = Column(Text)
    run_id = Column(String, nullable=True)

class AutopilotRunModel(Base):
    __tablename__ = "autopilot_runs"
    run_id = Column(String, primary_key=True, index=True)
    status = Column(String, default="INITIALIZING")  # INITIALIZING, SCANNING, RUNNING, PAUSED, COMPLETED, STOPPED
    mode = Column(String, default="AUTOPILOT_ULTRA")
    current_symbol = Column(String, nullable=True)
    current_interval = Column(String, nullable=True)
    best_candidate_id = Column(String, nullable=True)
    best_fast_return_pct = Column(Float, default=0.0)
    best_canonical_return_pct = Column(Float, nullable=True)
    evaluated_strategies_count = Column(Integer, default=0)
    explored_symbols_count = Column(Integer, default=0)
    cpu_budget_workers = Column(Integer, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)

class AutopilotDecisionModel(Base):
    __tablename__ = "autopilot_decisions"
    decision_id = Column(String, primary_key=True, index=True)
    run_id = Column(String, index=True)
    module = Column(String)  # UniverseScanner, OpportunityRanker, LeverageAutopilot, CandidateRepairer
    decision = Column(String)
    reason = Column(Text)
    alternatives_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class OpportunityMatrixModel(Base):
    __tablename__ = "opportunity_matrix"
    matrix_id = Column(String, primary_key=True, index=True)
    symbol = Column(String, index=True)
    interval = Column(String)
    liquidity_score = Column(Float)
    volatility_score = Column(Float)
    dataset_status = Column(String, default="APPROVED")
    rank = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class LeverageTrialModel(Base):
    __tablename__ = "leverage_trials"
    trial_id = Column(String, primary_key=True, index=True)
    run_id = Column(String, index=True)
    strategy_id = Column(String, index=True)
    symbol = Column(String)
    leverage = Column(Integer)
    tier = Column(Integer, default=1)
    status = Column(String)  # PASSED, LIQUIDATED, FAILED
    final_equity = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class NoveltyArchiveModel(Base):
    __tablename__ = "novelty_archive"
    archive_id = Column(String, primary_key=True, index=True)
    run_id = Column(String, index=True)
    strategy_hash = Column(String, index=True)
    ast_distance_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class CanonicalValidationModel(Base):
    __tablename__ = "canonical_validations"
    validation_id = Column(String, primary_key=True, index=True)
    strategy_id = Column(String, index=True)
    fast_backtest_id = Column(String)
    canonical_engine = Column(String, default="NAUTILUS_TRADER")
    status = Column(String)  # PENDING, PASSED, DISPUTED
    fast_return_pct = Column(Float)
    canonical_return_pct = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProviderRuleSetModel(Base):
    __tablename__ = "provider_rule_sets"
    provider_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    provider_name = Column(String, nullable=False, index=True)
    market_type = Column(String, default="FUTURES")  # FUTURES, CFD, CRYPTO
    platform = Column(String, default="Tradovate / NinjaTrader")
    allowed_instruments = Column(String, default="MES, MNQ, ES, NQ")
    account_size = Column(Float, default=50000.0)
    target_usd = Column(Float, default=3000.0)
    target_pct = Column(Float, default=6.0)
    daily_loss_limit_usd = Column(Float, nullable=True)
    daily_loss_limit_pct = Column(Float, nullable=True)
    dll_calc_model = Column(String, default="EOD Balance")  # EOD Balance, Intraday High, None
    max_trailing_dd_usd = Column(Float, default=2000.0)
    max_trailing_dd_pct = Column(Float, default=4.0)
    trailing_dd_type = Column(String, default="EOD Trailing")  # EOD Trailing, Intraday Peak Trailing, Static
    consistency_rule_pct = Column(Float, default=50.0)
    min_trading_days = Column(Integer, default=2)
    overnight_allowed = Column(Boolean, default=False)
    news_trading_allowed = Column(Boolean, default=True)
    ea_bots_allowed = Column(String, default="PERMITTED")  # PERMITTED, PERMITTED_WITH_CONDITIONS, PROHIBITED
    monthly_cost_usd = Column(Float, nullable=True)
    source_url = Column(String, nullable=True)
    verified_at = Column(String, nullable=True)
    verification_status = Column(String, default="VERIFIED")  # VERIFIED, UNVERIFIED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CandidateModel(Base):
    __tablename__ = "candidates"
    candidate_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    route = Column(String, default="FONDEO")  # ULTRA, FONDEO
    symbol = Column(String, default="BTC-USDT")
    timeframe = Column(String, default="1h")
    dataset_id = Column(String, nullable=True)
    status = Column(String, default="INVESTIGACION_BTC")
    # Statuses: INVESTIGACION_BTC, RECHAZADA_FONDEO_DD, CANDIDATA_FONDEO, PAPER, LISTA_PARA_EVALUACION, EJECUTANDO, PAUSADA, RETIRADA
    status_reason = Column(Text, nullable=True)
    net_profit_is = Column(Float, default=0.0)
    trades_is = Column(Integer, default=0)
    profit_factor_is = Column(Float, default=0.0)
    max_dd_is_pct = Column(Float, default=0.0)
    net_profit_oos = Column(Float, default=0.0)
    trades_oos = Column(Integer, default=0)
    profit_factor_oos = Column(Float, default=0.0)
    max_dd_oos_pct = Column(Float, default=0.0)
    ratio_oos_is = Column(Float, default=0.0)
    wfo_pass_pct = Column(Float, nullable=True)
    monte_carlo_score = Column(Float, nullable=True)
    scorecard_json = Column(Text, nullable=True)
    engine_version = Column(String, default="1.02", nullable=True)
    validation_pipeline_version = Column(String, default="1.02", nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExecutionSessionModel(Base):
    __tablename__ = "execution_sessions"
    session_id = Column(String, primary_key=True, index=True)
    route = Column(String, default="ULTRA")  # ULTRA, FONDEO
    environment = Column(String, default="PAPER_BINGX")  # PAPER_BINGX, LIVE_BINGX, PAPER_PROP_FIRM, EVAL_PROP_FIRM
    candidate_id = Column(String, nullable=True)
    provider_id = Column(String, nullable=True)
    symbol = Column(String, default="BTC-USDT")
    status = Column(String, default="INITIALIZING")  # INITIALIZING, RUNNING, PAUSED, STOPPED, KILL_SWITCH_TRIGGERED
    current_pnl_usd = Column(Float, default=0.0)
    daily_pnl_usd = Column(Float, default=0.0)
    current_drawdown_pct = Column(Float, default=0.0)
    peak_equity_usd = Column(Float, default=50000.0)
    heartbeat_last_at = Column(DateTime, default=datetime.utcnow)
    last_signal = Column(Text, nullable=True)
    last_order = Column(Text, nullable=True)
    open_positions_json = Column(Text, nullable=True)
    kill_switch_active = Column(Boolean, default=False)
    kill_switch_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditEventModel(Base):
    __tablename__ = "audit_events"
    event_id = Column(String, primary_key=True, index=True)
    category = Column(String, default="SYSTEM")  # CAMPAIGN, GATE, EXPORT, PAPER, LIVE, KILL_SWITCH, SYSTEM, RULE_CHANGE
    route = Column(String, default="SYSTEM")  # ULTRA, FONDEO, SYSTEM
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, default="INFO")  # INFO, WARNING, CRITICAL, SUCCESS
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


from sqlalchemy import text


def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Auto-migration for engine_version columns if missing
    try:
        with engine.connect() as conn:
            cursor = conn.connection.cursor()
            cursor.execute("PRAGMA table_info(candidates);")
            cols = [row[1] for row in cursor.fetchall()]
            if cols and "engine_version" not in cols:
                cursor.execute("ALTER TABLE candidates ADD COLUMN engine_version VARCHAR DEFAULT '1.02';")
            if cols and "validation_pipeline_version" not in cols:
                cursor.execute("ALTER TABLE candidates ADD COLUMN validation_pipeline_version VARCHAR DEFAULT '1.02';")
            conn.connection.commit()
    except Exception:
        pass
    
    # Ensure tables and seed initial canonical data
    with SessionLocal() as db:
        # Seed ProviderRuleSets if empty
        if db.query(ProviderRuleSetModel).count() == 0:
            providers = [
                ProviderRuleSetModel(
                    provider_id="topstep_combine_50k",
                    name="Topstep Combine 50K",
                    provider_name="Topstep",
                    market_type="FUTURES",
                    platform="TopstepX / Tradovate",
                    allowed_instruments="MES, MNQ, ES, NQ, YM, RTY, CL, GC",
                    account_size=50000.0,
                    target_usd=3000.0,
                    target_pct=6.0,
                    daily_loss_limit_usd=1000.0,
                    daily_loss_limit_pct=2.0,
                    dll_calc_model="EOD Balance",
                    max_trailing_dd_usd=2000.0,
                    max_trailing_dd_pct=4.0,
                    trailing_dd_type="EOD Trailing",
                    consistency_rule_pct=50.0,
                    min_trading_days=2,
                    overnight_allowed=False,
                    news_trading_allowed=True,
                    ea_bots_allowed="PERMITTED_WITH_CONDITIONS",
                    monthly_cost_usd=49.0,
                    source_url="https://help.topstep.com/en/articles/8284197-account-combine-parameters",
                    verified_at="2026-08-08",
                    verification_status="VERIFIED",
                    notes="Prohibido VPN/proxy residencial, sin scalping que explote fills SIM."
                ),
                ProviderRuleSetModel(
                    provider_id="tradeday_50k",
                    name="TradeDay 50K (14-Day Free Trial Available)",
                    provider_name="TradeDay",
                    market_type="FUTURES",
                    platform="Tradovate / NinjaTrader",
                    allowed_instruments="MES, MNQ, ES, NQ, YM, RTY",
                    account_size=50000.0,
                    target_usd=3000.0,
                    target_pct=6.0,
                    daily_loss_limit_usd=1000.0,
                    daily_loss_limit_pct=2.0,
                    dll_calc_model="Intraday High",
                    max_trailing_dd_usd=2000.0,
                    max_trailing_dd_pct=4.0,
                    trailing_dd_type="Intraday Peak Trailing",
                    consistency_rule_pct=30.0,
                    min_trading_days=5,
                    overnight_allowed=False,
                    news_trading_allowed=True,
                    ea_bots_allowed="PERMITTED",
                    monthly_cost_usd=125.0,
                    source_url="https://www.tradeday.com/",
                    verified_at="2026-08-08",
                    verification_status="VERIFIED",
                    notes="Ofrece Free Trial de 14 días. Confirmar soporte para bot VPS."
                ),
                ProviderRuleSetModel(
                    provider_id="apex_50k",
                    name="Apex Trader Funding 50K",
                    provider_name="Apex Trader Funding",
                    market_type="FUTURES",
                    platform="NinjaTrader 8 / Tradovate / Rithmic",
                    allowed_instruments="MES, MNQ, ES, NQ, YM, RTY",
                    account_size=50000.0,
                    target_usd=3000.0,
                    target_pct=6.0,
                    daily_loss_limit_usd=None,
                    daily_loss_limit_pct=None,
                    dll_calc_model="None",
                    max_trailing_dd_usd=2500.0,
                    max_trailing_dd_pct=5.0,
                    trailing_dd_type="Intraday Peak Trailing",
                    consistency_rule_pct=100.0,
                    min_trading_days=1,
                    overnight_allowed=False,
                    news_trading_allowed=True,
                    ea_bots_allowed="PERMITTED",
                    monthly_cost_usd=35.0,
                    source_url="https://apextraderfunding.com/",
                    verified_at="2026-08-08",
                    verification_status="VERIFIED",
                    notes="Sin límite de pérdida diaria en evaluación; trailing DD continuo."
                ),
                ProviderRuleSetModel(
                    provider_id="fundednext_futures_50k",
                    name="FundedNext Futures Rapid 50K",
                    provider_name="FundedNext",
                    market_type="FUTURES",
                    platform="MT5 / TradeLocker",
                    allowed_instruments="MES, MNQ, ES, NQ, Commodities",
                    account_size=50000.0,
                    target_usd=3000.0,
                    target_pct=6.0,
                    daily_loss_limit_usd=None,
                    daily_loss_limit_pct=None,
                    dll_calc_model="None",
                    max_trailing_dd_usd=2000.0,
                    max_trailing_dd_pct=4.0,
                    trailing_dd_type="EOD Trailing",
                    consistency_rule_pct=100.0,
                    min_trading_days=3,
                    overnight_allowed=True,
                    news_trading_allowed=True,
                    ea_bots_allowed="PERMITTED",
                    monthly_cost_usd=99.0,
                    source_url="https://fundednext.com/general-rules/futures/",
                    verified_at="2026-08-08",
                    verification_status="VERIFIED",
                    notes="Reglas claras de futuros; 90% payout split."
                ),
                ProviderRuleSetModel(
                    provider_id="takeprofit_50k",
                    name="Take Profit Trader 50K",
                    provider_name="Take Profit Trader",
                    market_type="FUTURES",
                    platform="Tradovate / NinjaTrader",
                    allowed_instruments="MES, MNQ, ES, NQ",
                    account_size=50000.0,
                    target_usd=3000.0,
                    target_pct=6.0,
                    daily_loss_limit_usd=1100.0,
                    daily_loss_limit_pct=2.2,
                    dll_calc_model="EOD Balance",
                    max_trailing_dd_usd=2000.0,
                    max_trailing_dd_pct=4.0,
                    trailing_dd_type="EOD Trailing",
                    consistency_rule_pct=50.0,
                    min_trading_days=5,
                    overnight_allowed=False,
                    news_trading_allowed=True,
                    ea_bots_allowed="PERMITTED",
                    monthly_cost_usd=150.0,
                    source_url="https://takeprofittrader.com/",
                    verified_at="2026-08-08",
                    verification_status="VERIFIED",
                    notes="Permite retiros desde el día 1 de cuenta Pro."
                ),
                ProviderRuleSetModel(
                    provider_id="bulenox_50k",
                    name="Bulenox 50K (Rithmic)",
                    provider_name="Bulenox",
                    market_type="FUTURES",
                    platform="NinjaTrader / Rithmic",
                    allowed_instruments="MES, MNQ, ES, NQ",
                    account_size=50000.0,
                    target_usd=3000.0,
                    target_pct=6.0,
                    daily_loss_limit_usd=1250.0,
                    daily_loss_limit_pct=2.5,
                    dll_calc_model="Intraday High",
                    max_trailing_dd_usd=2500.0,
                    max_trailing_dd_pct=5.0,
                    trailing_dd_type="Intraday Peak Trailing",
                    consistency_rule_pct=40.0,
                    min_trading_days=5,
                    overnight_allowed=False,
                    news_trading_allowed=False,
                    ea_bots_allowed="UNVERIFIED",
                    monthly_cost_usd=125.0,
                    source_url="https://bulenox.com/",
                    verified_at="2026-08-08",
                    verification_status="UNVERIFIED",
                    notes="Política de EAs y bots no confirmada oficialmente en web. Validar con soporte."
                ),
            ]
            for p in providers:
                db.add(p)
            db.commit()

        # Candidates table remains clean (0 candidates) until discovered by the search engine

        # Seed initial Audit Events
        if db.query(AuditEventModel).count() == 0:
            events = [
                AuditEventModel(
                    event_id="evt_001_init",
                    category="SYSTEM",
                    route="SYSTEM",
                    title="Inicialización del Sistema Anti-Overfit",
                    description="Aplicados los 10 cambios XML al generador StrategyQuant X con función de fitness ReturnDDRatio y WFO activo.",
                    severity="SUCCESS"
                ),
                AuditEventModel(
                    event_id="evt_002_reclass_54",
                    category="GATE",
                    route="FONDEO",
                    title="Reclasificación: Strategy 1.0.54 ➔ RECHAZADA_FONDEO_DD",
                    description="Strategy 1.0.54 marcada como RECHAZADA_FONDEO_DD por presentar DD OOS del 10.18% superando el límite canónico de 4.0%.",
                    severity="WARNING"
                ),
                AuditEventModel(
                    event_id="evt_003_reclass_32",
                    category="GATE",
                    route="FONDEO",
                    title="Reclasificación: Strategy 1.0.32 ➔ INVESTIGACION_BTC",
                    description="Strategy 1.0.32 catalogada como INVESTIGACION_BTC. Requiere datos CME y validación intrabar antes de postular a fondeo.",
                    severity="INFO"
                ),
            ]
            for e in events:
                db.add(e)
            db.commit()

        # Purge any legacy demo/fake execution sessions (REAL-ONLY DOCTRINE)
        db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id.like("%demo%")).delete()
        db.commit()

    return DB_PATH

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
