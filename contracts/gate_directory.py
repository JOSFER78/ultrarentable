"""contracts/gate_directory.py
CATÁLOGO CANÓNICO ÚNICO de los 11 Gates cuantitativos (slugs, nombres, umbrales
default_params y esquema de telemetría).
Backend (routers, orchestrator), frontend y documentación DEBEN consumir esta
definición; prohibido re-declarar gates en otros módulos.
DOCTRINA ZERO-MOCKS: live_telemetry es None/UNKNOWN hasta que exista telemetría
medida real por gate (no valores decorativos).
"""

GATES_DIRECTORY = [
    {
        "gate_number": 1,
        "slug": "gate-1-data-ingest",
        "name": "Data Ingest & Integrity SHA-256",
        "short_title": "1. Ingesta & Datos",
        "category": "DATA_INTEGRITY",
        "badge": "Gate Fundamental",
        "icon": "🗄️",
        "formula": "SHA256(OHLCV) · Gaps < 0.1% · Bars >= 3,840 (H1) / 25,000 (M15)",
        "objective": "Garantiza que el backtest opera sobre series de precios 100% reales, sin interpolaciones sintéticas, sin velas fantasma y con timestamp UTC estricto.",
        "description": "Auditoría de integridad a nivel de byte para el historial de precios OHLCV. Calcula huella criptográfica SHA-256 de cada bloque de velas y detecta desalineaciones temporales.",
        "default_params": {
            "min_bars_required": {"label": "Mínimo de Velas Requeridas", "value": 3840, "unit": "barras", "type": "number", "min": 500, "max": 100000, "step": 100, "desc": "Umbral mínimo de historial para considerar válido el dataset."},
            "max_gap_tolerance_pct": {"label": "Tolerancia Máxima de Gaps", "value": 0.10, "unit": "%", "type": "number", "min": 0.0, "max": 1.0, "step": 0.01, "desc": "Porcentaje máximo de huecos temporales permitidos en la serie."},
            "enforce_sha256_checksum": {"label": "Verificación SHA-256 Obligatoria", "value": True, "type": "boolean", "desc": "Calcula y compara huella criptográfica de cada bloque de datos."},
            "storage_mode": {"label": "Modo de Persistencia", "value": "SQLITE_WAL", "type": "select", "options": ["SQLITE_WAL", "PARQUET", "MEMORY_STREAM"], "desc": "Formato de almacenamiento de alta velocidad."}
        },
        "live_telemetry": {
            "status": "SIN TELEMETRÍA REAL CONECTADA",
            "status_color": "#94a3b8",
            "datasets_audited": None,
            "candles_verified": None,
            "pass_rate_pct": None,
            "avg_latency_ms": None,
            "last_verdict": "N/D · ZERO-MOCKS: la telemetría de este gate debe medirse, no declararse"
        }
    },
    {
        "gate_number": 2,
        "slug": "gate-2-cost-backtest",
        "name": "Cost & Friction Realistic Backtest",
        "short_title": "2. Costes & Fricción",
        "category": "FRICTION_AUDIT",
        "badge": "Gate de Fricción",
        "icon": "💸",
        "formula": "PnL_Neto = PnL_Bruto - (Comisión_Fija + Fee_% * Nocional + Slippage_Ticks * Tick_Value)",
        "objective": "Aplica la estructura de comisiones y deslizamiento institucional real según la clase de activo (CME $2.50/ctto, Forex spreads, Cripto 0.05%).",
        "description": "Elimina estrategias 'fantasmas' que solo ganan dinero en ausencia de costes de transacción. Simula ejecuciones taker y slippage adaptativo.",
        "default_params": {
            "crypto_taker_fee_pct": {"label": "Comisión Cripto Taker", "value": 0.05, "unit": "%", "type": "number", "min": 0.01, "max": 0.20, "step": 0.01, "desc": "Comisión porcentual por orden ejecutada en Cripto Perpetuos."},
            "cme_fixed_fee_per_contract": {"label": "Comisión Fija CME", "value": 2.50, "unit": "USD", "type": "number", "min": 0.50, "max": 10.0, "step": 0.25, "desc": "Comisión fija por contrato en Futuros CME (NQ, ES, YM, GC)."},
            "forex_spread_pips": {"label": "Spread Estándar Forex", "value": 0.6, "unit": "pips", "type": "number", "min": 0.1, "max": 3.0, "step": 0.1, "desc": "Diferencial bid-ask aplicado en pares de divisas."},
            "min_profit_factor_after_costs": {"label": "Profit Factor Mínimo Post-Costes", "value": 1.15, "unit": "PF", "type": "number", "min": 1.0, "max": 3.0, "step": 0.05, "desc": "Umbral mínimo de rentabilidad neta para superar la prueba."}
        },
        "live_telemetry": {
            "status": "SIN TELEMETRÍA REAL CONECTADA",
            "status_color": "#94a3b8",
            "datasets_audited": None,
            "candles_verified": None,
            "pass_rate_pct": None,
            "avg_latency_ms": None,
            "last_verdict": "N/D · ZERO-MOCKS: la telemetría de este gate debe medirse, no declararse"
        }
    },
    {
        "gate_number": 3,
        "slug": "gate-3-trade-significance",
        "name": "Statistical Trade Significance & Outliers",
        "short_title": "3. Muestra Estadística",
        "category": "STATISTICAL_RIGOR",
        "badge": "Gate Estadístico",
        "icon": "📊",
        "formula": "Trades_OOS >= 20 · Max_Single_Trade_PnL <= 20% Total_PnL · t_stat > 2.0",
        "objective": "Verifica que el rendimiento no dependa de un 'golpe de suerte' (outlier) o de una muestra ínfima de operaciones.",
        "description": "Calcula la distribución de retornos, el ratio de concentración del mejor trade sobre el beneficio total y la significancia estadística Student-t.",
        "default_params": {
            "min_oos_trades": {"label": "Mínimo de Operaciones OOS", "value": 20, "unit": "trades", "type": "number", "min": 10, "max": 100, "step": 5, "desc": "Número mínimo de operaciones en periodo fuera de muestra."},
            "max_outlier_pnl_pct": {"label": "Concentración Máxima 1 Trade", "value": 20.0, "unit": "%", "type": "number", "min": 5.0, "max": 50.0, "step": 1.0, "desc": "El mejor trade no puede representar más de este % del beneficio total."},
            "min_t_statistic": {"label": "T-Statistic Mínimo", "value": 2.0, "unit": "t", "type": "number", "min": 1.5, "max": 4.0, "step": 0.1, "desc": "Grado de confianza estadística en el retorno medio positivo."},
            "min_win_loss_ratio": {"label": "Ratio Promedio Ganador/Perdedor", "value": 1.2, "unit": "ratio", "type": "number", "min": 0.8, "max": 5.0, "step": 0.1, "desc": "Relación entre el beneficio medio y la pérdida media."}
        },
        "live_telemetry": {
            "status": "SIN TELEMETRÍA REAL CONECTADA",
            "status_color": "#94a3b8",
            "datasets_audited": None,
            "candles_verified": None,
            "pass_rate_pct": None,
            "avg_latency_ms": None,
            "last_verdict": "N/D · ZERO-MOCKS: la telemetría de este gate debe medirse, no declararse"
        }
    },
    {
        "gate_number": 4,
        "slug": "gate-4-walk-forward",
        "name": "Walk-Forward Efficiency & Cluster Stability",
        "short_title": "4. Walk-Forward (WFE)",
        "category": "ROBUSTNESS_TEST",
        "badge": "Gate Anti-Sobreajuste",
        "icon": "🔄",
        "formula": "WFE = (Annualized_OOS_Return / Annualized_IS_Return) >= 0.50 (50%)",
        "objective": "Mide si la estrategia mantiene al menos el 50% de su rendimiento en datos no vistos (Out-Of-Sample) frente al In-Sample.",
        "description": "Divide el historial en múltiples bloques temporales secuenciales (Walk-Forward Optimization Matrix) para descartar sobreajuste de curva.",
        "default_params": {
            "min_wfe_ratio": {"label": "Ratio WFE Mínimo", "value": 0.50, "unit": "ratio", "type": "number", "min": 0.30, "max": 0.90, "step": 0.05, "desc": "Eficiencia mínima OOS respecto al periodo de optimización IS."},
            "num_wf_windows": {"label": "Número de Ventanas WFO", "value": 5, "unit": "ventanas", "type": "number", "min": 3, "max": 12, "step": 1, "desc": "Divisiones temporales para validar la consistencia del algoritmo."},
            "max_degradation_pct": {"label": "Degradación Máxima de Sharpe", "value": 40.0, "unit": "%", "type": "number", "min": 10.0, "max": 60.0, "step": 5.0, "desc": "Caída máxima tolerada en el Sharpe Ratio de IS a OOS."},
            "cluster_similarity_threshold": {"label": "Similitud en Clúster de Parámetros", "value": 0.75, "unit": "%", "type": "number", "min": 0.5, "max": 0.95, "step": 0.05, "desc": "Estabilidad de los parámetros óptimos vecinos."}
        },
        "live_telemetry": {
            "status": "SIN TELEMETRÍA REAL CONECTADA",
            "status_color": "#94a3b8",
            "datasets_audited": None,
            "candles_verified": None,
            "pass_rate_pct": None,
            "avg_latency_ms": None,
            "last_verdict": "N/D · ZERO-MOCKS: la telemetría de este gate debe medirse, no declararse"
        }
    },
    {
        "gate_number": 5,
        "slug": "gate-5-monte-carlo",
        "name": "Monte Carlo Resampling & Ruin Risk",
        "short_title": "5. Monte Carlo 1,000x",
        "category": "RISK_ANALYSIS",
        "badge": "Gate de Riesgo Extremo",
        "icon": "🎲",
        "formula": "Risk_of_Ruin_1000sims == 0.0% · Max_DD_95th_Percentile <= Limit_Route",
        "objective": "Genera 1,000 caminos estocásticos permutando el orden de los trades para certificar 0.0% riesgo de ruina y cuantificar el Drawdown percentil 95.",
        "description": "Simulación de remuestreo Bootstrap con reposición y perturbación de slippage aleatorio para predecir el peor escenario en racha de pérdidas consecutivas.",
        "default_params": {
            "simulations_count": {"label": "Número de Simulaciones", "value": 1000, "unit": "it", "type": "number", "min": 500, "max": 10000, "step": 500, "desc": "Iteraciones estocásticas de reordenamiento de trades."},
            "confidence_level_pct": {"label": "Nivel de Confianza de Drawdown", "value": 95.0, "unit": "%", "type": "number", "min": 90.0, "max": 99.0, "step": 1.0, "desc": "Percentil para proyectar el Drawdown máximo probable."},
            "max_allowed_ruin_probability": {"label": "Probabilidad Máxima de Ruina", "value": 0.0, "unit": "%", "type": "number", "min": 0.0, "max": 1.0, "step": 0.1, "desc": "Riesgo de pérdida total de la cuenta en 1,000 simulaciones."},
            "resampling_method": {"label": "Método de Remuestreo", "value": "BOOTSTRAP_WITH_SLIPPAGE", "type": "select", "options": ["BOOTSTRAP_WITH_SLIPPAGE", "RANDOMIZE_ENTRY_PRICES", "BAR_SHUFFLE"], "desc": "Técnica de perturbación estadística."}
        },
        "live_telemetry": {
            "status": "SIN TELEMETRÍA REAL CONECTADA",
            "status_color": "#94a3b8",
            "datasets_audited": None,
            "candles_verified": None,
            "pass_rate_pct": None,
            "avg_latency_ms": None,
            "last_verdict": "N/D · ZERO-MOCKS: la telemetría de este gate debe medirse, no declararse"
        }
    },
    {
        "gate_number": 6,
        "slug": "gate-6-stress-slippage",
        "name": "Stress & Extreme Friction Testing",
        "short_title": "6. Estrés & Slippage 3x",
        "category": "STRESS_TEST",
        "badge": "Gate de Resistencia",
        "icon": "⚡",
        "formula": "PnL_Neto_Stress(Slippage * 2.0x & Fee * 1.5x) > 0 · ROI_Mensual >= 2.0%/m",
        "objective": "Somete la estrategia a condiciones de mercado degradadas (noticias de alto impacto, iliquidez nocturna y flash crashes) duplicando la fricción.",
        "description": "Comprueba si el algoritmo sobrevive a un ensanchamiento repentino de spreads y retardos de ejecución de hasta 300 ms.",
        "default_params": {
            "stress_slippage_multiplier": {"label": "Multiplicador de Slippage", "value": 2.0, "unit": "x", "type": "number", "min": 1.5, "max": 5.0, "step": 0.5, "desc": "Factor de multiplicación del deslizamiento base."},
            "stress_fee_multiplier": {"label": "Multiplicador de Comisiones", "value": 1.5, "unit": "x", "type": "number", "min": 1.0, "max": 3.0, "step": 0.25, "desc": "Sobrecarga de coste por spread o comisión exchange."},
            "simulated_latency_ms": {"label": "Latencia Simulada de Red", "value": 150, "unit": "ms", "type": "number", "min": 10, "max": 1000, "step": 20, "desc": "Retardo entre generación de señal y fill de orden."},
            "min_stressed_profit_factor": {"label": "Profit Factor Mínimo en Estrés", "value": 1.05, "unit": "PF", "type": "number", "min": 1.0, "max": 2.0, "step": 0.05, "desc": "Debe mantenerse estrictamente rentable bajo estrés."}
        },
        "live_telemetry": {
            "status": "SIN TELEMETRÍA REAL CONECTADA",
            "status_color": "#94a3b8",
            "datasets_audited": None,
            "candles_verified": None,
            "pass_rate_pct": None,
            "avg_latency_ms": None,
            "last_verdict": "N/D · ZERO-MOCKS: la telemetría de este gate debe medirse, no declararse"
        }
    },
    {
        "gate_number": 7,
        "slug": "gate-7-regime-coverage",
        "name": "Market Regime Coverage & Stability",
        "short_title": "7. Cobertura de Regímenes",
        "category": "MACRO_REGIME",
        "badge": "Gate Multimercado",
        "icon": "🌐",
        "formula": "Regimes_Evaluated = {BULL_MOMENTUM, BEAR_EXPANSION, LATERAL_CHOP, HIGH_VOL} >= 3",
        "objective": "Asegura que el sistema ha operado y sobrevivido en al menos 3 regímenes de mercado distintos (tendencia alcista, bajista y rango lateral).",
        "description": "Segmentación automática de la serie temporal mediante ADX, ATR Normalizado y Hurst Exponent para auditar el comportamiento en distintas fases de mercado.",
        "default_params": {
            "min_regimes_evaluated": {"label": "Mínimo de Regímenes Probados", "value": 3, "unit": "regímenes", "type": "number", "min": 2, "max": 4, "step": 1, "desc": "Cantidad de entornos de mercado distintos requeridos."},
            "max_loss_in_unfavorable_regime_pct": {"label": "Pérdida Máxima en Régimen Adverso", "value": 15.0, "unit": "%", "type": "number", "min": 5.0, "max": 30.0, "step": 2.5, "desc": "Drawdown máximo permitido en la fase más desfavorable."},
            "adx_trend_threshold": {"label": "Umbral ADX de Tendencia", "value": 25.0, "unit": "pts", "type": "number", "min": 15.0, "max": 40.0, "step": 1.0, "desc": "Punto de corte para clasificar tendencia fuerte vs lateral."},
            "volatility_expansion_ratio": {"label": "Ratio de Expansión de Volatilidad", "value": 1.5, "unit": "ratio", "type": "number", "min": 1.1, "max": 3.0, "step": 0.1, "desc": "Factor de ATR respecto a la media de 50 periodos."}
        },
        "live_telemetry": {
            "status": "SIN TELEMETRÍA REAL CONECTADA",
            "status_color": "#94a3b8",
            "datasets_audited": None,
            "candles_verified": None,
            "pass_rate_pct": None,
            "avg_latency_ms": None,
            "last_verdict": "N/D · ZERO-MOCKS: la telemetría de este gate debe medirse, no declararse"
        }
    },
    {
        "gate_number": 8,
        "slug": "gate-8-dsr-ratio",
        "name": "Deflated Sharpe Ratio (Bailey & López de Prado)",
        "short_title": "8. Deflated Sharpe (DSR)",
        "category": "QUANT_ALGO",
        "badge": "Gate Matemático Avanzado",
        "icon": "📐",
        "formula": "DSR = PSR(Sharpe*, Var[Sharpe], N_Trials, Skewness, Kurtosis) · p_value < 0.05",
        "objective": "Aplica la formulación de Marcos López de Prado para corregir el sesgo de selección y minería de datos por múltiples ensayos (Data Snooping).",
        "description": "Calcula el Sharpe Ratio Deflactado penalizando el número de combinaciones exploradas, la asimetría negativa y el exceso de curtosis de los retornos.",
        "default_params": {
            "min_dsr_score": {"label": "Puntuación DSR Mínima", "value": 1.50, "unit": "DSR", "type": "number", "min": 1.0, "max": 3.0, "step": 0.1, "desc": "Umbral del Deflated Sharpe Ratio tras corrección de ensayos."},
            "max_p_value": {"label": "P-Value Máximo Permitido", "value": 0.05, "unit": "p", "type": "number", "min": 0.001, "max": 0.10, "step": 0.005, "desc": "Probabilidad máxima de que el Sharpe sea producto del azar."},
            "estimated_trials_penalization": {"label": "Ensayos de Búsqueda Estimados", "value": 500, "unit": "trials", "type": "number", "min": 50, "max": 10000, "step": 50, "desc": "Número de estrategias candidatas evaluadas en la campaña."},
            "enforce_skew_kurtosis_adjustment": {"label": "Ajuste por Asimetría & Curtosis", "value": True, "type": "boolean", "desc": "Considera colas pesadas de la distribución de retornos."}
        },
        "live_telemetry": {
            "status": "SIN TELEMETRÍA REAL CONECTADA",
            "status_color": "#94a3b8",
            "datasets_audited": None,
            "candles_verified": None,
            "pass_rate_pct": None,
            "avg_latency_ms": None,
            "last_verdict": "N/D · ZERO-MOCKS: la telemetría de este gate debe medirse, no declararse"
        }
    },
    {
        "gate_number": 9,
        "slug": "gate-9-novelty-antifit",
        "name": "Novelty & Failure DB Inoculation",
        "short_title": "9. Novedad & Inoculación",
        "category": "AI_IMMUNIZATION",
        "badge": "Gate de Inmunización",
        "icon": "🧬",
        "formula": "Distance_to_FailureKnowledgeDB > 0.85 · Structural_Novelty >= 80%",
        "objective": "Verifica contra la base de datos de fallos históricos (FailureKnowledgeDB) que el algoritmo no repite patrones frágiles o trampas de sobreoptimización.",
        "description": "Compara los genes de la estrategia, reglas de entrada/salida y correlación de pérdidas con 11 categorías de fallos cuantitativos conocidos.",
        "default_params": {
            "min_novelty_distance": {"label": "Distancia Mínima a Fallos Conocidos", "value": 0.85, "unit": "dist", "type": "number", "min": 0.50, "max": 0.99, "step": 0.05, "desc": "Distancia vectorial en el espacio de parámetros respecto a estrategias fallidas."},
            "block_known_overfit_trees": {"label": "Bloquear Árboles Sobreoptimizados", "value": True, "type": "boolean", "desc": "Rechaza estructuras de árbol de decisión con profundidad excesiva."},
            "similarity_threshold_to_reject": {"label": "Umbral de Similitud para Descarte", "value": 0.90, "unit": "ratio", "type": "number", "min": 0.70, "max": 0.99, "step": 0.02, "desc": "Si coincide en más de este ratio con un fallo archivado, se descarta."},
            "active_failure_categories": {"label": "Categorías de Fallo Activas", "value": 11, "unit": "cat", "type": "number", "min": 5, "max": 20, "step": 1, "desc": "Patologías cuantitativas monitorizadas en tiempo real."}
        },
        "live_telemetry": {
            "status": "SIN TELEMETRÍA REAL CONECTADA",
            "status_color": "#94a3b8",
            "datasets_audited": None,
            "candles_verified": None,
            "pass_rate_pct": None,
            "avg_latency_ms": None,
            "last_verdict": "N/D · ZERO-MOCKS: la telemetría de este gate debe medirse, no declararse"
        }
    },
    {
        "gate_number": 10,
        "slug": "gate-10-multi-agent-debate",
        "name": "Dynamic 5-Agent Committee Consensus",
        "short_title": "10. Debate 5 Agentes IA",
        "category": "AGENTIC_AI",
        "badge": "Gate Agéntico Semántico",
        "icon": "🤖",
        "formula": "Consensus_Score = (Interpreter + Critic + Improver + Regime + Adversarial) / 5 >= 80.0",
        "objective": "Debate semántico multidisciplinar entre 5 agentes de IA especializados que auditan la tesis de mercado, fragilidad y robustez de la estrategia.",
        "description": "Comité de deliberación en tiempo real: Interpreter Agent (hipótesis), Critic Agent (auditoría), Improver Agent (mutaciones), Regime Analyst (macro) y Adversarial Researcher (estrés).",
        "default_params": {
            "min_consensus_score": {"label": "Puntuación de Consenso Mínima", "value": 80.0, "unit": "pts", "type": "number", "min": 60.0, "max": 95.0, "step": 5.0, "desc": "Promedio ponderado de las evaluaciones de los 5 agentes."},
            "require_adversarial_pass": {"label": "Aprobación Adversarial Obligatoria", "value": True, "type": "boolean", "desc": "El agente adversarial debe dar veredicto favorable sin vetos críticos."},
            "min_improver_ideas": {"label": "Propuestas de Mutación Mínimas", "value": 3, "unit": "ideas", "type": "number", "min": 1, "max": 5, "step": 1, "desc": "Ideas de mejora generadas por el agente de optimización."},
            "debate_rounds": {"label": "Rondas de Deliberación", "value": 3, "unit": "rondas", "type": "number", "min": 1, "max": 5, "step": 1, "desc": "Intercambios dialécticos entre los agentes antes de emitir veredicto."}
        },
        "live_telemetry": {
            "status": "SIN TELEMETRÍA REAL CONECTADA",
            "status_color": "#94a3b8",
            "datasets_audited": None,
            "candles_verified": None,
            "pass_rate_pct": None,
            "avg_latency_ms": None,
            "last_verdict": "N/D · ZERO-MOCKS: la telemetría de este gate debe medirse, no declararse"
        }
    },
    {
        "gate_number": 11,
        "slug": "gate-11-nautilus-trader",
        "name": "NautilusTrader Event-Driven Simulation & Cross Margin",
        "short_title": "11. NautilusTrader Core",
        "category": "EVENT_DRIVEN_ENGINE",
        "badge": "Gate Final Institucional",
        "icon": "⚡",
        "formula": "Liquidation_Distance >= 15.0% · Cross_Margin_Solvent == TRUE · Tick_Event_Execution == PASS",
        "objective": "Simulación evento a evento de grado institucional mediante el motor NautilusTrader (Rust/Cython Core), verificando apalancamiento real, margen cross y colchón a liquidación.",
        "description": "Auditoría definitiva trade a trade con matching engine real, latencia microsegundo, colas de órdenes limit/stop y control exhaustivo de garantías.",
        "default_params": {
            "min_liquidation_cushion_pct": {"label": "Colchón Mínimo a Liquidación", "value": 15.0, "unit": "%", "type": "number", "min": 5.0, "max": 40.0, "step": 2.5, "desc": "Distancia mínima porcentual entre precio de entrada y precio de liquidación."},
            "cross_margin_model": {"label": "Modelo de Margen", "value": "CROSS_ISOLATED_HYBRID", "type": "select", "options": ["CROSS_ISOLATED_HYBRID", "STRICT_ISOLATED", "PORTFOLIO_MARGIN"], "desc": "Régimen de colateral en cuenta."},
            "max_effective_leverage": {"label": "Apalancamiento Efectivo Máximo", "value": 50.0, "unit": "x", "type": "number", "min": 1.0, "max": 500.0, "step": 5.0, "desc": "Techo de apalancamiento real permitido durante la simulación."},
            "fill_model": {"label": "Modelo de Ejecución de Órdenes", "value": "TICK_BY_TICK_QUEUE", "type": "select", "options": ["TICK_BY_TICK_QUEUE", "BAR_MAGNIFIER_1M", "LAST_PRICE_FILL"], "desc": "Resolución del motor de matching."}
        },
        "live_telemetry": {
            "status": "SIN TELEMETRÍA REAL CONECTADA",
            "status_color": "#94a3b8",
            "datasets_audited": None,
            "candles_verified": None,
            "pass_rate_pct": None,
            "avg_latency_ms": None,
            "last_verdict": "N/D · ZERO-MOCKS: la telemetría de este gate debe medirse, no declararse"
        }
    }
]

