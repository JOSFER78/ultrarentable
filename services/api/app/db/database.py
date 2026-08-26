import os
from sqlalchemy import create_engine, event, Column, Integer, String, Float, Text, Boolean, DateTime, text
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
    cursor.execute("PRAGMA mmap_size=268435456;")
    cursor.execute("PRAGMA cache_size=-64000;")
    cursor.execute("PRAGMA busy_timeout=15000;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# NOTE: Existing model declarations are preserved exactly; only the redundant
# index=True on GatewayProviderModel.provider_id is removed below because the
# column is already the table primary key and duplicate metadata/index creation
# was blocking clean SQLite startup.

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
    pf_os = Column(Float, nullable=True)
    net_return_os_pct = Column(Float, nullable=True)
    max_drawdown_os_pct = Column(Float, nullable=True)
    trades_os = Column(Integer, nullable=True)
    ret_dd_ratio = Column(Float, nullable=True)

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
    status = Column(String)
    checkpoints_path = Column(String, nullable=True)
    mode = Column(String, default="EXPLORE")
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
    mode = Column(String, default="ultra")
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
    status = Column(String, default="INITIALIZING")
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
    module = Column(String)
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
    status = Column(String)
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
    status = Column(String)
    fast_return_pct = Column(Float)
    canonical_return_pct = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProviderRuleSetModel(Base):
    __tablename__ = "provider_rule_sets"
    provider_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    provider_name = Column(String, nullable=False, index=True)
    market_type = Column(String, default="FUTURES")
    platform = Column(String, default="Tradovate / NinjaTrader")
    allowed_instruments = Column(String, default="MES, MNQ, ES, NQ")
    account_size = Column(Float, default=50000.0)
    program_type = Column(String, default="Standard")
    account_tier = Column(String, default="50K")
    target_usd = Column(Float, default=3000.0)
    target_pct = Column(Float, default=6.0)
    daily_loss_limit_usd = Column(Float, nullable=True)
    daily_loss_limit_pct = Column(Float, nullable=True)
    dll_calc_model = Column(String, default="EOD Balance")
    max_trailing_dd_usd = Column(Float, default=2000.0)
    max_trailing_dd_pct = Column(Float, default=4.0)
    trailing_dd_type = Column(String, default="EOD Trailing")
    consistency_rule_pct = Column(Float, default=50.0)
    min_trading_days = Column(Integer, default=2)
    overnight_allowed = Column(Boolean, default=False)
    news_trading_allowed = Column(Boolean, default=True)
    ea_bots_allowed = Column(String, default="PERMITTED")
    monthly_cost_usd = Column(Float, nullable=True)
    regular_price_usd = Column(Float, nullable=True)
    promo_price_usd = Column(Float, nullable=True)
    discount_code = Column(String, nullable=True)
    discount_pct = Column(Float, default=0.0)
    activation_fee_usd = Column(Float, default=0.0)
    payout_split_pct = Column(Float, default=90.0)
    payout_frequency = Column(String, default="Quincenal")
    created_at = Column(DateTime, default=datetime.utcnow)

class GateEventModel(Base):
    __tablename__ = "gate_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    category = Column(String, default="SYSTEM")
    route = Column(String, default="SYSTEM")
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, default="INFO")
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class GatewayProviderModel(Base):
    __tablename__ = "gateway_providers"
    provider_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, default="PROP_FIRM_BRIDGE")
    auth_token = Column(String, nullable=True)
    endpoint_url = Column(String, nullable=True)
    api_key = Column(String, nullable=True)
    api_secret = Column(String, nullable=True)
    is_enabled = Column(Boolean, default=True)
    status = Column(String, default="IDLE_WAITING")
    latency_ms = Column(Float, default=0.0)
    telemetry_packets_count = Column(Integer, default=0)
    config_json = Column(Text, nullable=True)
    last_ping_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Ensure tables and seed initial canonical data
    with SessionLocal() as db:
        from services.api.app.db.seed_prop_firms import PROP_FIRMS_CATALOG
        
        for item in PROP_FIRMS_CATALOG:
            existing = db.query(ProviderRuleSetModel).filter(
                ProviderRuleSetModel.provider_id == item["provider_id"]
            ).first()
            
            if existing:
                existing.name = item["name"]
                existing.provider_name = item["provider_name"]
                existing.market_type = item.get("market_type", "FUTURES")
                existing.platform = item.get("platform", "Tradovate / NinjaTrader")
                existing.allowed_instruments = item.get("allowed_instruments", "MES, MNQ, ES, NQ")
                existing.account_size = item.get("account_size", 50000.0)
                existing.program_type = item.get("program_type", "Standard")
                existing.account_tier = item.get("account_tier", "50K")
                existing.target_usd = item.get("target_usd", 3000.0)
                existing.target_pct = item.get("target_pct", 6.0)
                existing.daily_loss_limit_usd = item.get("daily_loss_limit_usd")
                existing.daily_loss_limit_pct = item.get("daily_loss_limit_pct")
                existing.dll_calc_model = item.get("dll_calc_model", "EOD Balance")
                existing.max_trailing_dd_usd = item.get("max_trailing_dd_usd", 2000.0)
                existing.max_trailing_dd_pct = item.get("max_trailing_dd_pct", 4.0)
                existing.trailing_dd_type = item.get("trailing_dd_type", "EOD Trailing")
                existing.consistency_rule_pct = item.get("consistency_rule_pct", 50.0)
                existing.min_trading_days = item.get("min_trading_days", 2)
                existing.overnight_allowed = item.get("overnight_allowed", False)
                existing.news_trading_allowed = item.get("news_trading_allowed", True)
                existing.ea_bots_allowed = item.get("ea_bots_allowed", "PERMITTED")
                existing.monthly_cost_usd = item.get("monthly_cost_usd")
                existing.regular_price_usd = item.get("regular_price_usd")
                existing.promo_price_usd = item.get("promo_price_usd")
                existing.discount_code = item.get("discount_code")
                existing.discount_pct = item.get("discount_pct", 0.0)
                existing.activation_fee_usd = item.get("activation_fee_usd", 0.0)
                existing.payout_split_pct = item.get("payout_split_pct", 90.0)
                existing.payout_frequency = item.get("payout_frequency", "Quincenal")
            else:
                db.add(ProviderRuleSetModel(**item))
        db.commit()
