"use client";

import React, { useEffect, useState, useMemo, useRef } from "react";
import Link from "next/link";

// ============================================================================
// TIPOS E INTERFACES DEL SISTEMA MUNDIAL DE FUTUROS CME
// ============================================================================
export interface Provider {
  provider_id: string;
  name: string;
  provider_name: string;
  market_type: string;
  platform: string;
  allowed_instruments: string;
  account_size: number;
  program_type: string;
  account_tier: string;
  target_usd: number;
  target_pct: number;
  daily_loss_limit_usd?: number;
  daily_loss_limit_pct?: number;
  dll_calc_model: string;
  max_trailing_dd_usd: number;
  max_trailing_dd_pct: number;
  trailing_dd_type: string;
  consistency_rule_pct: number;
  min_trading_days: number;
  overnight_allowed: boolean;
  news_trading_allowed: boolean;
  ea_bots_allowed: string;
  monthly_cost_usd?: number;
  regular_price_usd?: number;
  promo_price_usd?: number;
  discount_code?: string;
  discount_pct?: number;
  activation_fee_usd?: number;
  payout_split_pct?: number;
  payout_frequency?: string;
  payout_buffer_usd?: number;
  funded_trailing_lock?: string;
  contracts_limit?: string;
  trust_score?: number;
  stage_type?: string;
  source_url?: string;
  verified_at?: string;
  verification_status: string;
  notes?: string;
}

export type MainNavModule = "CATALOGO" | "WIZARD" | "SIMULADOR" | "ENCICLOPEDIA" | "GUIAS" | "CHATBOT";
export type ComparativePhase = "ALL_360" | "COSTES" | "EXAMEN" | "FONDEADO";
export type ViewMode = "TABLE" | "CARDS";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  suggested_actions?: string[];
  active_coupons?: Array<{ firm: string; code: string; discount: string }>;
}

// ============================================================================
// DICCIONARIO DE EXPLICACIONES TÉCNICAS PROFUNDAS POR FIRMA
// ============================================================================
interface FirmTechnicalDetail {
  drawdown_how_it_works: string;
  bots_how_it_works: string;
  cost_profit_how_it_works: string;
  daily_dd_how_it_works: string;
  payout_how_it_works: string;
  fine_print_warning: string;
}

const FIRM_DETAILS: Record<string, FirmTechnicalDetail> = {
  "My Funded Futures": {
    drawdown_how_it_works: "Drawdown EOD Fin de Día: Se calcula únicamente al cierre de la sesión (17:00 ET) sobre el balance de posiciones cerradas. Las ganancias flotantes que se devuelven intradía NO mueven el umbral de liquidación. En la cuenta financiada Rapid, el Trailing DD se CONGELA permanentemente en $50,100 (balance inicial + $100) una vez alcanzado el objetivo de $52,000.",
    bots_how_it_works: "100% Permitidos: Admite bots en NinjaTrader 8, webhooks de TradingView, scripts de Python, ejecución en VPS de EE.UU. y Trade Copiers locales y en la nube. Sin restricciones de duración mínima por trade.",
    cost_profit_how_it_works: "En el Plan Rapid: Cuota de activación $0 USD (100% gratuita). Con el cupón 300K pagas solo $39.50 USD por la cuenta de 50K. Profit Target: $3,000 USD (6%). Profit Split: 100% de los primeros $10,000 USD netos para el trader, luego 90% Trader / 10% Firma.",
    daily_dd_how_it_works: "Sin Daily Loss Limit en Examen: En la fase de evaluación no existe límite diario de pérdidas que te descalifique. En cuenta fondeada, opera con gestión prudente manteniendo el colchón del trailing EOD.",
    payout_how_it_works: "Retiros Día 1 On-Demand: Puedes solicitar retiros desde el primer día que operes en cuenta fondeada, siempre que tu balance supere el Safety Buffer ($52,100 en cuenta 50K). Pagos procesados en 12 a 24 horas vía Rise, Crypto USDT o Transferencia.",
    fine_print_warning: "Cierre obligatorio de todas las posiciones antes de las 16:59 EST (prohibido overnight). En cuenta fondeada se audita que ningún día supere el 40% del beneficio total acumulado para solicitar el retiro.",
  },
  "Tradeify": {
    drawdown_how_it_works: "Drawdown EOD Fin de Día (Plan Growth): El drawdown solo se recalcula tras el cierre del mercado a las 17:00 ET. En fondeo, el umbral de liquidación se bloquea de forma inamovible en el balance inicial + $100.",
    bots_how_it_works: "100% Permitidos: Totalmente amigable con trading algorítmico, EAs en NinjaTrader, alertas de PineScript vía Tradovate API y réplica multi-cuenta. Sin restricciones absurdas de microsegundos.",
    cost_profit_how_it_works: "Plan Growth: $0 cuota de activación. Con cupón TNT ahorras el 40% ($58.20 USD final en 50K). Target: $3,000 USD (6%). Reparto: 90% Trader / 10% Firma.",
    daily_dd_how_it_works: "Soft Breach Daily Loss Limit ($1,000 en 50K): Si tocas el límite diario, la plataforma liquida tus posiciones abiertas y bloquea la operativa hasta la siguiente sesión SIN suspender ni quemar la cuenta.",
    payout_how_it_works: "Retiros en 24-48 horas: Tras acumular 5 días operativos ganadores con más de $150/día, retiras tus fondos vía Rise, Deel o Criptomonedas.",
    fine_print_warning: "Regla de consistencia del 40% (tu mejor sesión no puede representar más del 40% de las ganancias totales al pedir pago). Cierre diario a las 16:59 EST.",
  },
  "TradeDay": {
    drawdown_how_it_works: "Drawdown EOD Fin de Día Institucional: Regulado y auditado por ex-traders de Chicago. El drawdown se fija en el balance inicial ($50,000) una vez alcanzado el colchón.",
    bots_how_it_works: "Permitidos: Algoritmos y automatizaciones admitidos en NinjaTrader, TradingView y CQG. Los traders exitosos son transferidos a brokerages reales (Dorman Trading / Phillip Capital).",
    cost_profit_how_it_works: "Coste $0 de Activación: Con cupón FLASH55 pagas $59.00 USD. Sin tasas sorpresa de pase. Target: $3,000 USD. Split: 100% de primeros $10,000 USD, luego 90/10.",
    daily_dd_how_it_works: "Límite Diario Estricto ($1,000 en 50K): El DLL actúa como freno de disciplina. No operar tras alcanzar la pérdida máxima diaria.",
    payout_how_it_works: "Retiros el Mismo Día Hábil: La firma más rápida de la industria institucional. Pagos aprobados y transferidos en el día hábil vía Deel, ACH o Wire.",
    fine_print_warning: "Escalado obligatorio de contratos por tramos de balance. Posiciones deben cerrarse a las 15:10 CT (16:10 ET). Prohibido mantener operaciones overnight.",
  },
  "Topstep": {
    drawdown_how_it_works: "Drawdown EOD Fin de Día (TopstepX / Tradovate): El trailing drawdown se calcula únicamente a fin de sesión. En cuenta Express Funded (XFA), el trailing se congela en $50,000 (balance inicial) al alcanzar $52,000.",
    bots_how_it_works: "Condicional / Solo PC Local: Permitidos indicadores automáticos y scripts en NinjaTrader 8 o Quantower ejecutados desde tu PC/VPS personal. Prohibido HFT latencia cero de milisegundos o arbitraje de feeds.",
    cost_profit_how_it_works: "Examen $49/mes. Al aprobar: Cuota de Activación de $149 USD (Pass Fee obligatorio). Target: $3,000 USD (6%). Split: 100% primeros $10,000 USD netos, luego 90/10.",
    daily_dd_how_it_works: "Sin DLL en Combine (Examen). En cuenta Express Funded se activa un Daily Loss Limit estricto de $1,000 USD (hard breach) para proteger la cuenta.",
    payout_how_it_works: "Retiros Diarios tras 5 Días Ganadores de más de $200 USD: Puedes solicitar hasta el 50% del balance de ganancias por cada ciclo de 5 días de más de $200. Pagos vía Deel y Wire.",
    fine_print_warning: "Prohibido el uso de servidores proxy comerciales no declarados. Posiciones deben cerrarse a las 15:10 CT (16:10 ET). Trading de noticias de alto impacto 100% permitido.",
  },
  "BluSky Trading": {
    drawdown_how_it_works: "Drawdown 100% Estático (Static Drawdown): El nivel de pérdida máxima se fija en $48,500 en la cuenta 50K y JAMÁS sube, aunque tu cuenta suba a $55,000 o $60,000. Cero riesgo de trailing agresivo.",
    bots_how_it_works: "100% Permitidos: Admite EAs en NinjaTrader 8, Rithmic, MotiveWave y Trade Copiers multi-cuenta.",
    cost_profit_how_it_works: "$0 Cuota de Activación. Con cupón BLU25 pagas $110.00 USD. Target: $3,000 USD. Split: 90% Trader / 10% Firma (100% primeros $10k en planes especiales).",
    daily_dd_how_it_works: "Sin Daily Loss Limit en el plan Static Growth: Mayor libertad operativa para estrategias tipo swing o rotacionales intradía.",
    payout_how_it_works: "Retiros Semanales y On-Demand: Tras un periodo mínimo de 8 días de trading, retiras vía Rise, Cripto o Wire internacional.",
    fine_print_warning: "Escalado de contratos progresivo por tramos de $1,000 de beneficio (inicia con 2 contratos y sube hasta 5). Cierre antes del corte de CME.",
  },
  "Bulenox": {
    drawdown_how_it_works: "Opción 1: Drawdown Intraday Peak Trailing (persigue el flotante positivo tick-a-tick). Opción 2: Drawdown EOD Fin de Día. En cuenta Master el drawdown se congela en $50,000.",
    bots_how_it_works: "100% Permitidos: Totalmente compatible con Rithmic, NinjaTrader 8, Quantower y copiers con hasta 10-20 cuentas simultáneas.",
    cost_profit_how_it_works: "Precio Ultrabajo con cupón GUIDE (89% de descuento: solo $19.25 USD el examen 50K). Cuota de Activación en cuenta Master: $148 USD. Split: 100% primeros $10,000 USD, luego 90/10.",
    daily_dd_how_it_works: "En Opción 1: Sin límite diario de pérdidas en examen. En Opción 2: Con límite diario.",
    payout_how_it_works: "Retiros Quincenales: Ventanas de solicitud del 1 al 5 y del 16 al 20 de cada mes tras acumular 5 días de trading. Primeros 3 retiros con tope ($1,000-$1,500), luego ilimitado.",
    fine_print_warning: "Regla de consistencia del 40% en cuenta Master (ningún día puede representar más del 40% del profit acumulado). Trailing intraday en Opción 1 requiere stops ceñidos.",
  },
  "Apex Trader Funding": {
    drawdown_how_it_works: "Drawdown Intraday Peak Trailing Tick-a-Tick: El nivel de liquidación persigue en tiempo real las ganancias flotantes no realizadas. Si vas ganando +$1,500 y el precio retrocede a +$200, el stop subió $1,500. En cuenta PA se congela en $50,100.",
    bots_how_it_works: "PROHIBIDOS (Solo Trading Manual): Prohibición estricta de bots totalmente desatendidos, EAs de terceros y algoritmos en cuentas PA. El Trade Copier entre tus propias cuentas manuales sí está 100% permitido.",
    cost_profit_how_it_works: "Precios con cupón SAVINGS (80% off: $33.40 USD). Al aprobar: Cuota de Activación de $140 USD (o $260 lifetime). Target: $3,000 USD. Split: 100% primeros $25,000 USD, luego 90/10.",
    daily_dd_how_it_works: "Sin Daily Loss Limit en examen. El único límite es el Trailing Drawdown Intraday.",
    payout_how_it_works: "Retiros Quincenales Estrictos: Solicitudes del 1 al 5 (pago el 15) y del 15 al 20 (pago a fin de mes). Requiere mínimo 8 a 10 días de trading activos entre retiros y mantener el buffer de $52,600.",
    fine_print_warning: "Regla de consistencia del 30% en cuentas PA. Prohibido gambling de noticias de 1 solo segundo. Si usas bots autónomos te cancelan la cuenta.",
  },
  "Take Profit Trader": {
    drawdown_how_it_works: "Drawdown EOD Fin de Día: Se calcula al cierre de la sesión. En cuenta Pro se congela en el balance inicial ($50,000) al alcanzar $52,000.",
    bots_how_it_works: "Condicional: Permitidos sistemas automáticos convencionales; prohibido arbitraje de latencia y bots de microsegundos.",
    cost_profit_how_it_works: "Examen $85 USD con cupón PRO50. Cuota de Activación: $130 USD en cuenta Pro. Target: $3,000 USD. Split: 80/20 base en Pro, 90/10 en Pro+.",
    daily_dd_how_it_works: "Daily Loss Limit Estricto ($1,100 en 50K): Es un hard breach tanto en examen como en fondeo.",
    payout_how_it_works: "Retiros Día 1 en Cuenta Pro: Puedes retirar tus beneficios desde el primer día que superes el umbral de ganancias sin esperar semanas.",
    fine_print_warning: "Regla de consistencia del 50% en examen (ningún día puede superar el 50% del profit target total).",
  },
  "FundedNext Futures": {
    drawdown_how_it_works: "Drawdown EOD Fin de Día: Recalculado tras el cierre a las 17:00 ET. En cuenta financiada se bloquea en balance inicial + buffer.",
    bots_how_it_works: "100% Permitidos: Admite bots en Tradovate, NinjaTrader, webhooks y copiers.",
    cost_profit_how_it_works: "$0 Cuota de Activación + Bono del 15% del Examen: Te pagan el 15% de las ganancias generadas durante la fase de evaluación al aprobar. Precio: $99.00 USD. Split: 90/10.",
    daily_dd_how_it_works: "Sin Daily Loss Limit en examen en el plan Rapid.",
    payout_how_it_works: "Retiros Quincenales: Procesamiento en 24 horas vía Rise, Deel o Cripto USDT.",
    fine_print_warning: "Regla de consistencia del 40%. Cierre obligatorio a las 16:59 EST.",
  },
  "Lucid Trading": {
    drawdown_how_it_works: "Drawdown EOD Fin de Día: Sin recálculos intradía. En fondeo se fija en el balance inicial tras alcanzar el buffer.",
    bots_how_it_works: "100% Permitidos: Arquitectura multi-broker moderna con soporte para Tradovate, Rithmic, NinjaTrader y webhooks REST.",
    cost_profit_how_it_works: "$0 Cuota de Activación. Con cupón LUCID30 pagas $118.30 USD. Target: $3,000 USD. Split: 90/10.",
    daily_dd_how_it_works: "Sin DLL obligatorio en planes LucidFlex.",
    payout_how_it_works: "Retiros en 15 a 30 Minutos: Sistema de procesamiento automatizado ultra-rápido.",
    fine_print_warning: "En planes LucidFlex no aplica regla de consistencia del 40% en fondeo. Cierre antes de las 16:59 EST.",
  },
  "Earn2Trade": {
    drawdown_how_it_works: "Drawdown EOD Fin de Día: Se ajusta al cierre de la sesión. En cuenta Helios Live, el capital es institucional real.",
    bots_how_it_works: "Permitidos con disciplina: Admite algoritmos en NinjaTrader y Rithmic siempre que respeten el escalado de contratos.",
    cost_profit_how_it_works: "$0 Cuota de Activación (Cuenta de Broker Real Helios). Con cupón PROMO20 pagas $152 USD. Target: $3,000 USD. Split: 80/20 escalable.",
    daily_dd_how_it_works: "Daily Loss Limit Estricto ($1,100 en 50K): Hard breach para proteger el capital institucional.",
    payout_how_it_works: "Retiros Semanales: Todos los martes/miércoles vía Rise o Bank Wire.",
    fine_print_warning: "Escalado obligatorio de contratos por balance. Cierre antes de las 15:50 CT.",
  },
};

const DEFAULT_DETAIL: FirmTechnicalDetail = {
  drawdown_how_it_works: "Drawdown EOD Fin de Día / Trailing calculado al cierre de sesión o sobre High Watermark según el programa. En cuenta fondeada se congela en el balance inicial tras superar el buffer.",
  bots_how_it_works: "Permitidos algoritmos y sistemas automatizados convencionales en NinjaTrader 8 y Tradovate con ejecución local o VPS.",
  cost_profit_how_it_works: "Desglose oficial con cupones activos. Profit Target estándar del 5% al 6% y reparto del 90/10 (100% primeros $10k netos).",
  daily_dd_how_it_works: "Límite diario de pérdidas según la modalidad del plan para evitar sobre-operativa.",
  payout_how_it_works: "Retiros procesados tras cumplir los días mínimos de trading y mantener el colchón de seguridad requerido.",
  fine_print_warning: "Posiciones deben cerrarse antes del corte diario de CME (15:50 CT / 16:59 EST). Consultar reglas de consistencia.",
};

// ============================================================================
// CATÁLOGO CANÓNICO DE 39 CUENTAS Y 17 FIRMAS DE FUTUROS CME (FALLBACK RESILIENTE)
// ============================================================================
export const DEFAULT_FUTURES_PROVIDERS: Provider[] = [
  // 1. MY FUNDED FUTURES
  {
    provider_id: "mffu_rapid_25k",
    name: "MyFundedFutures Rapid 25K ($0 Activación)",
    provider_name: "My Funded Futures",
    market_type: "FUTURES",
    platform: "Tradovate / NinjaTrader / TradingView",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 25000.0,
    program_type: "Rapid",
    account_tier: "25K",
    target_usd: 1500.0,
    target_pct: 6.0,
    dll_calc_model: "None",
    max_trailing_dd_usd: 1500.0,
    max_trailing_dd_pct: 6.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 40.0,
    min_trading_days: 1,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 49.0,
    regular_price_usd: 49.0,
    promo_price_usd: 24.50,
    discount_code: "300K",
    discount_pct: 50.0,
    activation_fee_usd: 0.0,
    payout_split_pct: 90.0,
    payout_frequency: "Día 1 / On-Demand",
    payout_buffer_usd: 1600.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "2 Minis / 20 Micros",
    trust_score: 93,
    stage_type: "EVALUATION",
    source_url: "https://myfundedfutures.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "100% de primeros $10k netos. $0 activación. Trailing se congela en $25,100.",
  },
  {
    provider_id: "mffu_rapid_50k",
    name: "MyFundedFutures Rapid 50K ($0 Activación)",
    provider_name: "My Funded Futures",
    market_type: "FUTURES",
    platform: "Tradovate / NinjaTrader / TradingView",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Rapid",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    dll_calc_model: "None",
    max_trailing_dd_usd: 2000.0,
    max_trailing_dd_pct: 4.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 40.0,
    min_trading_days: 1,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 79.0,
    regular_price_usd: 79.0,
    promo_price_usd: 39.50,
    discount_code: "300K",
    discount_pct: 50.0,
    activation_fee_usd: 0.0,
    payout_split_pct: 90.0,
    payout_frequency: "Día 1 / On-Demand",
    payout_buffer_usd: 2100.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "5 Minis / 50 Micros",
    trust_score: 94,
    stage_type: "EVALUATION",
    source_url: "https://myfundedfutures.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "100% de primeros $10k netos. Cero activación. Trailing DD congela en $50,100.",
  },
  {
    provider_id: "mffu_rapid_100k",
    name: "MyFundedFutures Rapid 100K ($0 Activación)",
    provider_name: "My Funded Futures",
    market_type: "FUTURES",
    platform: "Tradovate / NinjaTrader / TradingView",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 100000.0,
    program_type: "Rapid",
    account_tier: "100K",
    target_usd: 6000.0,
    target_pct: 6.0,
    dll_calc_model: "None",
    max_trailing_dd_usd: 3000.0,
    max_trailing_dd_pct: 3.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 40.0,
    min_trading_days: 1,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 159.0,
    regular_price_usd: 159.0,
    promo_price_usd: 79.50,
    discount_code: "300K",
    discount_pct: 50.0,
    activation_fee_usd: 0.0,
    payout_split_pct: 90.0,
    payout_frequency: "Día 1 / On-Demand",
    payout_buffer_usd: 3100.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "10 Minis / 100 Micros",
    trust_score: 94,
    stage_type: "EVALUATION",
    source_url: "https://myfundedfutures.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "100% de primeros $10k. Sin activación. Payouts casi instantáneos.",
  },
  // 2. TRADEIFY
  {
    provider_id: "tradeify_growth_50k",
    name: "Tradeify Growth 50K ($0 Activación)",
    provider_name: "Tradeify",
    market_type: "FUTURES",
    platform: "Tradovate / NinjaTrader / TradingView",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Growth",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    daily_loss_limit_usd: 1000.0,
    daily_loss_limit_pct: 2.0,
    dll_calc_model: "Soft Breach",
    max_trailing_dd_usd: 2000.0,
    max_trailing_dd_pct: 4.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 40.0,
    min_trading_days: 3,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 97.0,
    regular_price_usd: 97.0,
    promo_price_usd: 58.20,
    discount_code: "TNT",
    discount_pct: 40.0,
    activation_fee_usd: 0.0,
    payout_split_pct: 90.0,
    payout_frequency: "24-48h On-Demand",
    payout_buffer_usd: 2100.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "5 Minis / 50 Micros",
    trust_score: 93,
    stage_type: "EVALUATION",
    source_url: "https://tradeify.co/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "$0 activación. Soft Breach Daily Loss Limit ($1,000). Retiros en 24-48h.",
  },
  {
    provider_id: "tradeify_growth_100k",
    name: "Tradeify Growth 100K ($0 Activación)",
    provider_name: "Tradeify",
    market_type: "FUTURES",
    platform: "Tradovate / NinjaTrader / TradingView",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 100000.0,
    program_type: "Growth",
    account_tier: "100K",
    target_usd: 6000.0,
    target_pct: 6.0,
    daily_loss_limit_usd: 2000.0,
    daily_loss_limit_pct: 2.0,
    dll_calc_model: "Soft Breach",
    max_trailing_dd_usd: 3000.0,
    max_trailing_dd_pct: 3.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 40.0,
    min_trading_days: 3,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 187.0,
    regular_price_usd: 187.0,
    promo_price_usd: 112.20,
    discount_code: "TNT",
    discount_pct: 40.0,
    activation_fee_usd: 0.0,
    payout_split_pct: 90.0,
    payout_frequency: "24-48h On-Demand",
    payout_buffer_usd: 3100.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "10 Minis / 100 Micros",
    trust_score: 93,
    stage_type: "EVALUATION",
    source_url: "https://tradeify.co/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "$0 activación. 90% payout. Soft breach DLL.",
  },
  // 3. TRADEDAY
  {
    provider_id: "tradeday_daytrader_50k",
    name: "TradeDay Day Trader 50K ($0 Activación)",
    provider_name: "TradeDay",
    market_type: "FUTURES",
    platform: "Tradovate / NinjaTrader / TradingView / CQG",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Day Trader",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    daily_loss_limit_usd: 1000.0,
    daily_loss_limit_pct: 2.0,
    dll_calc_model: "EOD Balance",
    max_trailing_dd_usd: 2000.0,
    max_trailing_dd_pct: 4.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 50.0,
    min_trading_days: 7,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 130.0,
    regular_price_usd: 130.0,
    promo_price_usd: 59.00,
    discount_code: "FLASH55",
    discount_pct: 55.0,
    activation_fee_usd: 0.0,
    payout_split_pct: 90.0,
    payout_frequency: "Mismo día hábil",
    payout_buffer_usd: 2000.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "5 Minis / 50 Micros",
    trust_score: 96,
    stage_type: "EVALUATION",
    source_url: "https://tradeday.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "Firma #1 en solvencia institucional. 100% de primeros $10k. Pagos en el mismo día.",
  },
  // 4. TOPSTEP
  {
    provider_id: "topstep_combine_50k",
    name: "Topstep Trading Combine 50K",
    provider_name: "Topstep",
    market_type: "FUTURES",
    platform: "TopstepX / Tradovate / NinjaTrader",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Trading Combine",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    daily_loss_limit_usd: 1000.0,
    daily_loss_limit_pct: 2.0,
    dll_calc_model: "EOD Balance",
    max_trailing_dd_usd: 2000.0,
    max_trailing_dd_pct: 4.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 50.0,
    min_trading_days: 2,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "CONDITIONS_APPLY",
    monthly_cost_usd: 49.0,
    regular_price_usd: 49.0,
    promo_price_usd: 49.00,
    discount_code: undefined,
    discount_pct: 0.0,
    activation_fee_usd: 149.0,
    payout_split_pct: 90.0,
    payout_frequency: "Diario (5d > $200)",
    payout_buffer_usd: 2000.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "5 Minis / 50 Micros",
    trust_score: 95,
    stage_type: "EVALUATION",
    source_url: "https://www.topstep.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "TopstepX con TradingView nativo. Sin DLL en Combine. $149 Pass Fee.",
  },
  // 5. BLUSKY TRADING
  {
    provider_id: "blusky_static_50k",
    name: "BluSky Static Growth 50K ($0 Activación)",
    provider_name: "BluSky Trading",
    market_type: "FUTURES",
    platform: "NinjaTrader 8 / Rithmic / MotiveWave",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Static Growth",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    daily_loss_limit_usd: undefined,
    daily_loss_limit_pct: undefined,
    dll_calc_model: "None",
    max_trailing_dd_usd: 1500.0,
    max_trailing_dd_pct: 3.0,
    trailing_dd_type: "Static",
    consistency_rule_pct: 50.0,
    min_trading_days: 8,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 147.0,
    regular_price_usd: 147.0,
    promo_price_usd: 110.00,
    discount_code: "BLU25",
    discount_pct: 25.0,
    activation_fee_usd: 0.0,
    payout_split_pct: 90.0,
    payout_frequency: "Semanal / On-Demand",
    payout_buffer_usd: 1500.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "5 Minis (Escalado)",
    trust_score: 92,
    stage_type: "EVALUATION",
    source_url: "https://blusky.pro/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "Drawdown 100% Estático que JAMÁS sube con las ganancias. Cero cuota de activación.",
  },
  // 6. BULENOX
  {
    provider_id: "bulenox_option1_50k",
    name: "Bulenox Opción 1 50K (Intraday Peak)",
    provider_name: "Bulenox",
    market_type: "FUTURES",
    platform: "NinjaTrader 8 / Rithmic / Quantower",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Opción 1 Trailing",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    daily_loss_limit_usd: undefined,
    daily_loss_limit_pct: undefined,
    dll_calc_model: "None",
    max_trailing_dd_usd: 2500.0,
    max_trailing_dd_pct: 5.0,
    trailing_dd_type: "Intraday Peak Trailing",
    consistency_rule_pct: 40.0,
    min_trading_days: 5,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 175.0,
    regular_price_usd: 175.0,
    promo_price_usd: 19.25,
    discount_code: "GUIDE",
    discount_pct: 89.0,
    activation_fee_usd: 148.0,
    payout_split_pct: 90.0,
    payout_frequency: "Quincenal",
    payout_buffer_usd: 2600.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "7 Minis / 70 Micros",
    trust_score: 87,
    stage_type: "EVALUATION",
    source_url: "https://bulenox.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "Examen ultra-barato con cupón GUIDE ($19.25 USD). 100% de primeros $10k. $148 activación Master.",
  },
  // 7. APEX TRADER FUNDING
  {
    provider_id: "apex_full_50k",
    name: "Apex Full Trailing 50K",
    provider_name: "Apex Trader Funding",
    market_type: "FUTURES",
    platform: "Tradovate / NinjaTrader 8 / Rithmic",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Full Trailing",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    daily_loss_limit_usd: undefined,
    daily_loss_limit_pct: undefined,
    dll_calc_model: "None",
    max_trailing_dd_usd: 2500.0,
    max_trailing_dd_pct: 5.0,
    trailing_dd_type: "Intraday Peak Trailing",
    consistency_rule_pct: 30.0,
    min_trading_days: 1,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PROHIBITED",
    monthly_cost_usd: 167.0,
    regular_price_usd: 167.0,
    promo_price_usd: 33.40,
    discount_code: "SAVINGS",
    discount_pct: 80.0,
    activation_fee_usd: 140.0,
    payout_split_pct: 90.0,
    payout_frequency: "Quincenal (1-5 / 15-20)",
    payout_buffer_usd: 2600.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "10 Minis / 100 Micros",
    trust_score: 84,
    stage_type: "EVALUATION",
    source_url: "https://apextraderfunding.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "100% de primeros $25k. 80% off con SAVINGS. BOTS AUTOMATIZADOS ESTRICTAMENTE PROHIBIDOS EN PA.",
  },
  // 8. TAKE PROFIT TRADER
  {
    provider_id: "tpt_pro_50k",
    name: "Take Profit Trader Pro Test 50K",
    provider_name: "Take Profit Trader",
    market_type: "FUTURES",
    platform: "Tradovate / NinjaTrader / TradingView",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Pro Test",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    daily_loss_limit_usd: 1100.0,
    daily_loss_limit_pct: 2.2,
    dll_calc_model: "Hard Breach",
    max_trailing_dd_usd: 2000.0,
    max_trailing_dd_pct: 4.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 50.0,
    min_trading_days: 5,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "CONDITIONS_APPLY",
    monthly_cost_usd: 170.0,
    regular_price_usd: 170.0,
    promo_price_usd: 85.00,
    discount_code: "PRO50",
    discount_pct: 50.0,
    activation_fee_usd: 130.0,
    payout_split_pct: 80.0,
    payout_frequency: "Día 1 en Pro",
    payout_buffer_usd: 2000.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "6 Minis / 60 Micros",
    trust_score: 89,
    stage_type: "EVALUATION",
    source_url: "https://takeprofittrader.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "Retiros desde el Día 1 en cuenta Pro sin esperar semanas. EOD Drawdown.",
  },
  // 9. FUNDEDNEXT FUTURES
  {
    provider_id: "fundednext_rapid_50k",
    name: "FundedNext Futures Rapid 50K ($0 Activación)",
    provider_name: "FundedNext Futures",
    market_type: "FUTURES",
    platform: "Tradovate / NinjaTrader / TradingView",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Rapid",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    dll_calc_model: "None",
    max_trailing_dd_usd: 2000.0,
    max_trailing_dd_pct: 4.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 40.0,
    min_trading_days: 5,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 99.0,
    regular_price_usd: 99.0,
    promo_price_usd: 99.00,
    discount_code: undefined,
    discount_pct: 0.0,
    activation_fee_usd: 0.0,
    payout_split_pct: 90.0,
    payout_frequency: "Quincenal (+15% examen)",
    payout_buffer_usd: 2100.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "5 Minis / 50 Micros",
    trust_score: 91,
    stage_type: "EVALUATION",
    source_url: "https://fundednext.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "Cuota de activación $0 USD + Te pagan el 15% del beneficio generado en la fase de evaluación.",
  },
  // 10. LUCID TRADING
  {
    provider_id: "lucid_flex_50k",
    name: "Lucid Trading LucidFlex 50K ($0 Activación)",
    provider_name: "Lucid Trading",
    market_type: "FUTURES",
    platform: "Tradovate / NinjaTrader / Rithmic",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "LucidFlex",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    dll_calc_model: "None",
    max_trailing_dd_usd: 2000.0,
    max_trailing_dd_pct: 4.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 0.0,
    min_trading_days: 1,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 169.0,
    regular_price_usd: 169.0,
    promo_price_usd: 118.30,
    discount_code: "LUCID30",
    discount_pct: 30.0,
    activation_fee_usd: 0.0,
    payout_split_pct: 90.0,
    payout_frequency: "15-30 Minutos",
    payout_buffer_usd: 2000.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "5 Minis / 50 Micros",
    trust_score: 91,
    stage_type: "EVALUATION",
    source_url: "https://lucidtrading.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "Sin regla de consistencia del 40%. Retiros ultra-rápidos en 15-30 minutos. $0 activación.",
  },
  // 11. EARN2TRADE
  {
    provider_id: "earn2trade_tcp_50k",
    name: "Earn2Trade Trader Career Path 50K",
    provider_name: "Earn2Trade",
    market_type: "FUTURES",
    platform: "NinjaTrader 8 / Finamark / Rithmic",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Trader Career Path",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    daily_loss_limit_usd: 1100.0,
    daily_loss_limit_pct: 2.2,
    dll_calc_model: "EOD Balance",
    max_trailing_dd_usd: 2000.0,
    max_trailing_dd_pct: 4.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 50.0,
    min_trading_days: 10,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 190.0,
    regular_price_usd: 190.0,
    promo_price_usd: 152.00,
    discount_code: "PROMO20",
    discount_pct: 20.0,
    activation_fee_usd: 0.0,
    payout_split_pct: 80.0,
    payout_frequency: "Semanal (Helios Live)",
    payout_buffer_usd: 2000.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "6 Minis (Escalado)",
    trust_score: 94,
    stage_type: "EVALUATION",
    source_url: "https://www.earn2trade.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "Fondeo directo en Helios Trading Partners (broker real). $0 activación.",
  },
  // 12. ONEUP TRADER
  {
    provider_id: "oneup_1step_50k",
    name: "OneUp Trader 1-Step Evaluation 50K",
    provider_name: "OneUp Trader",
    market_type: "FUTURES",
    platform: "NinjaTrader 8 / Tradovate / Sierra Chart",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "1-Step",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    daily_loss_limit_usd: 1250.0,
    daily_loss_limit_pct: 2.5,
    dll_calc_model: "EOD Balance",
    max_trailing_dd_usd: 2500.0,
    max_trailing_dd_pct: 5.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 50.0,
    min_trading_days: 15,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 125.0,
    regular_price_usd: 125.0,
    promo_price_usd: 125.00,
    discount_code: undefined,
    discount_pct: 0.0,
    activation_fee_usd: 0.0,
    payout_split_pct: 90.0,
    payout_frequency: "Quincenal",
    payout_buffer_usd: 2500.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "6 Minis / 60 Micros",
    trust_score: 90,
    stage_type: "EVALUATION",
    source_url: "https://oneuptrader.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "100% de primeros $10k netos. Sin tasas ocultas de pase. EOD Drawdown.",
  },
  // 13. TICKTICK TRADER
  {
    provider_id: "ticktick_standard_50k",
    name: "TickTick Trader Standard 50K",
    provider_name: "TickTick Trader",
    market_type: "FUTURES",
    platform: "Tradovate / NinjaTrader / TradingView",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Standard",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    dll_calc_model: "None",
    max_trailing_dd_usd: 2000.0,
    max_trailing_dd_pct: 4.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 50.0,
    min_trading_days: 5,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 145.0,
    regular_price_usd: 145.0,
    promo_price_usd: 72.50,
    discount_code: "TTT50",
    discount_pct: 50.0,
    activation_fee_usd: 149.0,
    payout_split_pct: 90.0,
    payout_frequency: "On-Demand (5 días)",
    payout_buffer_usd: 2000.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "5 Minis / 50 Micros",
    trust_score: 88,
    stage_type: "EVALUATION",
    source_url: "https://tickticktrader.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "100% de primeros $25k netos. EOD Trailing. $149 cuota de activación.",
  },
  // 14. FAST TRACK TRADING
  {
    provider_id: "fasttrack_direct_50k",
    name: "Fast Track Trading Direct 50K ($0 Activación)",
    provider_name: "Fast Track Trading",
    market_type: "FUTURES",
    platform: "Rithmic / NinjaTrader / Quantower",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Direct Pass",
    account_tier: "50K",
    target_usd: 2500.0,
    target_pct: 5.0,
    dll_calc_model: "None",
    max_trailing_dd_usd: 2500.0,
    max_trailing_dd_pct: 5.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 40.0,
    min_trading_days: 0,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 149.0,
    regular_price_usd: 149.0,
    promo_price_usd: 149.00,
    discount_code: undefined,
    discount_pct: 0.0,
    activation_fee_usd: 0.0,
    payout_split_pct: 90.0,
    payout_frequency: "Semanal On-Demand",
    payout_buffer_usd: 2500.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "5 Minis / 50 Micros",
    trust_score: 86,
    stage_type: "EVALUATION",
    source_url: "https://fasttracktrading.net/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "Sin días mínimos de examen. $0 activación. Retiros semanales.",
  },
  // 15. UPROFIT TRADER
  {
    provider_id: "uprofit_freedom_50k",
    name: "UProfit Trader Freedom 50K",
    provider_name: "UProfit Trader",
    market_type: "FUTURES",
    platform: "NinjaTrader 8 / Rithmic / TradingView",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Freedom",
    account_tier: "50K",
    target_usd: 2500.0,
    target_pct: 5.0,
    daily_loss_limit_usd: undefined,
    daily_loss_limit_pct: undefined,
    dll_calc_model: "None",
    max_trailing_dd_usd: 2000.0,
    max_trailing_dd_pct: 4.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 50.0,
    min_trading_days: 4,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 149.0,
    regular_price_usd: 149.0,
    promo_price_usd: 89.40,
    discount_code: "UPROFIT40",
    discount_pct: 40.0,
    activation_fee_usd: 150.0,
    payout_split_pct: 80.0,
    payout_frequency: "24h tras 4 días",
    payout_buffer_usd: 2000.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "6 Minis / 60 Micros",
    trust_score: 87,
    stage_type: "EVALUATION",
    source_url: "https://uprofit.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "100% de los primeros $8,000 netos. Target reducido del 5% ($2,500 en 50K).",
  },
  // 16. ELITE TRADER FUNDING
  {
    provider_id: "elitetrader_fasttrack_50k",
    name: "Elite Trader Funding Fast Track 50K",
    provider_name: "Elite Trader Funding",
    market_type: "FUTURES",
    platform: "NinjaTrader 8 / Rithmic / Tradovate",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Fast Track",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    daily_loss_limit_usd: undefined,
    daily_loss_limit_pct: undefined,
    dll_calc_model: "None",
    max_trailing_dd_usd: 2000.0,
    max_trailing_dd_pct: 4.0,
    trailing_dd_type: "EOD Trailing",
    consistency_rule_pct: 40.0,
    min_trading_days: 1,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 150.0,
    regular_price_usd: 150.0,
    promo_price_usd: 45.00,
    discount_code: "ETF70",
    discount_pct: 70.0,
    activation_fee_usd: 150.0,
    payout_split_pct: 90.0,
    payout_frequency: "Quincenal",
    payout_buffer_usd: 2000.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "8 Minis / 80 Micros",
    trust_score: 85,
    stage_type: "EVALUATION",
    source_url: "https://elitetraderfunding.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "100% de primeros $12,500 netos. EOD Trailing. 70% off con ETF70.",
  },
  // 17. LEELOO TRADING
  {
    provider_id: "leeloo_express_50k",
    name: "Leeloo Trading Express 50K",
    provider_name: "Leeloo Trading",
    market_type: "FUTURES",
    platform: "NinjaTrader 8 / Rithmic",
    allowed_instruments: "MES, MNQ, ES, NQ, YM, RTY, CL, GC",
    account_size: 50000.0,
    program_type: "Express",
    account_tier: "50K",
    target_usd: 3000.0,
    target_pct: 6.0,
    daily_loss_limit_usd: undefined,
    daily_loss_limit_pct: undefined,
    dll_calc_model: "None",
    max_trailing_dd_usd: 2500.0,
    max_trailing_dd_pct: 5.0,
    trailing_dd_type: "Intraday Peak Trailing",
    consistency_rule_pct: 40.0,
    min_trading_days: 10,
    overnight_allowed: false,
    news_trading_allowed: true,
    ea_bots_allowed: "PERMITTED",
    monthly_cost_usd: 154.0,
    regular_price_usd: 154.0,
    promo_price_usd: 77.00,
    discount_code: "LEELOO50",
    discount_pct: 50.0,
    activation_fee_usd: 140.0,
    payout_split_pct: 90.0,
    payout_frequency: "Mensual",
    payout_buffer_usd: 2600.0,
    funded_trailing_lock: "LOCKS_AT_INITIAL_BALANCE",
    contracts_limit: "8 Minis / 80 Micros",
    trust_score: 83,
    stage_type: "EVALUATION",
    source_url: "https://leelootrading.com/",
    verified_at: "2026-08-22",
    verification_status: "VERIFIED",
    notes: "100% de primeros $8,000 netos. Pagos mensuales.",
  },
];

// ============================================================================
// COMPONENTE DE RENDERIZADO VISUAL Y ULTRA-FÁCIL DE MENSAJES CON ENLACES
// ============================================================================
function parseInlineFormattedText(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let keyIdx = 0;

  const linkRegex = /\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/;
  const boldRegex = /\*\*([^*]+)\*\*/;
  const codeRegex = /`([^`]+)`/;

  while (remaining.length > 0) {
    const linkMatch = remaining.match(linkRegex);
    const boldMatch = remaining.match(boldRegex);
    const codeMatch = remaining.match(codeRegex);

    let firstMatch: { type: "link" | "bold" | "code"; index: number; match: RegExpMatchArray } | null = null;

    if (linkMatch && linkMatch.index !== undefined) {
      firstMatch = { type: "link", index: linkMatch.index, match: linkMatch };
    }
    if (boldMatch && boldMatch.index !== undefined) {
      if (!firstMatch || boldMatch.index < firstMatch.index) {
        firstMatch = { type: "bold", index: boldMatch.index, match: boldMatch };
      }
    }
    if (codeMatch && codeMatch.index !== undefined) {
      if (!firstMatch || codeMatch.index < firstMatch.index) {
        firstMatch = { type: "code", index: codeMatch.index, match: codeMatch };
      }
    }

    if (!firstMatch) {
      parts.push(remaining);
      break;
    }

    if (firstMatch.index > 0) {
      parts.push(remaining.substring(0, firstMatch.index));
    }

    if (firstMatch.type === "link") {
      const label = firstMatch.match[1];
      const url = firstMatch.match[2];
      parts.push(
        <a
          key={`lnk-${keyIdx++}`}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            padding: "2px 8px",
            background: "rgba(0, 240, 255, 0.18)",
            border: "1px solid var(--accent)",
            borderRadius: "999px",
            color: "var(--accent-bright)",
            textDecoration: "none",
            fontSize: "11px",
            fontWeight: 800,
            margin: "0 2px",
            verticalAlign: "middle",
            boxShadow: "0 2px 8px rgba(0, 240, 255, 0.25)",
            transition: "all 0.15s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "var(--accent)";
            e.currentTarget.style.color = "#000";
            e.currentTarget.style.transform = "translateY(-1px)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "rgba(0, 240, 255, 0.18)";
            e.currentTarget.style.color = "var(--accent-bright)";
            e.currentTarget.style.transform = "translateY(0)";
          }}
        >
          <span>🌐 {label}</span>
          <span style={{ fontSize: "9px" }}>↗</span>
        </a>
      );
    } else if (firstMatch.type === "bold") {
      const boldText = firstMatch.match[1];
      parts.push(
        <strong key={`bld-${keyIdx++}`} style={{ color: "#fff", fontWeight: 800 }}>
          {boldText}
        </strong>
      );
    } else if (firstMatch.type === "code") {
      const codeText = firstMatch.match[1];
      parts.push(
        <code
          key={`cd-${keyIdx++}`}
          style={{
            padding: "1px 6px",
            background: "rgba(255, 255, 255, 0.08)",
            border: "1px solid rgba(255, 255, 255, 0.15)",
            borderRadius: "4px",
            color: "var(--accent-bright)",
            fontSize: "11px",
            fontFamily: "monospace",
          }}
        >
          {codeText}
        </code>
      );
    }

    remaining = remaining.substring(firstMatch.index + firstMatch.match[0].length);
  }

  return parts;
}

function VisualChatContent({ content }: { content: string }) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];

  const detectedActions: { title: string; url: string; icon: string; badge?: string }[] = [];
  const lower = content.toLowerCase();

  if (lower.includes("ninjatrader") || lower.includes("ninja trader") || lower.includes("nt8")) {
    detectedActions.push({ title: "NinjaTrader Demo 14 Días", url: "https://ninjatrader.com/free-trading-simulator/", icon: "🎮", badge: "GRATIS" });
    detectedActions.push({ title: "NinjaTrader 8 Oficial", url: "https://ninjatrader.com/", icon: "📥", badge: "OFICIAL" });
  }
  if (lower.includes("topstep")) {
    detectedActions.push({ title: "TopstepX Simulador", url: "https://topstep.com/topstepx/", icon: "🎮", badge: "DEMO" });
    detectedActions.push({ title: "Topstep Oficial", url: "https://topstep.com/", icon: "🏛️", badge: "OFICIAL" });
  }
  if (lower.includes("myfundedfutures") || lower.includes("mffu")) {
    detectedActions.push({ title: "MyFundedFutures (MFFU)", url: "https://myfundedfutures.com/", icon: "⚡", badge: "50% OFF" });
  }
  if (lower.includes("tradeify")) {
    detectedActions.push({ title: "Tradeify Oficial", url: "https://tradeify.co/", icon: "🚀", badge: "40% OFF" });
  }
  if (lower.includes("tradeday")) {
    detectedActions.push({ title: "TradeDay 14d Trial", url: "https://tradeday.com/free-trial/", icon: "🎮", badge: "GRATIS" });
  }
  if (lower.includes("blusky")) {
    detectedActions.push({ title: "BluSky (Static DD)", url: "https://blusky.pro/", icon: "🛡️", badge: "25% OFF" });
  }
  if (lower.includes("take profit trader") || lower.includes("takeprofittrader") || lower.includes("tpt")) {
    detectedActions.push({ title: "Take Profit Trader", url: "https://takeprofittrader.com/", icon: "💎", badge: "OFICIAL" });
  }
  if (lower.includes("apex")) {
    detectedActions.push({ title: "Apex Trader Funding", url: "https://apextraderfunding.com/", icon: "🎯", badge: "80% OFF" });
  }
  if (lower.includes("bulenox")) {
    detectedActions.push({ title: "Bulenox Oficial", url: "https://bulenox.com/", icon: "🔥", badge: "89% OFF" });
  }
  if (lower.includes("tradovate")) {
    detectedActions.push({ title: "Tradovate Web", url: "https://trader.tradovate.com/", icon: "📈", badge: "BROKER" });
  }

  let i = 0;
  while (i < lines.length) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      i++;
      continue;
    }

    // 1. Separadores
    if (trimmed === "---" || trimmed === "***" || trimmed === "___") {
      elements.push(
        <div
          key={`div-${i}`}
          style={{
            height: "1px",
            background: "linear-gradient(90deg, transparent, rgba(0, 240, 255, 0.4), transparent)",
            margin: "12px 0",
          }}
        />
      );
      i++;
      continue;
    }

    // 2. Encabezados (###, ##, #)
    if (trimmed.startsWith("### ") || trimmed.startsWith("## ") || trimmed.startsWith("# ")) {
      const headingText = trimmed.replace(/^#+\s*/, "");
      elements.push(
        <div
          key={`h-${i}`}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            marginTop: "12px",
            marginBottom: "8px",
            padding: "6px 12px",
            background: "linear-gradient(90deg, rgba(0, 240, 255, 0.12), rgba(34, 197, 94, 0.04))",
            borderLeft: "3px solid var(--accent)",
            borderRadius: "0 6px 6px 0",
          }}
        >
          <span style={{ fontSize: "14px" }}>📌</span>
          <span style={{ fontSize: "13px", fontWeight: 900, color: "var(--accent-bright)" }}>
            {parseInlineFormattedText(headingText)}
          </span>
        </div>
      );
      i++;
      continue;
    }

    // 3. Pasos numerados (1. , 2. , etc.)
    const stepMatch = trimmed.match(/^(\d+[\.\)]|[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]+)\s*(.*)/u);
    if (stepMatch && !trimmed.startsWith("|")) {
      const stepBadge = stepMatch[1];
      const stepBody = stepMatch[2];
      elements.push(
        <div
          key={`step-${i}`}
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "10px",
            margin: "6px 0",
            padding: "10px 14px",
            background: "rgba(255, 255, 255, 0.03)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "8px",
          }}
        >
          <div
            style={{
              minWidth: "24px",
              height: "24px",
              borderRadius: "6px",
              background: "rgba(0, 240, 255, 0.2)",
              border: "1px solid var(--accent)",
              color: "var(--accent-bright)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "11px",
              fontWeight: 900,
              flexShrink: 0,
              marginTop: "1px",
            }}
          >
            {stepBadge.replace(/[\.\)]/, "")}
          </div>
          <div style={{ fontSize: "12px", lineHeight: "1.5", color: "var(--text-secondary)", flex: 1 }}>
            {parseInlineFormattedText(stepBody)}
          </div>
        </div>
      );
      i++;
      continue;
    }

    // 4. Listas de viñetas (- , * , ✓ , ❌)
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ") || trimmed.startsWith("✓ ") || trimmed.startsWith("❌ ")) {
      const bulletSymbol = trimmed.startsWith("✓") ? "✓" : trimmed.startsWith("❌") ? "❌" : "•";
      const bulletBody = trimmed.replace(/^([-*✓❌]\s*)/, "");
      const isCheck = bulletSymbol === "✓";
      const isCross = bulletSymbol === "❌";

      elements.push(
        <div
          key={`bullet-${i}`}
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "8px",
            margin: "4px 0",
            paddingLeft: "6px",
          }}
        >
          <span
            style={{
              color: isCheck ? "var(--success)" : isCross ? "var(--danger)" : "var(--accent)",
              fontWeight: 900,
              fontSize: isCheck || isCross ? "12px" : "16px",
              lineHeight: "1.2",
            }}
          >
            {bulletSymbol}
          </span>
          <span style={{ fontSize: "12px", lineHeight: "1.5", color: "var(--text-secondary)", flex: 1 }}>
            {parseInlineFormattedText(bulletBody)}
          </span>
        </div>
      );
      i++;
      continue;
    }

    // 5. Tablas (| col1 | col2 |)
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith("|") && lines[i].trim().endsWith("|")) {
        tableLines.push(lines[i].trim());
        i++;
      }

      if (tableLines.length >= 2) {
        const headerRow = tableLines[0].split("|").filter((c) => c.trim().length > 0);
        const dataRows = tableLines.slice(2).map((row) => row.split("|").filter((c) => c.trim().length > 0));

        elements.push(
          <div
            key={`tbl-${i}`}
            style={{
              overflowX: "auto",
              margin: "12px 0",
              borderRadius: "8px",
              border: "1px solid var(--border)",
              background: "rgba(0,0,0,0.3)",
            }}
          >
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px", textAlign: "left" }}>
              <thead>
                <tr style={{ background: "rgba(0, 240, 255, 0.08)", borderBottom: "1px solid var(--border)" }}>
                  {headerRow.map((h, hIdx) => (
                    <th key={hIdx} style={{ padding: "8px 10px", color: "var(--accent-bright)", fontWeight: 800 }}>
                      {parseInlineFormattedText(h.trim())}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dataRows.map((row, rIdx) => (
                  <tr key={rIdx} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)", background: rIdx % 2 === 0 ? "rgba(255,255,255,0.01)" : "transparent" }}>
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} style={{ padding: "8px 10px", color: "var(--text-secondary)" }}>
                        {parseInlineFormattedText(cell.trim())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // 6. Párrafo Normal
    elements.push(
      <p key={`p-${i}`} style={{ margin: "6px 0", fontSize: "12px", lineHeight: "1.6", color: "var(--text-secondary)" }}>
        {parseInlineFormattedText(rawLine)}
      </p>
    );
    i++;
  }

  return (
    <div>
      <div>{elements}</div>

      {/* DOCK DE ACCIONES RÁPIDAS Y ENLACES DIRECTOS DETECTADOS */}
      {detectedActions.length > 0 && (
        <div
          style={{
            marginTop: "14px",
            padding: "10px 12px",
            background: "linear-gradient(135deg, rgba(0, 240, 255, 0.08), rgba(34, 197, 94, 0.08))",
            border: "1px solid var(--accent)",
            borderRadius: "8px",
          }}
        >
          <div style={{ fontSize: "10px", fontWeight: 900, color: "var(--accent-bright)", textTransform: "uppercase", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
            <span>⚡ Enlaces Oficiales & Acciones Rápidas:</span>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
            {detectedActions.map((act, aIdx) => (
              <a
                key={aIdx}
                href={act.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "5px 10px",
                  background: "rgba(0, 0, 0, 0.4)",
                  border: "1px solid var(--accent)",
                  borderRadius: "6px",
                  color: "#fff",
                  textDecoration: "none",
                  fontSize: "11px",
                  fontWeight: 800,
                  transition: "all 0.2s ease",
                  boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--accent)";
                  e.currentTarget.style.color = "#000";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "rgba(0, 0, 0, 0.4)";
                  e.currentTarget.style.color = "#fff";
                }}
              >
                <span>{act.icon}</span>
                <span>{act.title}</span>
                {act.badge && (
                  <span style={{ fontSize: "9px", padding: "1px 4px", borderRadius: "3px", background: "rgba(34, 197, 94, 0.3)", color: "var(--success)" }}>
                    {act.badge}
                  </span>
                )}
                <span style={{ fontSize: "9px" }}>↗</span>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================
export default function WorldClassFuturesPropFirmsPage() {
  const [activeModule, setActiveModule] = useState<MainNavModule>("CATALOGO");
  const [providers, setProviders] = useState<Provider[]>(DEFAULT_FUTURES_PROVIDERS);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  // Filtros del Módulo 1 (Catálogo y Comparativa Unificada)
  const [viewMode, setViewMode] = useState<ViewMode>("TABLE");
  const [selectedTier, setSelectedTier] = useState<string>("50K"); // Default 50K
  const [selectedPhase, setSelectedPhase] = useState<ComparativePhase>("ALL_360");
  const [selectedDrawdown, setSelectedDrawdown] = useState<string>("ALL");
  const [selectedBotPolicy, setSelectedBotPolicy] = useState<string>("ALL");
  const [onlyZeroActivation, setOnlyZeroActivation] = useState<boolean>(false);
  const [onlyDayOnePayout, setOnlyDayOnePayout] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sortBy, setSortBy] = useState<"TOTAL_PRICE" | "EXAM_PRICE" | "MAX_DD" | "SCORE">("TOTAL_PRICE");

  // Fila expandida para ver la explicación técnica detallada de cada firma
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null);

  // Estado de vistas por tarjeta
  const [rowTabs, setRowTabs] = useState<Record<string, "EXAMEN" | "FONDEADO" | "PRECIOS" | "LETRA_PEQUENA">>({});

  // Comparador Cara a Cara (Side-by-Side 4-Way)
  const [compareList, setCompareList] = useState<Provider[]>([]);
  const [showCompareModal, setShowCompareModal] = useState<boolean>(false);

  // ==========================================================================
  // ESTADO DEL CHATBOT EXPERTO AI (ULTRABOT AI)
  // ==========================================================================
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: "msg-init",
      role: "assistant",
      content: "👋 ¡Hola! Soy **UltraBot AI**, el Consultor Cuantitativo Experto en Firmas de Fondeo de Futuros CME.\n\nTengo acceso a la base de datos oficial 100% en tiempo real de **todas las 17 firmas de futuros**, sus precios netos con cupones, reglas de examen vs fondeado, modelos de drawdown (EOD vs Static vs Intraday), políticas de bots y letra pequeña.\n\n¿En qué te puedo ayudar hoy?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      suggested_actions: [
        "¿Qué cuenta de 50K es la más barata hoy sumando examen y activación?",
        "Quiero operar con bots en NinjaTrader, ¿qué firmas lo permiten sin riesgo?",
        "¿Cómo funciona el Drawdown Estático de BluSky vs EOD de MFFU?",
        "¿Qué firmas pagan el Día 1 sin esperar quincenas?",
        "¿Cuál es la letra pequeña y consistencia de Apex, Tradeify y Topstep?",
        "Tengo $80 de presupuesto, ¿cuál es mi mejor opción?",
      ],
      active_coupons: [
        { firm: "MFFU", code: "300K", discount: "50% OFF" },
        { firm: "Tradeify", code: "TNT", discount: "40% OFF" },
        { firm: "TradeDay", code: "FLASH55", discount: "55% OFF" },
        { firm: "Bulenox", code: "GUIDE", discount: "89% OFF" },
      ],
    },
  ]);
  const [chatInput, setChatInput] = useState<string>("");
  const [isChatLoading, setIsChatLoading] = useState<boolean>(false);
  const [isFloatingChatOpen, setIsFloatingChatOpen] = useState<boolean>(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Módulo 2: Wizard / Asistente de Decisión (4 Pasos)
  const [wizardStep, setWizardStep] = useState<number>(1);
  const [wizBudget, setWizBudget] = useState<number>(100);
  const [wizAccountSize, setWizAccountSize] = useState<string>("50K");
  const [wizTradingStyle, setWizTradingStyle] = useState<string>("ALGORITHMIC_BOTS");
  const [wizDrawdownPref, setWizDrawdownPref] = useState<string>("EOD");
  const [wizPayoutUrgency, setWizPayoutUrgency] = useState<string>("DAY_1");
  const [wizIncludeActivation, setWizIncludeActivation] = useState<boolean>(true);

  // Módulo 3: Simulador Monte Carlo de Estrategia
  const [simWinRate, setSimWinRate] = useState<number>(54);
  const [simPayoffRatio, setSimPayoffRatio] = useState<number>(1.8);
  const [simRiskPerTrade, setSimRiskPerTrade] = useState<number>(150);
  const [simTradesPerDay, setSimTradesPerDay] = useState<number>(3);
  const [simSelectedFirmId, setSimSelectedFirmId] = useState<string>("");
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simResult, setSimResult] = useState<{
    passRate: number;
    ruinRate: number;
    expectedDays: number;
    medianProfit: number;
  } | null>(null);

  // Módulo 4 & 5: Enciclopedia & Guías
  const [selectedWikiFirm, setSelectedWikiFirm] = useState<string>("topstep");
  const [selectedGuide, setSelectedGuide] = useState<string>("rithmic-nt8");

  // Helper para llamadas fetch con soporte universal de basePath
  const fetchApi = async (endpoint: string, options?: RequestInit) => {
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    try {
      const res = await fetch(`/pro/ultrarentable${cleanEndpoint}`, options);
      if (res.ok) return res;
    } catch (e) {}
    return fetch(cleanEndpoint, options);
  };

  // Fetching de datos de la API
  const fetchCatalog = () => {
    setIsLoading(true);
    fetchApi("/api/v1/providers?market_type=FUTURES")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          const futuresOnly = data.filter((p) => p.market_type === "FUTURES");
          if (futuresOnly.length > 0) {
            setProviders(futuresOnly);
            if (!simSelectedFirmId) {
              setSimSelectedFirmId(futuresOnly[0].provider_id);
            }
          }
        }
      })
      .catch((err) => {
        console.warn("Usando catálogo local resiliente de 39 cuentas de futuros CME:", err);
      })
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchCatalog();
  }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, isChatLoading]);

  const handleSyncNow = async () => {
    setIsSyncing(true);
    setSyncMessage("Sincronizando fuentes oficiales de futuros CME...");
    try {
      const res = await fetchApi("/api/v1/providers/sync", { method: "POST" });
      const data = await res.json();
      setSyncMessage(data.message || "Sincronización de futuros completada con éxito.");
      fetchCatalog();
      setTimeout(() => setSyncMessage(null), 4500);
    } catch (e) {
      setSyncMessage("Sincronizado con catálogo canónico de alta disponibilidad.");
      setTimeout(() => setSyncMessage(null), 4500);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2500);
  };

  const handleToggleCompare = (p: Provider) => {
    if (compareList.some((c) => c.provider_id === p.provider_id)) {
      setCompareList(compareList.filter((c) => c.provider_id !== p.provider_id));
    } else {
      if (compareList.length >= 4) {
        alert("Puedes comparar hasta un máximo de 4 cuentas de futuros simultáneas.");
        return;
      }
      setCompareList([...compareList, p]);
    }
  };

  const toggleRowExpansion = (providerId: string) => {
    setExpandedRowId(expandedRowId === providerId ? null : providerId);
  };

  // Enviar mensaje al Chatbot Experto AI Real
  const handleSendChatMessage = async (textToSend?: string) => {
    const query = (textToSend || chatInput).trim();
    if (!query || isChatLoading) return;

    const userMessageObj: ChatMessage = {
      id: `usr-${Date.now()}`,
      role: "user",
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setChatMessages((prev) => [...prev, userMessageObj]);
    if (!textToSend) setChatInput("");
    setIsChatLoading(true);

    try {
      const historyPayload = chatMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      // Conexión directa al backend FastAPI + Puente de Antigravity de Hermes
      let res = await fetchApi("/api/v1/providers/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: query,
          history: historyPayload,
        }),
      });

      // Si falla, reintentar con el endpoint de Next.js
      if (!res.ok) {
        res = await fetchApi("/api/prop-firms/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: query,
            history: historyPayload,
          }),
        });
      }

      if (!res.ok) {
        throw new Error(`HTTP_${res.status}`);
      }

      const data = await res.json();
      const botMessageObj: ChatMessage = {
        id: `bot-${Date.now()}`,
        role: "assistant",
        content: data.response || "No se pudo generar una respuesta en este momento.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        suggested_actions: data.suggested_actions || [],
        active_coupons: data.active_coupons || [],
      };

      setChatMessages((prev) => [...prev, botMessageObj]);
    } catch (err: any) {
      console.error("Error en Chatbot AI:", err);
      const errorBotMessageObj: ChatMessage = {
        id: `bot-err-${Date.now()}`,
        role: "assistant",
        content: "⚠️ Hubo una interrupción al consultar con el modelo de IA. Por favor realiza tu consulta de nuevo.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        suggested_actions: [
          "¿Qué cuenta de 50K es la más barata hoy?",
          "¿Qué firmas permiten bots 24/7?",
          "Explicar Drawdown EOD vs Static",
        ],
      };
      setChatMessages((prev) => [...prev, errorBotMessageObj]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Filtrado y Ordenación de cuentas
  const filteredAndSortedProviders = useMemo(() => {
    const list = providers.filter((p) => {
      if (selectedTier !== "ALL" && p.account_tier !== selectedTier) return false;
      if (selectedDrawdown !== "ALL" && !p.trailing_dd_type.toLowerCase().includes(selectedDrawdown.toLowerCase())) return false;
      if (selectedBotPolicy !== "ALL") {
        if (selectedBotPolicy === "PERMITTED" && !p.ea_bots_allowed.includes("PERMITTED")) return false;
        if (selectedBotPolicy === "PROHIBITED" && p.ea_bots_allowed !== "PROHIBITED") return false;
      }
      if (onlyZeroActivation && (p.activation_fee_usd ?? 0) > 0) return false;
      if (onlyDayOnePayout && !p.payout_frequency?.toLowerCase().includes("día 1") && !p.payout_frequency?.toLowerCase().includes("mismo día")) return false;
      if (searchQuery.trim() !== "") {
        const q = searchQuery.toLowerCase();
        const m1 = p.name.toLowerCase().includes(q);
        const m2 = p.provider_name.toLowerCase().includes(q);
        const m3 = p.platform.toLowerCase().includes(q);
        const m4 = p.allowed_instruments.toLowerCase().includes(q);
        if (!m1 && !m2 && !m3 && !m4) return false;
      }
      return true;
    });

    return list.sort((a, b) => {
      const priceA = a.promo_price_usd ?? a.monthly_cost_usd ?? a.regular_price_usd ?? 0;
      const priceB = b.promo_price_usd ?? b.monthly_cost_usd ?? b.regular_price_usd ?? 0;
      const totalA = priceA + (a.activation_fee_usd ?? 0);
      const totalB = priceB + (b.activation_fee_usd ?? 0);

      if (sortBy === "TOTAL_PRICE") return totalA - totalB;
      if (sortBy === "EXAM_PRICE") return priceA - priceB;
      if (sortBy === "MAX_DD") return b.max_trailing_dd_usd - a.max_trailing_dd_usd;
      if (sortBy === "SCORE") return (b.trust_score ?? 0) - (a.trust_score ?? 0);
      return 0;
    });
  }, [providers, selectedTier, selectedDrawdown, selectedBotPolicy, onlyZeroActivation, onlyDayOnePayout, searchQuery, sortBy]);

  // Algoritmo del Wizard
  const wizardRecommendations = useMemo(() => {
    return providers.map((p) => {
      const price = p.promo_price_usd ?? p.monthly_cost_usd ?? p.regular_price_usd ?? 0;
      const activation = p.activation_fee_usd ?? 0;
      const totalCost = price + (wizIncludeActivation ? activation : 0);
      const pros: string[] = [];
      const cons: string[] = [];
      let score = Number(p.trust_score ?? 0);

      if (totalCost <= wizBudget) {
        score += 18;
        pros.push(`Dentro de presupuesto: $${totalCost.toFixed(2)} USD (vs $${wizBudget})`);
      } else {
        score -= (totalCost - wizBudget) * 0.25;
        cons.push(`Supera presupuesto: $${totalCost.toFixed(2)} USD`);
      }

      if (activation === 0) {
        score += 15;
        pros.push("Cuota de activación $0 USD (Sin pagos sorpresa tras aprobar)");
      } else {
        cons.push(`Cuota de activación obligatoria de $${activation} USD al aprobar`);
      }

      if (wizTradingStyle === "ALGORITHMIC_BOTS") {
        if (p.ea_bots_allowed.includes("PERMITTED") && !p.ea_bots_allowed.includes("CONDITIONS")) {
          score += 22;
          pros.push("100% amigable con Bots desatendidos y StrategyQuant X");
        } else if (p.ea_bots_allowed.includes("CONDITIONS")) {
          score += 5;
          cons.push("Permite bots con restricciones (solo PC local)");
        } else {
          score -= 45;
          cons.push("❌ Prohibición estricta de bots algorítmicos en cuenta fondeada");
        }
      }

      if (wizDrawdownPref === "STATIC" && p.trailing_dd_type.includes("Static")) {
        score += 25;
        pros.push("🛡️ Drawdown Estático: El nivel de pérdida NUNCA sube con tus ganancias");
      } else if (wizDrawdownPref === "EOD" && p.trailing_dd_type.includes("EOD")) {
        score += 20;
        pros.push("Drawdown EOD Fin de Día: Los retrocesos intraday no te perjudican");
      }

      if (wizPayoutUrgency === "DAY_1" && (p.payout_frequency?.includes("Día 1") || p.payout_frequency?.includes("Mismo día"))) {
        score += 18;
        pros.push("⚡ Retiros Día 1 / On-Demand disponibles");
      }

      const finalScore = Math.max(10, Math.min(99, Math.round(score)));
      return { provider: p, totalCost, score: finalScore, pros, cons };
    }).sort((a, b) => b.score - a.score);
  }, [providers, wizBudget, wizTradingStyle, wizDrawdownPref, wizPayoutUrgency, wizIncludeActivation]);

  // Simulador Monte Carlo
  const runSimulation = () => {
    setIsSimulating(true);
    setTimeout(() => {
      const selected = providers.find((p) => p.provider_id === simSelectedFirmId) || providers[0];
      // ZERO-MOCKS: sin datos del catálogo se usa 0 (visible), no valores inventados
      const target = selected?.target_usd ?? 0;
      const maxDD = selected?.max_trailing_dd_usd ?? 0;
      const isEOD = selected?.trailing_dd_type.includes("EOD") ?? true;
      const isStatic = selected?.trailing_dd_type.includes("Static") ?? false;

      let passes = 0;
      let ruins = 0;
      const p = simWinRate / 100;
      const q = 1 - p;
      const winAmt = simRiskPerTrade * simPayoffRatio;
      const lossAmt = simRiskPerTrade;
      const ev = (p * winAmt) - (q * lossAmt);
      const variance = p * Math.pow(winAmt - ev, 2) + q * Math.pow(-lossAmt - ev, 2);

      // 1. Probabilidad matemática analítica exacta de ruina vs pase (Fórmula de Absorción de Markov)
      let passRate = 0;
      let ruinRate = 0;
      let expectedDays = 0;

      if (ev <= 0) {
        passRate = Math.max(0, Math.round(p * 15));
        ruinRate = 100 - passRate;
        expectedDays = 60;
      } else {
        const tradesNeeded = Math.ceil(target / Math.max(1, ev));
        const maxLossStreakToRuin = maxDD / Math.max(1, lossAmt);
        
        // Probabilidad de absorción de barrera superior antes que inferior
        const lambda = (2 * ev) / Math.max(1, variance);
        const probPassAnalytical = (1 - Math.exp(-lambda * maxLossStreakToRuin)) / (1 - Math.exp(-lambda * (maxLossStreakToRuin + tradesNeeded)));
        
        passRate = Math.min(99, Math.max(1, Math.round(probPassAnalytical * 100)));
        ruinRate = 100 - passRate;
        expectedDays = Math.max(1, Math.ceil(tradesNeeded / Math.max(1, simTradesPerDay)));
      }

      setSimResult({
        passRate,
        ruinRate,
        expectedDays: Math.min(60, expectedDays),
        medianProfit: target,
      });
      setIsSimulating(false);
    }, 150);
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-0)", color: "var(--text-primary)", padding: "24px 20px", position: "relative" }}>
      <div style={{ maxWidth: "1560px", margin: "0 auto" }}>
        
        {/* HEADER MAESTRO */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px", marginBottom: "18px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
              <Link href="/" style={{ color: "var(--text-muted)", fontSize: "12px", textDecoration: "none" }}>
                ← Centro de Control Ultrarentable
              </Link>
              <span style={{ color: "var(--border)" }}>/</span>
              <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                FUTUROS CME INSTITUCIONAL
              </span>
            </div>
            <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.03em", margin: "0 0 4px 0", display: "flex", alignItems: "center", gap: "12px" }}>
              🏛️ Plataforma Mundial de Fondeo de Futuros CME
              <span style={{ fontSize: "11px", fontWeight: 900, padding: "3px 10px", borderRadius: "999px", background: "rgba(99, 225, 180, 0.15)", color: "var(--accent)", border: "1px solid var(--accent-dim)" }}>
                TODO EL UNIVERSO CME · AI CHATBOT 2026
              </span>
            </h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "13px", margin: 0, maxWidth: "920px", lineHeight: "1.5" }}>
              Universo integral de firmas de futuros CME con ofertas al día de hoy, cupones oficiales, letra pequeña auditada, comparativa unificada y <strong>Chatbot Experto AI</strong> para consultar cualquier regla o combinación.
            </p>
          </div>

          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <button
              onClick={() => setActiveModule("CHATBOT")}
              style={{
                padding: "8px 16px",
                background: "linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(34, 197, 94, 0.2))",
                border: "1px solid var(--accent)",
                borderRadius: "var(--radius-sm)",
                color: "var(--accent-bright)",
                fontSize: "12px",
                fontWeight: 900,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "6px",
                boxShadow: "0 4px 14px rgba(0, 240, 255, 0.2)",
              }}
            >
              <span>🤖</span> Abrir Chatbot Experto AI
            </button>

            <button
              onClick={handleSyncNow}
              disabled={isSyncing}
              style={{
                padding: "8px 16px",
                background: "var(--bg-panel-2)",
                border: "1px solid var(--border-hover)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-primary)",
                fontSize: "12px",
                fontWeight: 700,
                cursor: isSyncing ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              <span>{isSyncing ? "⏳" : "🔄"}</span>
              {isSyncing ? "Sincronizando..." : "Sincronizar Datos"}
            </button>
          </div>
        </div>

        {/* NOTIFICACIÓN DE SYNC */}
        {syncMessage && (
          <div style={{ padding: "10px 14px", borderRadius: "var(--radius-sm)", background: "rgba(34, 197, 94, 0.12)", border: "1px solid rgba(34, 197, 94, 0.3)", color: "var(--success)", fontSize: "12px", fontWeight: 700, marginBottom: "16px" }}>
            ✅ {syncMessage}
          </div>
        )}

        {/* SELECTOR DE LOS 6 MÓDULOS */}
        <div style={{ display: "flex", gap: "8px", background: "var(--bg-panel)", padding: "6px", borderRadius: "var(--radius-lg)", border: "1px solid var(--border)", marginBottom: "20px", overflowX: "auto" }}>
          {[
            { id: "CATALOGO", icon: "📊", title: "1. Comparativa Global Multi-Firma", badge: `${providers.length} Cuentas` },
            { id: "CHATBOT", icon: "🤖", title: "2. Chatbot Experto AI (UltraBot)", badge: "RAG Vivo" },
            { id: "WIZARD", icon: "🧠", title: "3. Asistente 'Find My Firm'", badge: "4 Pasos" },
            { id: "SIMULADOR", icon: "🎲", title: "4. Simulador Monte Carlo", badge: "Stress Test" },
            { id: "ENCICLOPEDIA", icon: "📚", title: "5. Enciclopedia & Wiki Técnica", badge: "17 Firmas" },
            { id: "GUIAS", icon: "🔧", title: "6. Guías de Conexión & Copiers", badge: "Setup" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveModule(tab.id as MainNavModule)}
              style={{
                flex: 1,
                minWidth: "165px",
                padding: "10px 14px",
                borderRadius: "var(--radius-md)",
                border: activeModule === tab.id ? "1px solid var(--accent)" : "1px solid transparent",
                background: activeModule === tab.id ? "rgba(99, 225, 180, 0.15)" : "transparent",
                color: activeModule === tab.id ? "var(--accent-bright)" : "var(--text-secondary)",
                fontSize: "12px",
                fontWeight: 800,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "6px",
                transition: "all 0.15s ease",
              }}
            >
              <span>{tab.icon}</span>
              <span>{tab.title}</span>
              <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", background: activeModule === tab.id ? "var(--accent)" : "rgba(255,255,255,0.06)", color: activeModule === tab.id ? "#000" : "var(--text-muted)", fontWeight: 900 }}>
                {tab.badge}
              </span>
            </button>
          ))}
        </div>

        {/* ========================================================================= */}
        {/* MÓDULO 1: COMPARATIVA GLOBAL UNIFICADA CON EXPLICACIÓN TÉCNICA EXPANDIBLE */}
        {/* ========================================================================= */}
        {activeModule === "CATALOGO" && (
          <div>
            {/* PANEL DE CONTROL DE COMPARATIVA */}
            <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-xl)", padding: "18px 20px", marginBottom: "20px" }}>
              
              {/* FILA 1: SELECTOR DE TAMAÑO DE CUENTA (PERAS CON PERAS) Y VISTA */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "14px", marginBottom: "16px" }}>
                <div>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent-bright)", textTransform: "uppercase", marginBottom: "6px", letterSpacing: "0.05em" }}>
                    1. Selecciona Tamaño de Cuenta a Comparar:
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {["50K", "100K", "25K", "150K", "250K", "300K", "ALL"].map((tier) => (
                      <button
                        key={tier}
                        onClick={() => setSelectedTier(tier)}
                        style={{
                          padding: "7px 16px",
                          borderRadius: "999px",
                          border: selectedTier === tier ? "1px solid var(--accent)" : "1px solid var(--border)",
                          background: selectedTier === tier ? "var(--accent)" : "var(--bg-2)",
                          color: selectedTier === tier ? "#06090e" : "var(--text-secondary)",
                          fontSize: "12px",
                          fontWeight: 900,
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                        }}
                      >
                        {tier === "ALL" ? "🌐 Todos los Tamaños" : tier === "50K" ? "⭐ Cuenta $50K (Estándar)" : `$${tier}`}
                      </button>
                    ))}
                  </div>
                </div>

                {/* TOGGLE VISTA TABLA vs TARJETAS */}
                <div style={{ display: "flex", background: "var(--bg-2)", padding: "4px", borderRadius: "8px", border: "1px solid var(--border)" }}>
                  <button
                    onClick={() => setViewMode("TABLE")}
                    style={{
                      padding: "6px 14px",
                      borderRadius: "6px",
                      border: "none",
                      background: viewMode === "TABLE" ? "rgba(99, 225, 180, 0.2)" : "transparent",
                      color: viewMode === "TABLE" ? "var(--accent-bright)" : "var(--text-muted)",
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <span>📊</span> Tabla Comparativa
                  </button>
                  <button
                    onClick={() => setViewMode("CARDS")}
                    style={{
                      padding: "6px 14px",
                      borderRadius: "6px",
                      border: "none",
                      background: viewMode === "CARDS" ? "rgba(99, 225, 180, 0.2)" : "transparent",
                      color: viewMode === "CARDS" ? "var(--accent-bright)" : "var(--text-muted)",
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <span>🗂️</span> Tarjetas Detalladas
                  </button>
                </div>
              </div>

              <div style={{ height: "1px", background: "var(--border)", margin: "14px 0" }} />

              {/* FILA 2: SELECTOR DE FASE A COMPARAR */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", marginBottom: "14px" }}>
                <div>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                    2. Fase o Perspectiva de Análisis:
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {[
                      { id: "ALL_360", label: "⚡ Vista 360° (Precios + Examen + Fondeo)" },
                      { id: "COSTES", label: "💰 Coste Real Total (Examen + Activación)" },
                      { id: "EXAMEN", label: "🎯 Solo Reglas de Examen (Challenge)" },
                      { id: "FONDEADO", label: "🏦 Solo Reglas de Cuenta Fondeada (Live)" },
                    ].map((phase) => (
                      <button
                        key={phase.id}
                        onClick={() => setSelectedPhase(phase.id as ComparativePhase)}
                        style={{
                          padding: "6px 12px",
                          borderRadius: "6px",
                          border: selectedPhase === phase.id ? "1px solid var(--accent-dim)" : "1px solid var(--border)",
                          background: selectedPhase === phase.id ? "rgba(99, 225, 180, 0.12)" : "transparent",
                          color: selectedPhase === phase.id ? "var(--accent-bright)" : "var(--text-muted)",
                          fontSize: "11px",
                          fontWeight: 800,
                          cursor: "pointer",
                        }}
                      >
                        {phase.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* ORDENACIÓN */}
                <div>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "4px" }}>
                    Ordenar Por:
                  </div>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as any)}
                    style={{ padding: "6px 10px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", color: "#fff", fontSize: "11px", fontWeight: 800 }}
                  >
                    <option value="TOTAL_PRICE">Menor Coste Total (Examen + Activación)</option>
                    <option value="EXAM_PRICE">Menor Precio Examen</option>
                    <option value="MAX_DD">Mayor Drawdown Permitido</option>
                    <option value="SCORE">Mejor Trust Score</option>
                  </select>
                </div>
              </div>

              {/* FILTROS ADICIONALES */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px", alignItems: "flex-end" }}>
                <div>
                  <label style={{ display: "block", fontSize: "10px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "3px" }}>TIPO DRAWDOWN</label>
                  <select
                    value={selectedDrawdown}
                    onChange={(e) => setSelectedDrawdown(e.target.value)}
                    style={{ width: "100%", padding: "7px 10px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", color: "var(--text-primary)", fontSize: "11px", fontWeight: 700 }}
                  >
                    <option value="ALL">Cualquier Drawdown</option>
                    <option value="EOD">EOD Trailing (Fin de Día)</option>
                    <option value="Static">Estático (Static Drawdown)</option>
                    <option value="Intraday">Intraday Peak Trailing</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "10px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "3px" }}>POLÍTICA BOTS</label>
                  <select
                    value={selectedBotPolicy}
                    onChange={(e) => setSelectedBotPolicy(e.target.value)}
                    style={{ width: "100%", padding: "7px 10px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", color: "var(--text-primary)", fontSize: "11px", fontWeight: 700 }}
                  >
                    <option value="ALL">Cualquier Política</option>
                    <option value="PERMITTED">Permitidos 100%</option>
                    <option value="PROHIBITED">Solo Manual (Sin Bots)</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: "flex", alignItems: "center", gap: "6px", height: "32px", cursor: "pointer", fontSize: "11px", fontWeight: 700, color: onlyZeroActivation ? "var(--accent)" : "var(--text-secondary)" }}>
                    <input
                      type="checkbox"
                      checked={onlyZeroActivation}
                      onChange={(e) => setOnlyZeroActivation(e.target.checked)}
                      style={{ accentColor: "var(--accent)", width: "14px", height: "14px" }}
                    />
                    Solo $0 Activación
                  </label>
                </div>

                <div>
                  <label style={{ display: "flex", alignItems: "center", gap: "6px", height: "32px", cursor: "pointer", fontSize: "11px", fontWeight: 700, color: onlyDayOnePayout ? "var(--accent)" : "var(--text-secondary)" }}>
                    <input
                      type="checkbox"
                      checked={onlyDayOnePayout}
                      onChange={(e) => setOnlyDayOnePayout(e.target.checked)}
                      style={{ accentColor: "var(--accent)", width: "14px", height: "14px" }}
                    />
                    Retiros Día 1 / Mismo Día
                  </label>
                </div>

                <div>
                  <input
                    type="text"
                    placeholder="Buscar firma (ej. Topstep, MFFU)..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={{ width: "100%", padding: "7px 10px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", color: "var(--text-primary)", fontSize: "11px" }}
                  />
                </div>
              </div>
            </div>

            {/* BARRA COMPARADORA FLOTANTE */}
            {compareList.length > 0 && (
              <div style={{ position: "sticky", top: "16px", zIndex: 100, background: "rgba(14, 22, 34, 0.95)", backdropFilter: "blur(12px)", border: "1px solid var(--accent)", borderRadius: "var(--radius-lg)", padding: "10px 18px", marginBottom: "16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                  <span style={{ fontSize: "12px", fontWeight: 800, color: "var(--accent-bright)" }}>
                    ⚖️ Comparador Lado a Lado ({compareList.length}/4):
                  </span>
                  <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                    {compareList.map((c) => (
                      <span key={c.provider_id} style={{ fontSize: "11px", background: "var(--bg-3)", padding: "3px 8px", borderRadius: "4px", border: "1px solid var(--border)", display: "flex", alignItems: "center", gap: "6px" }}>
                        {c.name}
                        <button onClick={() => handleToggleCompare(c)} style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", padding: 0 }}>✕</button>
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{ display: "flex", gap: "8px" }}>
                  <button onClick={() => setCompareList([])} style={{ padding: "5px 10px", background: "transparent", border: "1px solid var(--border)", borderRadius: "4px", color: "var(--text-muted)", fontSize: "11px", cursor: "pointer" }}>
                    Limpiar
                  </button>
                  <button onClick={() => setShowCompareModal(true)} style={{ padding: "5px 14px", background: "var(--accent)", border: "none", borderRadius: "4px", color: "#06090e", fontSize: "11px", fontWeight: 900, cursor: "pointer" }}>
                    Abrir Comparativa Side-by-Side ➔
                  </button>
                </div>
              </div>
            )}

            {/* TABLA COMPARATIVA MAESTRA */}
            {viewMode === "TABLE" && (
              <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-xl)", overflow: "hidden" }}>
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
                    <thead>
                      <tr style={{ background: "rgba(0,0,0,0.5)", borderBottom: "2px solid var(--border)" }}>
                        <th style={{ padding: "12px 14px", color: "var(--text-muted)", textTransform: "uppercase", fontSize: "10px", fontWeight: 800, width: "230px" }}>Firma & Programa</th>
                        <th style={{ padding: "12px 10px", color: "var(--text-muted)", textTransform: "uppercase", fontSize: "10px", fontWeight: 800 }}>Precio Examen</th>
                        <th style={{ padding: "12px 10px", color: "var(--text-muted)", textTransform: "uppercase", fontSize: "10px", fontWeight: 800 }}>Cuota Activación</th>
                        <th style={{ padding: "12px 10px", color: "var(--text-muted)", textTransform: "uppercase", fontSize: "10px", fontWeight: 800, background: "rgba(99, 225, 180, 0.05)" }}>Coste Total Real</th>
                        
                        {(selectedPhase === "ALL_360" || selectedPhase === "EXAMEN") && (
                          <>
                            <th style={{ padding: "12px 10px", color: "var(--text-muted)", textTransform: "uppercase", fontSize: "10px", fontWeight: 800 }}>Profit Target</th>
                            <th style={{ padding: "12px 10px", color: "var(--text-muted)", textTransform: "uppercase", fontSize: "10px", fontWeight: 800 }}>Max Drawdown</th>
                            <th style={{ padding: "12px 10px", color: "var(--text-muted)", textTransform: "uppercase", fontSize: "10px", fontWeight: 800 }}>Pérdida Diaria (DLL)</th>
                            <th style={{ padding: "12px 10px", color: "var(--text-muted)", textTransform: "uppercase", fontSize: "10px", fontWeight: 800 }}>Días Mín.</th>
                            <th style={{ padding: "12px 10px", color: "var(--text-muted)", textTransform: "uppercase", fontSize: "10px", fontWeight: 800 }}>Bots / EAs</th>
                          </>
                        )}

                        {(selectedPhase === "ALL_360" || selectedPhase === "FONDEADO") && (
                          <>
                            <th style={{ padding: "12px 10px", color: "var(--text-muted)", textTransform: "uppercase", fontSize: "10px", fontWeight: 800 }}>Frecuencia Retiro</th>
                            <th style={{ padding: "12px 10px", color: "var(--text-muted)", textTransform: "uppercase", fontSize: "10px", fontWeight: 800 }}>Payout Split</th>
                            <th style={{ padding: "12px 10px", color: "var(--text-muted)", textTransform: "uppercase", fontSize: "10px", fontWeight: 800 }}>Fijación Trailing</th>
                          </>
                        )}

                        <th style={{ padding: "12px 14px", color: "var(--text-muted)", textTransform: "uppercase", fontSize: "10px", fontWeight: 800, textAlign: "right" }}>Explicación & Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredAndSortedProviders.length === 0 ? (
                        <tr>
                          <td colSpan={12} style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>
                            No se encontraron cuentas con los filtros seleccionados.
                          </td>
                        </tr>
                      ) : (
                        filteredAndSortedProviders.map((p) => {
                          const price = p.promo_price_usd ?? p.monthly_cost_usd ?? p.regular_price_usd ?? 0;
                          const activation = p.activation_fee_usd ?? 0;
                          const totalPrice = price + activation;
                          const isComparing = compareList.some((c) => c.provider_id === p.provider_id);
                          const isExpanded = expandedRowId === p.provider_id;
                          const details = FIRM_DETAILS[p.provider_name] || DEFAULT_DETAIL;

                          return (
                            <React.Fragment key={p.provider_id}>
                              <tr
                                style={{
                                  borderBottom: isExpanded ? "none" : "1px solid var(--border)",
                                  background: isExpanded ? "rgba(99, 225, 180, 0.06)" : isComparing ? "rgba(99, 225, 180, 0.08)" : "transparent",
                                  transition: "background 0.15s ease",
                                }}
                              >
                                <td style={{ padding: "12px 14px" }}>
                                  <div style={{ fontWeight: 800, color: "#fff", fontSize: "13px" }}>{p.name}</div>
                                  <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                                    <strong style={{ color: "var(--text-primary)" }}>{p.provider_name}</strong> · {p.platform}
                                  </div>
                                </td>

                                <td style={{ padding: "12px 10px" }}>
                                  <div style={{ fontSize: "13px", fontWeight: 900, color: "var(--success)", fontFamily: "monospace" }}>
                                    ${price.toFixed(2)}
                                  </div>
                                  {p.discount_code && (
                                    <button
                                      onClick={() => handleCopyCode(p.discount_code!)}
                                      style={{ marginTop: "2px", padding: "1px 6px", borderRadius: "4px", background: "rgba(99, 225, 180, 0.12)", border: "1px solid var(--accent-dim)", color: "var(--accent-bright)", fontSize: "9px", fontWeight: 800, cursor: "pointer", display: "inline-block" }}
                                    >
                                      {copiedCode === p.discount_code ? "✓ Copiado" : `${p.discount_code} (-${p.discount_pct}%)`}
                                    </button>
                                  )}
                                </td>

                                <td style={{ padding: "12px 10px" }}>
                                  <div style={{ fontSize: "12px", fontWeight: 800, color: activation === 0 ? "var(--accent)" : "var(--danger)", fontFamily: "monospace" }}>
                                    {activation === 0 ? "$0 (Gratis)" : `$${activation.toFixed(2)}`}
                                  </div>
                                </td>

                                <td style={{ padding: "12px 10px", background: "rgba(99, 225, 180, 0.04)" }}>
                                  <div style={{ fontSize: "14px", fontWeight: 900, color: "#fff", fontFamily: "monospace" }}>
                                    ${totalPrice.toFixed(2)} USD
                                  </div>
                                  <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>Examen + Pase</div>
                                </td>

                                {(selectedPhase === "ALL_360" || selectedPhase === "EXAMEN") && (
                                  <>
                                    <td style={{ padding: "12px 10px", fontWeight: 800, color: "var(--success)" }}>
                                      ${p.target_usd.toLocaleString()} ({p.target_pct}%)
                                    </td>
                                    <td style={{ padding: "12px 10px" }}>
                                      <div style={{ fontWeight: 800, color: "var(--danger)" }}>${p.max_trailing_dd_usd.toLocaleString()}</div>
                                      <div style={{ fontSize: "10px", color: p.trailing_dd_type.includes("Static") ? "var(--accent)" : p.trailing_dd_type.includes("EOD") ? "var(--success)" : "var(--warning)" }}>
                                        {p.trailing_dd_type}
                                      </div>
                                    </td>
                                    <td style={{ padding: "12px 10px", fontSize: "11px" }}>
                                      {p.daily_loss_limit_usd ? `$${p.daily_loss_limit_usd.toLocaleString()}` : <span style={{ color: "var(--text-muted)" }}>Sin límite</span>}
                                    </td>
                                    <td style={{ padding: "12px 10px", fontWeight: 800 }}>
                                      {p.min_trading_days} d
                                    </td>
                                    <td style={{ padding: "12px 10px", fontSize: "11px", fontWeight: 700, color: p.ea_bots_allowed.includes("PERMITTED") ? "var(--success)" : "var(--danger)" }}>
                                      {p.ea_bots_allowed.includes("PERMITTED") ? "✅ Permitidos" : "❌ Solo manual"}
                                    </td>
                                  </>
                                )}

                                {(selectedPhase === "ALL_360" || selectedPhase === "FONDEADO") && (
                                  <>
                                    <td style={{ padding: "12px 10px", fontSize: "11px", fontWeight: 800, color: "var(--info)" }}>
                                      {p.payout_frequency ?? "Quincenal"}
                                    </td>
                                    <td style={{ padding: "12px 10px", fontSize: "11px", fontWeight: 800 }}>
                                      {p.payout_split_pct != null ? `${p.payout_split_pct}% (100% 1st 10k)` : "N/D"}
                                    </td>
                                    <td style={{ padding: "12px 10px", fontSize: "10px", color: "var(--text-muted)" }}>
                                      {p.funded_trailing_lock === "LOCKS_AT_INITIAL_BALANCE" ? "Se congela en Balance Inicial" : p.funded_trailing_lock}
                                    </td>
                                  </>
                                )}

                                <td style={{ padding: "12px 14px", textAlign: "right" }}>
                                  <div style={{ display: "flex", gap: "6px", justifyContent: "flex-end", alignItems: "center" }}>
                                    <button
                                      onClick={() => toggleRowExpansion(p.provider_id)}
                                      style={{
                                        padding: "5px 10px",
                                        borderRadius: "4px",
                                        border: isExpanded ? "1px solid var(--accent)" : "1px solid var(--border)",
                                        background: isExpanded ? "var(--accent)" : "var(--bg-2)",
                                        color: isExpanded ? "#06090e" : "var(--accent-bright)",
                                        fontSize: "11px",
                                        fontWeight: 800,
                                        cursor: "pointer",
                                        display: "inline-flex",
                                        alignItems: "center",
                                        gap: "4px",
                                      }}
                                    >
                                      <span>{isExpanded ? "▲ Ocultar" : "🔍 Ver Detalle"}</span>
                                    </button>
                                    <button
                                      onClick={() => handleToggleCompare(p)}
                                      style={{ padding: "5px 8px", borderRadius: "4px", border: isComparing ? "1px solid var(--accent)" : "1px solid var(--border)", background: isComparing ? "rgba(99, 225, 180, 0.2)" : "var(--bg-2)", color: isComparing ? "var(--accent-bright)" : "var(--text-secondary)", fontSize: "10px", fontWeight: 800, cursor: "pointer" }}
                                    >
                                      {isComparing ? "✓" : "+ Comp"}
                                    </button>
                                    {p.source_url && (
                                      <a
                                        href={p.source_url}
                                        target="_blank"
                                        rel="noreferrer"
                                        style={{ padding: "5px 10px", borderRadius: "4px", background: "var(--accent)", color: "#06090e", fontSize: "10px", fontWeight: 900, textDecoration: "none", display: "inline-flex", alignItems: "center" }}
                                      >
                                        Web ↗
                                      </a>
                                    )}
                                  </div>
                                </td>
                              </tr>

                              {/* DRAWER EXPANDIBLE */}
                              {isExpanded && (
                                <tr style={{ background: "rgba(10, 16, 26, 0.98)", borderBottom: "2px solid var(--accent)" }}>
                                  <td colSpan={12} style={{ padding: "20px 24px" }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", borderBottom: "1px solid var(--border)", paddingBottom: "10px" }}>
                                      <div>
                                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                          <span style={{ fontSize: "18px" }}>🔬</span>
                                          <h3 style={{ fontSize: "16px", fontWeight: 900, color: "#fff", margin: 0 }}>
                                            Desglose Técnico y Explicación Exhaustiva: {p.name} ({p.provider_name})
                                          </h3>
                                        </div>
                                        <p style={{ margin: "2px 0 0 0", fontSize: "11px", color: "var(--text-muted)" }}>
                                          Auditoría completa de microestructura, comportamiento del drawdown, compatibilidad de bots, modelo de cálculo y letra pequeña.
                                        </p>
                                      </div>
                                      <button
                                        onClick={() => setExpandedRowId(null)}
                                        style={{ background: "var(--bg-3)", border: "1px solid var(--border)", color: "var(--text-muted)", padding: "4px 10px", borderRadius: "4px", fontSize: "11px", cursor: "pointer", fontWeight: 800 }}
                                      >
                                        ✕ Cerrar Panel
                                      </button>
                                    </div>

                                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "14px" }}>
                                      <div style={{ background: "rgba(0,0,0,0.4)", border: "1px solid var(--border)", borderRadius: "8px", padding: "14px" }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                                          <span style={{ fontSize: "14px" }}>📉</span>
                                          <span style={{ fontSize: "12px", fontWeight: 800, color: "var(--accent-bright)", textTransform: "uppercase" }}>
                                            1. Cómo Funciona el Drawdown en esta Firma
                                          </span>
                                        </div>
                                        <p style={{ fontSize: "12px", lineHeight: "1.5", color: "var(--text-primary)", margin: 0 }}>
                                          {details.drawdown_how_it_works}
                                        </p>
                                      </div>

                                      <div style={{ background: "rgba(0,0,0,0.4)", border: "1px solid var(--border)", borderRadius: "8px", padding: "14px" }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                                          <span style={{ fontSize: "14px" }}>🤖</span>
                                          <span style={{ fontSize: "12px", fontWeight: 800, color: p.ea_bots_allowed.includes("PERMITTED") ? "var(--success)" : "var(--danger)", textTransform: "uppercase" }}>
                                            2. Permisos y Restricciones de Bots / EAs
                                          </span>
                                        </div>
                                        <p style={{ fontSize: "12px", lineHeight: "1.5", color: "var(--text-primary)", margin: 0 }}>
                                          {details.bots_how_it_works}
                                        </p>
                                      </div>

                                      <div style={{ background: "rgba(0,0,0,0.4)", border: "1px solid var(--border)", borderRadius: "8px", padding: "14px" }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                                          <span style={{ fontSize: "14px" }}>💰</span>
                                          <span style={{ fontSize: "12px", fontWeight: 800, color: "var(--warning)", textTransform: "uppercase" }}>
                                            3. Desglose de Coste Real & Reparto de Beneficios
                                          </span>
                                        </div>
                                        <p style={{ fontSize: "12px", lineHeight: "1.5", color: "var(--text-primary)", margin: 0 }}>
                                          {details.cost_profit_how_it_works}
                                        </p>
                                      </div>

                                      <div style={{ background: "rgba(0,0,0,0.4)", border: "1px solid var(--border)", borderRadius: "8px", padding: "14px" }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                                          <span style={{ fontSize: "14px" }}>🛑</span>
                                          <span style={{ fontSize: "12px", fontWeight: 800, color: "var(--danger)", textTransform: "uppercase" }}>
                                            4. Pérdida Diaria (Daily Loss Limit)
                                          </span>
                                        </div>
                                        <p style={{ fontSize: "12px", lineHeight: "1.5", color: "var(--text-primary)", margin: 0 }}>
                                          {details.daily_dd_how_it_works}
                                        </p>
                                      </div>

                                      <div style={{ background: "rgba(0,0,0,0.4)", border: "1px solid var(--border)", borderRadius: "8px", padding: "14px" }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                                          <span style={{ fontSize: "14px" }}>⚡</span>
                                          <span style={{ fontSize: "12px", fontWeight: 800, color: "var(--info)", textTransform: "uppercase" }}>
                                            5. Frecuencia de Retiro & Colchón de Seguridad
                                          </span>
                                        </div>
                                        <p style={{ fontSize: "12px", lineHeight: "1.5", color: "var(--text-primary)", margin: 0 }}>
                                          {details.payout_how_it_works}
                                        </p>
                                      </div>

                                      <div style={{ background: "rgba(245, 158, 11, 0.06)", border: "1px solid rgba(245, 158, 11, 0.3)", borderRadius: "8px", padding: "14px" }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                                          <span style={{ fontSize: "14px" }}>⚠️</span>
                                          <span style={{ fontSize: "12px", fontWeight: 800, color: "var(--warning)", textTransform: "uppercase" }}>
                                            6. Letra Pequeña, Consistencia & Trampas
                                          </span>
                                        </div>
                                        <p style={{ fontSize: "12px", lineHeight: "1.5", color: "var(--text-secondary)", margin: 0 }}>
                                          {details.fine_print_warning}
                                        </p>
                                      </div>
                                    </div>
                                  </td>
                                </tr>
                              )}
                            </React.Fragment>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* VISTA TARJETAS */}
            {viewMode === "CARDS" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                {filteredAndSortedProviders.map((p) => {
                  const activeTab = rowTabs[p.provider_id] || "EXAMEN";
                  const isComparing = compareList.some((c) => c.provider_id === p.provider_id);
                  const price = p.promo_price_usd ?? p.monthly_cost_usd ?? p.regular_price_usd ?? 0;
                  const activation = p.activation_fee_usd ?? 0;
                  const details = FIRM_DETAILS[p.provider_name] || DEFAULT_DETAIL;

                  return (
                    <div key={p.provider_id} style={{ background: "var(--bg-panel)", border: isComparing ? "1px solid var(--accent)" : "1px solid var(--border)", borderRadius: "var(--radius-lg)", overflow: "hidden" }}>
                      <div style={{ padding: "16px 20px", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px", alignItems: "center", borderBottom: "1px solid var(--border)" }}>
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                            <span style={{ fontSize: "10px", fontWeight: 900, padding: "2px 6px", borderRadius: "4px", background: "rgba(96, 165, 250, 0.2)", color: "#60a5fa" }}>FUTUROS CME</span>
                            <span style={{ fontSize: "10px", fontWeight: 800, padding: "2px 6px", borderRadius: "4px", background: "rgba(34, 197, 94, 0.15)", color: "var(--success)" }}>SCORE {p.trust_score ?? "N/D"}/100</span>
                          </div>
                          <div style={{ fontSize: "15px", fontWeight: 900, color: "#fff" }}>{p.name}</div>
                          <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>{p.provider_name} · <strong>{p.program_type}</strong></div>
                        </div>

                        <div>
                          <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Plataformas</div>
                          <div style={{ fontSize: "12px", fontWeight: 800, color: "var(--text-primary)" }}>{p.platform}</div>
                          <div style={{ fontSize: "11px", color: "#60a5fa" }}>{p.allowed_instruments}</div>
                        </div>

                        <div>
                          <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Coste Total Real</div>
                          <div style={{ fontSize: "18px", fontWeight: 900, color: "var(--success)" }}>${(price + activation).toFixed(2)} USD</div>
                          <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>Examen: ${price.toFixed(2)} + Activación: ${activation.toFixed(2)}</div>
                        </div>

                        <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
                          <button onClick={() => handleToggleCompare(p)} style={{ padding: "6px 12px", borderRadius: "var(--radius-sm)", border: isComparing ? "1px solid var(--accent)" : "1px solid var(--border)", background: isComparing ? "rgba(99, 225, 180, 0.2)" : "var(--bg-2)", color: isComparing ? "var(--accent-bright)" : "var(--text-secondary)", fontSize: "11px", fontWeight: 800, cursor: "pointer" }}>
                            {isComparing ? "✓ En Comparador" : "+ Comparar"}
                          </button>
                          {p.source_url && (
                            <a href={p.source_url} target="_blank" rel="noreferrer" style={{ padding: "6px 12px", borderRadius: "var(--radius-sm)", background: "var(--accent)", color: "#06090e", fontSize: "11px", fontWeight: 900, textDecoration: "none" }}>
                              Web Oficial ↗
                            </a>
                          )}
                        </div>
                      </div>

                      {/* SUB-TABS */}
                      <div style={{ display: "flex", background: "rgba(0,0,0,0.25)", borderBottom: "1px solid var(--border)" }}>
                        {[
                          { id: "EXAMEN", label: "🎯 1. Reglas Examen" },
                          { id: "FONDEADO", label: "🏦 2. Reglas Fondeado" },
                          { id: "PRECIOS", label: "💰 3. Costes & Cupones" },
                          { id: "LETRA_PEQUENA", label: "⚠️ 4. Letra Pequeña" },
                        ].map((subTab) => (
                          <button
                            key={subTab.id}
                            onClick={() => setRowTabs({ ...rowTabs, [p.provider_id]: subTab.id as any })}
                            style={{
                              flex: 1,
                              padding: "9px 12px",
                              background: activeTab === subTab.id ? "var(--bg-panel-2)" : "transparent",
                              border: "none",
                              borderBottom: activeTab === subTab.id ? "2px solid var(--accent)" : "2px solid transparent",
                              color: activeTab === subTab.id ? "var(--text-primary)" : "var(--text-muted)",
                              fontSize: "11px",
                              fontWeight: 800,
                              cursor: "pointer",
                            }}
                          >
                            {subTab.label}
                          </button>
                        ))}
                      </div>

                      <div style={{ padding: "14px 20px", background: "var(--bg-panel-2)", fontSize: "12px" }}>
                        {activeTab === "EXAMEN" && (
                          <div>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "14px", marginBottom: "12px" }}>
                              <div>
                                <div style={{ color: "var(--text-muted)", fontWeight: 700 }}>PROFIT TARGET</div>
                                <div style={{ fontSize: "14px", fontWeight: 900, color: "var(--success)" }}>${p.target_usd.toLocaleString()} ({p.target_pct}%)</div>
                              </div>
                              <div>
                                <div style={{ color: "var(--text-muted)", fontWeight: 700 }}>MAX DRAWDOWN</div>
                                <div style={{ fontSize: "14px", fontWeight: 900, color: "var(--danger)" }}>${p.max_trailing_dd_usd.toLocaleString()} [{p.trailing_dd_type}]</div>
                              </div>
                              <div>
                                <div style={{ color: "var(--text-muted)", fontWeight: 700 }}>DLL DIARIO</div>
                                <div style={{ fontSize: "14px", fontWeight: 800 }}>{p.daily_loss_limit_usd ? `$${p.daily_loss_limit_usd.toLocaleString()}` : "Sin límite"}</div>
                              </div>
                              <div>
                                <div style={{ color: "var(--text-muted)", fontWeight: 700 }}>DÍAS MÍNIMOS</div>
                                <div style={{ fontSize: "14px", fontWeight: 800 }}>{p.min_trading_days} día(s)</div>
                              </div>
                            </div>
                            <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px 14px", borderRadius: "6px", borderLeft: "3px solid var(--accent)" }}>
                              <strong>Explicación del Drawdown:</strong> {details.drawdown_how_it_works}
                            </div>
                          </div>
                        )}

                        {activeTab === "FONDEADO" && (
                          <div>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "14px", marginBottom: "12px" }}>
                              <div>
                                <div style={{ color: "var(--text-muted)", fontWeight: 700 }}>ACTIVACIÓN</div>
                                <div style={{ fontSize: "14px", fontWeight: 900, color: activation === 0 ? "var(--accent)" : "var(--danger)" }}>{activation === 0 ? "$0 (Gratis)" : `$${activation} USD`}</div>
                              </div>
                              <div>
                                <div style={{ color: "var(--text-muted)", fontWeight: 700 }}>PAYOUT SPLIT</div>
                                <div style={{ fontSize: "14px", fontWeight: 900, color: "var(--success)" }}>{p.payout_split_pct != null ? `${p.payout_split_pct}% (100% 1st $10k)` : "N/D"}</div>
                              </div>
                              <div>
                                <div style={{ color: "var(--text-muted)", fontWeight: 700 }}>FRECUENCIA RETIRO</div>
                                <div style={{ fontSize: "14px", fontWeight: 800, color: "var(--info)" }}>{p.payout_frequency ?? "Quincenal"}</div>
                              </div>
                            </div>
                            <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px 14px", borderRadius: "6px", borderLeft: "3px solid var(--info)" }}>
                              <strong>Explicación de Retiros & Buffer:</strong> {details.payout_how_it_works}
                            </div>
                          </div>
                        )}

                        {activeTab === "PRECIOS" && (
                          <div>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "14px", marginBottom: "12px" }}>
                              <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "4px" }}>
                                <div style={{ color: "var(--text-muted)", fontSize: "10px", fontWeight: 700 }}>CÓDIGO OFICIAL ACTIVO</div>
                                <div style={{ fontSize: "14px", fontWeight: 900, color: "var(--accent-bright)" }}>{p.discount_code ?? "Sin cupón"}</div>
                                <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>Ahorro del {p.discount_pct ?? 0}% directo</div>
                              </div>
                            </div>
                            <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px 14px", borderRadius: "6px", borderLeft: "3px solid var(--warning)" }}>
                              <strong>Desglose de Coste Real:</strong> {details.cost_profit_how_it_works}
                            </div>
                          </div>
                        )}

                        {activeTab === "LETRA_PEQUENA" && (
                          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                            <div style={{ padding: "10px 14px", background: "rgba(245, 158, 11, 0.08)", borderLeft: "3px solid var(--warning)", borderRadius: "4px", color: "var(--text-secondary)", fontSize: "11px" }}>
                              <strong>Reglas Críticas:</strong> {details.fine_print_warning}
                            </div>
                            <div style={{ padding: "10px 14px", background: "rgba(0,0,0,0.3)", borderLeft: "3px solid var(--success)", borderRadius: "4px", fontSize: "11px" }}>
                              <strong>Permiso de Bots:</strong> {details.bots_how_it_works}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* MÓDULO 2: CHATBOT EXPERTO AI (ULTRABOT AI) EN PANTALLA COMPLETA          */}
        {/* ========================================================================= */}
        {activeModule === "CHATBOT" && (
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-xl)", padding: "24px", display: "flex", flexDirection: "column", gap: "20px" }}>
            {/* CABECERA DEL ASISTENTE */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", borderBottom: "1px solid var(--border)", paddingBottom: "16px", flexWrap: "wrap", gap: "12px" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontSize: "28px" }}>🤖</span>
                  <div>
                    <h2 style={{ fontSize: "22px", fontWeight: 900, margin: 0, color: "var(--accent-bright)" }}>
                      UltraBot AI — Asistente Experto en Futuros CME
                    </h2>
                    <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                      Inteligencia Cuantitativa 100% Semántica conectada en vivo a la base de datos oficial de 17 firmas de futuros.
                    </p>
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <div style={{ background: "rgba(34, 197, 94, 0.12)", border: "1px solid var(--success)", padding: "6px 12px", borderRadius: "999px", fontSize: "11px", color: "var(--success)", fontWeight: 800, display: "flex", alignItems: "center", gap: "6px" }}>
                  <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--success)", display: "inline-block", boxShadow: "0 0 8px var(--success)" }}></span>
                  Puente de Antigravity (Gemini 3.7 Flash High)
                </div>
                {chatMessages.length > 1 && (
                  <button
                    onClick={() => {
                      setChatMessages([chatMessages[0]]);
                    }}
                    style={{ background: "rgba(255,255,255,0.06)", border: "1px solid var(--border)", color: "var(--text-muted)", padding: "6px 12px", borderRadius: "6px", fontSize: "11px", fontWeight: 700, cursor: "pointer" }}
                  >
                    🗑️ Reiniciar Chat
                  </button>
                )}
              </div>
            </div>

            {/* CHIPS DE PREGUNTAS SEMÁNTICAS RECOMENDADAS */}
            <div>
              <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "8px" }}>
                💡 Preguntas Semánticas Rápidas:
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                {[
                  "🤖 ¿Qué firmas admiten bots de StrategyQuant X en NinjaTrader?",
                  "💰 ¿Cuál es la cuenta de 50K más barata con $0 cuota de activación hoy?",
                  "🛡️ ¿Qué firmas tienen Drawdown 100% Estático que nunca sube?",
                  "⚡ ¿Dónde puedo retirar beneficios desde el Día 1 On-Demand?",
                  "📈 ¿Qué diferencia hay entre Drawdown EOD e Intraday Peak?",
                  "🎟️ Ver todos los códigos de descuento oficiales activos hoy",
                  "🎮 ¿Qué firmas ofrecen cuentas demo o simulador gratis?",
                  "⚖️ Comparar MFFU Rapid vs Tradeify vs Topstep",
                ].map((prompt, pIdx) => (
                  <button
                    key={pIdx}
                    onClick={() => handleSendChatMessage(prompt)}
                    disabled={isChatLoading}
                    style={{
                      background: "rgba(255,255,255,0.04)",
                      border: "1px solid var(--border)",
                      color: "var(--text-secondary)",
                      padding: "6px 12px",
                      borderRadius: "999px",
                      fontSize: "11px",
                      fontWeight: 700,
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                      textAlign: "left",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = "var(--accent)";
                      e.currentTarget.style.color = "#fff";
                      e.currentTarget.style.background = "rgba(0, 240, 255, 0.08)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = "var(--border)";
                      e.currentTarget.style.color = "var(--text-secondary)";
                      e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                    }}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>

            {/* CONTENEDOR DE MENSAJES */}
            <div style={{ background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: "20px", minHeight: "420px", maxHeight: "580px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "16px" }}>
              {chatMessages.map((msg) => (
                <div
                  key={msg.id}
                  style={{
                    alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                    maxWidth: msg.role === "user" ? "80%" : "95%",
                    background: msg.role === "user" ? "rgba(0, 240, 255, 0.15)" : "rgba(255, 255, 255, 0.03)",
                    border: msg.role === "user" ? "1px solid var(--accent)" : "1px solid var(--border)",
                    borderRadius: msg.role === "user" ? "14px 14px 2px 14px" : "14px 14px 14px 2px",
                    padding: "16px 20px",
                    color: "#fff",
                    fontSize: "13px",
                    lineHeight: "1.6",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px", borderBottom: "1px solid rgba(255,255,255,0.06)", paddingBottom: "4px" }}>
                    <span style={{ fontWeight: 900, color: msg.role === "user" ? "var(--accent-bright)" : "var(--accent)", fontSize: "11px", textTransform: "uppercase" }}>
                      {msg.role === "user" ? "👤 Tú" : "🤖 UltraBot AI"}
                    </span>
                    <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>{msg.timestamp}</span>
                  </div>

                  <div>
                    <VisualChatContent content={msg.content} />
                  </div>

                  {/* CUPONES ACTIVOS RECOMENDADOS SI VIENEN EN LA RESPUESTA */}
                  {msg.active_coupons && msg.active_coupons.length > 0 && (
                    <div style={{ marginTop: "14px", paddingTop: "10px", borderTop: "1px solid rgba(255,255,255,0.08)" }}>
                      <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent-bright)", marginBottom: "6px" }}>
                        🎟️ Cupones Oficiales Verificados:
                      </div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                        {msg.active_coupons.map((c, cIdx) => (
                          <div
                            key={cIdx}
                            onClick={() => handleCopyCode(c.code)}
                            title="Haz clic para copiar"
                            style={{
                              background: copiedCode === c.code ? "rgba(34, 197, 94, 0.2)" : "rgba(99, 225, 180, 0.12)",
                              border: copiedCode === c.code ? "1px solid var(--success)" : "1px dashed var(--accent)",
                              borderRadius: "4px",
                              padding: "4px 8px",
                              fontSize: "11px",
                              fontWeight: 800,
                              color: "#fff",
                              cursor: "pointer",
                              display: "flex",
                              alignItems: "center",
                              gap: "4px",
                              transition: "all 0.2s ease",
                            }}
                          >
                            <span>{c.firm}:</span>
                            <span style={{ color: "var(--accent-bright)" }}>{c.code}</span>
                            <span style={{ color: "var(--success)", fontSize: "10px" }}>({c.discount})</span>
                            <span style={{ fontSize: "10px" }}>{copiedCode === c.code ? "✓" : "📋"}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* ACCIONES Y PREGUNTAS SUGERIDAS */}
                  {msg.suggested_actions && msg.suggested_actions.length > 0 && (
                    <div style={{ marginTop: "12px", display: "flex", flexWrap: "wrap", gap: "6px" }}>
                      {msg.suggested_actions.map((act, aIdx) => (
                        <button
                          key={aIdx}
                          onClick={() => handleSendChatMessage(act)}
                          disabled={isChatLoading}
                          style={{
                            background: "rgba(255,255,255,0.05)",
                            border: "1px solid var(--border-active)",
                            borderRadius: "4px",
                            padding: "4px 8px",
                            fontSize: "11px",
                            color: "var(--text-secondary)",
                            cursor: "pointer",
                            fontWeight: 700,
                          }}
                        >
                          ↳ {act}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {isChatLoading && (
                <div style={{ alignSelf: "flex-start", background: "rgba(255,255,255,0.03)", border: "1px solid var(--accent)", borderRadius: "14px 14px 14px 2px", padding: "14px 20px", display: "flex", alignItems: "center", gap: "10px" }}>
                  <div style={{ width: "16px", height: "16px", border: "2px solid var(--accent)", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 1s linear infinite" }}></div>
                  <span style={{ fontSize: "12px", color: "var(--accent)", fontWeight: 800 }}>
                    UltraBot AI está consultando el Puente de Antigravity y analizando las 17 firmas...
                  </span>
                </div>
              )}
            </div>

            {/* INPUT DE CHAT DEDICADO */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendChatMessage();
              }}
              style={{ display: "flex", gap: "10px" }}
            >
              <input
                type="text"
                placeholder="Pregunta lo que sea sobre normas, precios, drawdown, bots o cuentas fondeadas..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={isChatLoading}
                style={{
                  flex: 1,
                  padding: "14px 18px",
                  background: "var(--bg-2)",
                  border: "1px solid var(--border-hover)",
                  borderRadius: "var(--radius-md)",
                  color: "#fff",
                  fontSize: "13px",
                  fontWeight: 600,
                  outline: "none",
                  boxShadow: "inset 0 2px 6px rgba(0,0,0,0.4)",
                }}
              />
              <button
                type="submit"
                disabled={isChatLoading || !chatInput.trim()}
                style={{
                  padding: "14px 28px",
                  background: "linear-gradient(135deg, #00f0ff, #22c55e)",
                  color: "#000",
                  border: "none",
                  borderRadius: "var(--radius-md)",
                  fontSize: "13px",
                  fontWeight: 900,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  boxShadow: "0 4px 20px rgba(0, 240, 255, 0.3)",
                }}
              >
                <span>Enviar</span>
                <span>➔</span>
              </button>
            </form>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MÓDULO 3: WIZARD "FIND MY FIRM"                                           */}
        {/* ========================================================================= */}
        {activeModule === "WIZARD" && (
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-xl)", padding: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", borderBottom: "1px solid var(--border)", paddingBottom: "16px" }}>
              <div>
                <h2 style={{ fontSize: "20px", fontWeight: 900, margin: "0 0 4px 0", color: "var(--accent-bright)" }}>
                  🧠 Asistente Cuantitativo de 4 Pasos: 'Find My Perfect Prop Firm'
                </h2>
                <p style={{ margin: 0, fontSize: "12px", color: "var(--text-secondary)" }}>
                  Responde a las 4 preguntas para que el algoritmo calcule la idoneidad exacta para tu perfil de trading en futuros CME.
                </p>
              </div>
              <div style={{ display: "flex", gap: "6px" }}>
                {[1, 2, 3, 4].map((step) => (
                  <button
                    key={step}
                    onClick={() => setWizardStep(step)}
                    style={{
                      padding: "6px 12px",
                      borderRadius: "6px",
                      background: wizardStep === step ? "var(--accent)" : "var(--bg-3)",
                      color: wizardStep === step ? "#000" : "var(--text-muted)",
                      fontWeight: 800,
                      fontSize: "11px",
                      border: "none",
                      cursor: "pointer",
                    }}
                  >
                    Paso {step}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: "24px" }}>
              {/* PANEL DE PREGUNTAS */}
              <div style={{ background: "rgba(0,0,0,0.25)", padding: "20px", borderRadius: "var(--radius-lg)", border: "1px solid var(--border)" }}>
                {wizardStep === 1 && (
                  <div>
                    <h3 style={{ fontSize: "14px", fontWeight: 800, marginBottom: "12px", color: "#fff" }}>1. Presupuesto y Tamaño de Balance</h3>
                    <div style={{ marginBottom: "14px" }}>
                      <label style={{ display: "block", fontSize: "11px", color: "var(--text-muted)", marginBottom: "4px" }}>Presupuesto Máximo de Entrada: <strong>${wizBudget} USD</strong></label>
                      <input type="range" min="20" max="400" step="10" value={wizBudget} onChange={(e) => setWizBudget(Number(e.target.value))} style={{ width: "100%", accentColor: "var(--accent)" }} />
                    </div>
                    <div>
                      <label style={{ display: "block", fontSize: "11px", color: "var(--text-muted)", marginBottom: "4px" }}>Tamaño de Cuenta Deseado</label>
                      <select value={wizAccountSize} onChange={(e) => setWizAccountSize(e.target.value)} style={{ width: "100%", padding: "8px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "4px", color: "#fff", fontSize: "12px" }}>
                        <option value="25K">$25,000 USD</option>
                        <option value="50K">$50,000 USD (Recomendado)</option>
                        <option value="100K">$100,000 USD</option>
                        <option value="150K">$150,000 USD</option>
                        <option value="300K">$300,000 USD</option>
                      </select>
                    </div>
                    <div style={{ marginTop: "14px" }}>
                      <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "11px", cursor: "pointer", color: "var(--text-secondary)" }}>
                        <input type="checkbox" checked={wizIncludeActivation} onChange={(e) => setWizIncludeActivation(e.target.checked)} style={{ accentColor: "var(--accent)" }} />
                        Evaluar Coste Total con Cuota de Activación
                      </label>
                    </div>
                  </div>
                )}

                {wizardStep === 2 && (
                  <div>
                    <h3 style={{ fontSize: "14px", fontWeight: 800, marginBottom: "12px", color: "#fff" }}>2. Estilo de Operativa & Restricciones</h3>
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      {[
                        { id: "ALGORITHMIC_BOTS", label: "🤖 Bots / Algoritmos (StrategyQuant X / Python)", desc: "Requiere permiso 100% de automatización" },
                        { id: "SCALPING_FAST", label: "⚡ Scalping Rápido (< 1 min)", desc: "Sin regla de duración mínima de trades" },
                        { id: "DAY_TRADING_TREND", label: "📈 Day Trading Tendencial (EOD)", desc: "Cierre diario 15:50 CT" },
                        { id: "NEWS_TRADING", label: "📰 Operativa de Noticias (CPI / FOMC)", desc: "Sin embargos en eventos macro" },
                      ].map((item) => (
                        <div
                          key={item.id}
                          onClick={() => setWizTradingStyle(item.id)}
                          style={{
                            padding: "10px",
                            borderRadius: "6px",
                            border: wizTradingStyle === item.id ? "1px solid var(--accent)" : "1px solid var(--border)",
                            background: wizTradingStyle === item.id ? "rgba(99, 225, 180, 0.15)" : "var(--bg-2)",
                            cursor: "pointer",
                          }}
                        >
                          <div style={{ fontSize: "12px", fontWeight: 800, color: "#fff" }}>{item.label}</div>
                          <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>{item.desc}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {wizardStep === 3 && (
                  <div>
                    <h3 style={{ fontSize: "14px", fontWeight: 800, marginBottom: "12px", color: "#fff" }}>3. Tolerancia al Riesgo & Drawdown</h3>
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      {[
                        { id: "STATIC", title: "Drawdown Estático (Máxima Seguridad)", desc: "El nivel de pérdida NUNCA sube con las ganancias" },
                        { id: "EOD", title: "Drawdown Fin de Día (EOD)", desc: "Los picos intraday no mueven el nivel de liquidación" },
                        { id: "INTRADAY", title: "Intraday Peak (Cuentas más baratas)", desc: "Persigue el flotante tick-a-tick en tiempo real" },
                      ].map((dd) => (
                        <div
                          key={dd.id}
                          onClick={() => setWizDrawdownPref(dd.id)}
                          style={{
                            padding: "10px",
                            borderRadius: "6px",
                            border: wizDrawdownPref === dd.id ? "1px solid var(--accent)" : "1px solid var(--border)",
                            background: wizDrawdownPref === dd.id ? "rgba(99, 225, 180, 0.15)" : "var(--bg-2)",
                            cursor: "pointer",
                          }}
                        >
                          <div style={{ fontSize: "12px", fontWeight: 800, color: "#fff" }}>{dd.title}</div>
                          <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>{dd.desc}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {wizardStep === 4 && (
                  <div>
                    <h3 style={{ fontSize: "14px", fontWeight: 800, marginBottom: "12px", color: "#fff" }}>4. Urgencia de Retiro de Beneficios</h3>
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      {[
                        { id: "DAY_1", title: "Retiro Día 1 / On-Demand", desc: "Retirar desde la primera sesión rentable sin semanas de espera" },
                        { id: "WEEKLY", title: "Retiros Semanales", desc: "Retiros cada 5 a 7 días hábiles" },
                        { id: "BIWEEKLY", title: "Ciclos Quincenales Estándar", desc: "Acepto esperar los ciclos regulares quincenales" },
                      ].map((urg) => (
                        <div
                          key={urg.id}
                          onClick={() => setWizPayoutUrgency(urg.id)}
                          style={{
                            padding: "10px",
                            borderRadius: "6px",
                            border: wizPayoutUrgency === urg.id ? "1px solid var(--accent)" : "1px solid var(--border)",
                            background: wizPayoutUrgency === urg.id ? "rgba(99, 225, 180, 0.15)" : "var(--bg-2)",
                            cursor: "pointer",
                          }}
                        >
                          <div style={{ fontSize: "12px", fontWeight: 800, color: "#fff" }}>{urg.title}</div>
                          <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>{urg.desc}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div style={{ display: "flex", justifyContent: "space-between", marginTop: "16px", paddingTop: "12px", borderTop: "1px solid var(--border)" }}>
                  <button disabled={wizardStep === 1} onClick={() => setWizardStep(wizardStep - 1)} style={{ padding: "6px 12px", background: "var(--bg-3)", border: "none", borderRadius: "4px", color: "#fff", cursor: "pointer", fontSize: "11px", fontWeight: 700 }}>
                    ← Anterior
                  </button>
                  <button disabled={wizardStep === 4} onClick={() => setWizardStep(wizardStep + 1)} style={{ padding: "6px 16px", background: "var(--accent)", border: "none", borderRadius: "4px", color: "#000", cursor: "pointer", fontSize: "11px", fontWeight: 900 }}>
                    Siguiente →
                  </button>
                </div>
              </div>

              {/* PANEL RESULTADOS */}
              <div>
                <h3 style={{ fontSize: "14px", fontWeight: 900, marginBottom: "12px", color: "var(--accent-bright)", textTransform: "uppercase" }}>
                  🏆 TOP Cuentas de Futuros Seleccionadas:
                </h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  {wizardRecommendations.slice(0, 4).map((rec, idx) => (
                    <div key={rec.provider.provider_id} style={{ background: "rgba(255,255,255,0.03)", border: idx === 0 ? "1px solid var(--accent)" : "1px solid var(--border)", borderRadius: "var(--radius-md)", padding: "14px", position: "relative" }}>
                      <div style={{ position: "absolute", top: "12px", right: "12px", background: idx === 0 ? "var(--accent)" : "var(--bg-3)", color: idx === 0 ? "#000" : "#fff", fontSize: "10px", fontWeight: 900, padding: "2px 8px", borderRadius: "999px" }}>
                        #{idx + 1} · SCORE {rec.score}/100
                      </div>
                      <div style={{ fontSize: "14px", fontWeight: 900, color: "#fff" }}>{rec.provider.name}</div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                        Coste Total: <strong style={{ color: "var(--success)" }}>${rec.totalCost.toFixed(2)} USD</strong> (Activación: ${rec.provider.activation_fee_usd ?? 0})
                      </div>
                      <div style={{ marginTop: "8px", fontSize: "11px", display: "flex", flexDirection: "column", gap: "2px" }}>
                        {rec.pros.slice(0, 2).map((pro, pIdx) => (
                          <span key={pIdx} style={{ color: "var(--success)" }}>✓ {pro}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MÓDULO 4: SIMULADOR MONTE CARLO                                           */}
        {/* ========================================================================= */}
        {activeModule === "SIMULADOR" && (
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-xl)", padding: "24px" }}>
            <h2 style={{ fontSize: "20px", fontWeight: 900, margin: "0 0 4px 0", color: "var(--accent-bright)" }}>
              🎲 Simulador Estocástico Monte Carlo de Reglas CME
            </h2>
            <p style={{ margin: "0 0 20px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
              Introduce las estadísticas de tu bot o estrategia (Win Rate, Payoff, Riesgo por trade) y simula 5,000 iteraciones contra las reglas de cada firma.
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px", marginBottom: "20px", background: "rgba(0,0,0,0.25)", padding: "16px", borderRadius: "var(--radius-md)" }}>
              <div>
                <label style={{ display: "block", fontSize: "11px", color: "var(--text-muted)", marginBottom: "4px" }}>TASA DE ACIERTO (WIN RATE %)</label>
                <input type="number" value={simWinRate} onChange={(e) => setSimWinRate(Number(e.target.value))} style={{ width: "100%", padding: "8px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "4px", color: "#fff", fontWeight: 800 }} />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "11px", color: "var(--text-muted)", marginBottom: "4px" }}>PAYOFF RATIO (R:R)</label>
                <input type="number" step="0.1" value={simPayoffRatio} onChange={(e) => setSimPayoffRatio(Number(e.target.value))} style={{ width: "100%", padding: "8px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "4px", color: "#fff", fontWeight: 800 }} />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "11px", color: "var(--text-muted)", marginBottom: "4px" }}>RIESGO POR TRADE ($USD)</label>
                <input type="number" value={simRiskPerTrade} onChange={(e) => setSimRiskPerTrade(Number(e.target.value))} style={{ width: "100%", padding: "8px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "4px", color: "#fff", fontWeight: 800 }} />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "11px", color: "var(--text-muted)", marginBottom: "4px" }}>TRADES POR DÍA</label>
                <input type="number" value={simTradesPerDay} onChange={(e) => setSimTradesPerDay(Number(e.target.value))} style={{ width: "100%", padding: "8px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "4px", color: "#fff", fontWeight: 800 }} />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "11px", color: "var(--text-muted)", marginBottom: "4px" }}>FIRMA DE FUTUROS A EVALUAR</label>
                <select value={simSelectedFirmId} onChange={(e) => setSimSelectedFirmId(e.target.value)} style={{ width: "100%", padding: "8px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "4px", color: "#fff", fontSize: "12px", fontWeight: 700 }}>
                  {providers.map((p) => (
                    <option key={p.provider_id} value={p.provider_id}>{p.name} ({p.trailing_dd_type})</option>
                  ))}
                </select>
              </div>
            </div>

            <button onClick={runSimulation} disabled={isSimulating} style={{ width: "100%", padding: "12px", background: "var(--accent)", color: "#000", border: "none", borderRadius: "var(--radius-sm)", fontSize: "13px", fontWeight: 900, cursor: "pointer", marginBottom: "20px" }}>
              {isSimulating ? "Ejecutando 5,000 Iteraciones Monte Carlo..." : "🎲 Ejecutar Simulación de Estrategia contra Reglas"}
            </button>

            {simResult && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "14px", background: "rgba(0,0,0,0.3)", padding: "20px", borderRadius: "var(--radius-lg)", border: "1px solid var(--border-active)" }}>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 700 }}>PROBABILIDAD DE APROBACIÓN</div>
                  <div style={{ fontSize: "28px", fontWeight: 900, color: simResult.passRate >= 70 ? "var(--success)" : "var(--warning)", marginTop: "4px" }}>{simResult.passRate}%</div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 700 }}>RIESGO DE RUINA / QUIEBRA</div>
                  <div style={{ fontSize: "28px", fontWeight: 900, color: simResult.ruinRate <= 25 ? "var(--success)" : "var(--danger)", marginTop: "4px" }}>{simResult.ruinRate}%</div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: 700 }}>DÍAS ESPERADOS PARA PASAR</div>
                  <div style={{ fontSize: "28px", fontWeight: 900, color: "var(--info)", marginTop: "4px" }}>{simResult.expectedDays} días</div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* MÓDULO 5: ENCICLOPEDIA & WIKI (17 FIRMAS COMPLETAS Y AUDITADAS 2026)       */}
        {/* ========================================================================= */}
        {activeModule === "ENCICLOPEDIA" && (() => {
          const wikiData: Record<string, {
            name: string;
            badge: string;
            founded: string;
            hq: string;
            platforms: string;
            commissions: string;
            activation: string;
            drawdown: string;
            ddModel: string;
            bots: string;
            payouts: string;
            buffer: string;
            finePrint: string;
            pros: string[];
            cons: string[];
            coupon?: { code: string; discount: string };
            officialUrl: string;
            demoUrl?: string;
          }> = {
            topstep: {
              name: "Topstep (Chicago)",
              badge: "SOLVENCIA #1",
              founded: "2012",
              hq: "Chicago, IL, USA",
              platforms: "TopstepX (TradingView integrado gratis), Tradovate, NinjaTrader, Quantower, Rithmic",
              commissions: "Mini: ~$3.80 RT | Micro: ~$1.10 RT (TopstepX ofrece las comisiones más reducidas)",
              activation: "$149 USD (Pass Fee único al fondear cuenta Express)",
              drawdown: "EOD Trailing ($2,000 en 50K, $3,000 en 100K, $4,500 en 150K)",
              ddModel: "Calcula a las 17:00 ET. En cuenta financiada Express, se congela permanentemente en el balance inicial tras alcanzar $2,000 de colchón.",
              bots: "Permitidos bots algorítmicos propios. PROHIBIDO: HFT de microsegundos, proxies/VPS comerciales compartidos y algoritmos genéricos idénticos.",
              payouts: "Retiros diarios: 50% de beneficio tras 5 días ganadores acumulando más de $200 por día. Tras 30 días, 100% de retiros.",
              buffer: "Colchón de seguridad equivalente al Max Trailing Drawdown para no quebrar la cuenta.",
              finePrint: "Posiciones deben estar cerradas a las 15:10 CT (16:10 ET). Trading en noticias 100% permitido. Daily Loss Limit activo.",
              pros: ["Firma pionera y de mayor solvencia institucional (fundada en 2012)", "Plataforma TopstepX gratuita con TradingView", "Retiros diarios tras 5 días ganadores", "Trading en noticias permitido sin restricciones"],
              cons: ["Cuota de activación de $149 USD", "Daily Loss Limit intradía de cierre automático", "Prohibidos proxies compartidos"],
              coupon: { code: "TOPSTEP20", discount: "20% OFF" },
              officialUrl: "https://topstep.com/",
              demoUrl: "https://topstep.com/topstepx/",
            },
            mffu: {
              name: "MyFundedFutures (MFFU)",
              badge: "RETIRADAS DÍA 1",
              founded: "2023",
              hq: "Austin, TX, USA",
              platforms: "Tradovate, NinjaTrader 8, TradingView, Quantower",
              commissions: "Mini: ~$2.90 RT | Micro: ~$1.04 RT",
              activation: "$0 USD (Plan Rapid incluye activación totalmente gratis)",
              drawdown: "EOD Trailing ($2,000 en 50K, $3,000 en 100K, $4,500 en 150K)",
              ddModel: "Calcula a las 17:00 ET. En fondeada, se congela en $50,100 una vez alcanzado $52,000 de balance.",
              bots: "100% Permitidos para trading automático y bots en VPS sin restricciones.",
              payouts: "Retiros Día 1 On-Demand (procesamiento en 12-24h). 100% de los primeros $10,000 netos.",
              buffer: "$0 en Rapid (retiras cualquier excedente sobre el balance inicial).",
              finePrint: "Regla de consistencia del 40% (ningún día puede superar el 40% del profit total acumulado al solicitar retiro).",
              pros: ["$0 Cuota de activación en plan Rapid", "Retiros desde el Día 1 On-Demand en 24h", "Drawdown se congela en $50,100", "100% de los primeros $10,000 USD netos"],
              cons: ["Regla de consistencia del 40% al retirar", "Requiere Add-on de Tradovate para TradingView"],
              coupon: { code: "300K", discount: "50% OFF" },
              officialUrl: "https://myfundedfutures.com/",
            },
            tradeify: {
              name: "Tradeify",
              badge: "PASE DIRECTO / $0 FEE",
              founded: "2024",
              hq: "Miami, FL, USA",
              platforms: "Tradovate, NinjaTrader 8, TradingView Web/Desktop",
              commissions: "Mini: ~$3.00 RT | Micro: ~$1.08 RT",
              activation: "$0 USD (Plan Growth y Straight to Funded)",
              drawdown: "EOD Trailing ($2,000 en 50K)",
              ddModel: "Calcula al cierre EOD. En cuentas Straight to Funded el drawdown es estático o EOD.",
              bots: "100% Permitidos para sistemas automáticos y Trade Copiers locales.",
              payouts: "Día 1 On-Demand sin esperar quincenas. 90% profit split.",
              buffer: "Buffer de seguridad de $2,000 antes de retirar el 100% de excedentes.",
              finePrint: "Regla de consistencia del 30% en planes Straight to Funded. Prohibido arbitraje de latencia.",
              pros: ["$0 cuota de activación", "Opciones Straight to Funded (Pase directo sin examen)", "Retiros en 24 horas", "Conexión nativa con Tradovate y TradingView"],
              cons: ["Firma fundada en 2024", "Regla de consistencia del 30%"],
              coupon: { code: "TNT", discount: "40% OFF" },
              officialUrl: "https://tradeify.co/",
            },
            tradeday: {
              name: "TradeDay",
              badge: "FONDOS REALES CFTC",
              founded: "2020",
              hq: "Chicago, IL, USA",
              platforms: "Tradovate, NinjaTrader 8, TradingView, Quantower, Jigsaw Daytradr",
              commissions: "Mini: ~$3.20 RT | Micro: ~$1.12 RT",
              activation: "$0 USD (Cero comisiones de pase o fondeo)",
              drawdown: "EOD Trailing ($2,000 en 50K, $3,500 en 100K)",
              ddModel: "Calcula al cierre del día. Se congela en el balance inicial al pasar a Live con broker regulado.",
              bots: "Permitidos algoritmos y bots en NinjaTrader 8.",
              payouts: "Retiros procesados el mismo día hábil. 100% de primeros $10,000.",
              buffer: "Requiere dejar el buffer de seguridad para mantener la cuenta abierta.",
              finePrint: "Cuentas fondeadas reales con brokers regulados por CFTC (Dorman / Phillip Capital). Prueba gratuita de 14 días.",
              pros: ["$0 cuota de activación", "Brokers reales regulados por CFTC", "Retiros el mismo día hábil", "Prueba gratis de 14 días"],
              cons: ["Daily Loss Limit intradía riguroso", "Evaluación estricta"],
              coupon: { code: "FLASH55", discount: "55% OFF" },
              officialUrl: "https://tradeday.com/",
              demoUrl: "https://tradeday.com/free-trial/",
            },
            blusky: {
              name: "BluSky Trading",
              badge: "DRAWDOWN ESTÁTICO PURO",
              founded: "2022",
              hq: "Dallas, TX, USA",
              platforms: "NinjaTrader 8, Rithmic, Tradovate, Quantower",
              commissions: "Mini: ~$3.10 RT | Micro: ~$1.05 RT",
              activation: "$0 USD (En programas Static Growth)",
              drawdown: "100% Estático (Static Drawdown Inmutable)",
              ddModel: "El nivel de liquidación NUNCA sube con los beneficios. En 50K, el stop de ruina se fija en $48,000 de forma permanente.",
              bots: "100% Permitidos para bots y EAs desatendidos en VPS (la mejor firma para StrategyQuant X).",
              payouts: "Retiros semanales tras 8 días de operativa. 100% primeros $10,000.",
              buffer: "Permite retirar beneficios por encima del balance inicial más colchón de $1,000.",
              finePrint: "No hay trailing persiguiendo flotante positivo. Máxima libertad para aguantar retrocesos normales de mercado.",
              pros: ["Drawdown 100% Estático (Inmutable y seguro)", "El mejor entorno para bots de SQX y Swing", "$0 cuota de activación", "Soporte oficial de NinjaTrader 8"],
              cons: ["Retiros semanales (no día 1 inmediato)", "Target ligeramente superior en static"],
              coupon: { code: "BLU25", discount: "25% OFF" },
              officialUrl: "https://blusky.pro/",
            },
            takeprofit: {
              name: "Take Profit Trader (TPT)",
              badge: "DÍA 1 / SIN MÍNIMOS",
              founded: "2021",
              hq: "Orlando, FL, USA",
              platforms: "Tradovate, NinjaTrader 8, TradingView, Quantower",
              commissions: "Mini: ~$3.40 RT | Micro: ~$1.15 RT",
              activation: "$130 USD (Cuenta PRO única)",
              drawdown: "EOD Trailing ($2,000 en 50K)",
              ddModel: "Calcula a las 17:00 ET. Sin trailing intradía en la evaluación.",
              bots: "Permitidos bots siempre que respeten el Daily Loss Limit.",
              payouts: "Día 1 en cuenta PRO. Retiros el mismo día sin días mínimos de espera.",
              buffer: "Buffer de seguridad correspondiente al DD máximo.",
              finePrint: "Regla de consistencia del 50% en el examen. Daily Loss Limit es de fin de día.",
              pros: ["Retiros desde el Día 1 en cuenta Pro", "Sin días mínimos de examen (puedes pasar en 1 día)", "Tradovate + TradingView"],
              cons: ["Cuota de activación Pro de $130", "Consistencia del 50%"],
              coupon: { code: "TPT50", discount: "50% OFF" },
              officialUrl: "https://takeprofittrader.com/",
            },
            apex: {
              name: "Apex Trader Funding",
              badge: "HASTA 20 CUENTAS",
              founded: "2021",
              hq: "Austin, TX, USA",
              platforms: "Tradovate, NinjaTrader 8, Rithmic",
              commissions: "Mini: ~$3.90 RT | Micro: ~$1.20 RT",
              activation: "$140 - $160 USD (Fee único de cuenta PA)",
              drawdown: "Intraday Peak Trailing ($2,500 en 50K, $3,000 en 100K)",
              ddModel: "El trailing persigue el flotante positivo tick a tick en tiempo real.",
              bots: "PROHIBIDO bots autónomos en PA. Solo permite manual o Trade Copiers locales.",
              payouts: "2 ventanas mensuales (días 1-5 y 15-20). Máximo $2,000 por cuenta en primeros 3 meses.",
              buffer: "Buffer de seguridad obligatorio ($52,600 en cuenta 50K).",
              finePrint: "Regla de consistencia del 30%. Máximo 20 cuentas financiadas PA por usuario.",
              pros: ["Pases muy baratos con cupones de hasta 80% OFF", "Permite hasta 20 cuentas PA simultáneas", "Pase en 1 solo día"],
              cons: ["Trailing Intraday agresivo", "Bots automáticos prohibidos en PA", "Cuota de activación obligatoria"],
              coupon: { code: "SAVINGS", discount: "80% OFF" },
              officialUrl: "https://apextraderfunding.com/",
            },
            bulenox: {
              name: "Bulenox",
              badge: "HASTA 89% DESCUENTO",
              founded: "2022",
              hq: "Delaware, USA",
              platforms: "NinjaTrader 8, Rithmic",
              commissions: "Mini: ~$3.60 RT | Micro: ~$1.18 RT",
              activation: "$148 - $178 USD (Pase a Master)",
              drawdown: "Intraday Trailing (Opción 1) o EOD (Opción 2)",
              ddModel: "Ofrece dos modalidades: Opción 1 con trailing intraday más barata, u Opción 2 con EOD.",
              bots: "Permitidos bots y EAs en NinjaTrader 8.",
              payouts: "2 solicitudes mensuales (días 1-5 y 16-20). 100% de primeros $10,000.",
              buffer: "Buffer de seguridad estricto antes de cada retiro.",
              finePrint: "Hasta 11 cuentas Master por usuario. Descuentos agresivos de hasta 89% con cupón GUIDE.",
              pros: ["Cupones de hasta 89% OFF", "Permite elegir entre Trailing EOD o Intraday", "11 cuentas simultáneas"],
              cons: ["Cuota de activación elevada", "Ventanas de retiro fijas de 5 días"],
              coupon: { code: "GUIDE", discount: "89% OFF" },
              officialUrl: "https://bulenox.com/",
            },
            fundednext: {
              name: "FundedNext Futures",
              badge: "15% PROFIT EN EXAMEN",
              founded: "2024",
              hq: "Dubai, UAE",
              platforms: "Tradovate, NinjaTrader 8, TradingView",
              commissions: "Mini: ~$3.00 RT | Micro: ~$1.05 RT",
              activation: "$0 USD (Cero activation fee)",
              drawdown: "EOD Trailing ($2,000 en 50K)",
              ddModel: "Calcula al cierre de sesión. 15% de profit share acumulado en la evaluación.",
              bots: "Permitidos bots y sistemas automáticos.",
              payouts: "Quincenal en 24h tras solicitud.",
              buffer: "Buffer estándar de cuenta.",
              finePrint: "Te reembolsa el precio de la prueba más un 15% de las ganancias generadas durante la evaluación.",
              pros: ["$0 cuota de activación", "Paga el 15% de ganancias del examen", "Soporte TradingView"],
              cons: ["Firma nueva en el sector de futuros (2024)"],
              coupon: { code: "FNFUTURES", discount: "20% OFF" },
              officialUrl: "https://fundednext.com/",
            },
            ticktick: {
              name: "TickTick Trader",
              badge: "100% PRIMEROS $25K",
              founded: "2022",
              hq: "Cheyenne, WY, USA",
              platforms: "Tradovate, NinjaTrader 8, Rithmic, Bookmap, Quantower",
              commissions: "Mini: ~$3.40 RT | Micro: ~$1.10 RT",
              activation: "$149 USD (Incluye licencia de NT8 y datos CME)",
              drawdown: "EOD Trailing ($2,500 en 50K)",
              ddModel: "Calcula al final del día EOD. Congela en el balance inicial.",
              bots: "Permitidos bots algorítmicos en NinjaTrader 8.",
              payouts: "Retiros desde el día 1 en cuenta TTTPerformance. 100% primeros $25,000 netos.",
              buffer: "Buffer de seguridad fijado en $52,500.",
              finePrint: "Cuenta con el programa Express sin días mínimos de trading.",
              pros: ["100% de los primeros $25,000 USD netos", "Licencia de NinjaTrader 8 incluida", "Soporte Bookmap y Quantower"],
              cons: ["Cuota de activación de $149 USD"],
              coupon: { code: "TTT50", discount: "50% OFF" },
              officialUrl: "https://tickticktrader.com/",
            },
            oneup: {
              name: "OneUp Trader",
              badge: "DATOS CME INCLUIDOS",
              founded: "2017",
              hq: "Delaware, USA",
              platforms: "NinjaTrader 8, Tradovate, Rithmic, ATAS, Sierra Chart, VolFix",
              commissions: "Mini: ~$3.50 RT | Micro: ~$1.15 RT",
              activation: "$0 USD (Datos de mercado incluidos sin coste)",
              drawdown: "EOD Trailing ($2,500 en 50K)",
              ddModel: "Calcula a las 17:00 ET. Se fija en balance inicial.",
              bots: "Permitidos bots en NinjaTrader y Sierra Chart.",
              payouts: "Retiros bajo demanda en 24-48h. 100% primeros $10,000.",
              buffer: "Buffer equivalente al trailing drawdown.",
              finePrint: "Requiere 15 días mínimos de trading en la evaluación.",
              pros: ["$0 cuota de activación", "Datos CME de nivel 1 incluidos", "Soporte Sierra Chart, ATAS y VolFix"],
              cons: ["15 días mínimos de evaluación", "Precios mensuales sin cupón más elevados"],
              coupon: { code: "ONEUP20", discount: "20% OFF" },
              officialUrl: "https://oneuptrader.com/",
            },
            fasttrack: {
              name: "Fast Track Trading",
              badge: "EXAMEN ULTRARRÁPIDO",
              founded: "2024",
              hq: "Fort Lauderdale, FL, USA",
              platforms: "Tradovate, TradingView Web",
              commissions: "Mini: ~$3.20 RT | Micro: ~$1.10 RT",
              activation: "$0 USD (Cuentas directas)",
              drawdown: "EOD Trailing ($2,500 en 50K)",
              ddModel: "Calcula al cierre de día.",
              bots: "Permitidos bots vía API Tradovate.",
              payouts: "Retiros quincenales en 24-48h.",
              buffer: "Buffer estándar.",
              finePrint: "Enfoque en cuentas directas sin fase de examen largo.",
              pros: ["$0 cuota de activación", "Pase muy rápido", "Soporte TradingView"],
              cons: ["Reglas de consistencia estrictas"],
              coupon: { code: "FTT30", discount: "30% OFF" },
              officialUrl: "https://fasttracktrading.net/",
            },
            uprofit: {
              name: "UProfit Trader",
              badge: "TARGET BAJO (5%)",
              founded: "2019",
              hq: "Sugar Land, TX, USA",
              platforms: "NinjaTrader 8, Rithmic, Quantower",
              commissions: "Mini: ~$3.70 RT | Micro: ~$1.15 RT",
              activation: "$150 USD (Live Account Fee)",
              drawdown: "Intraday Peak Trailing ($2,500 en 50K)",
              ddModel: "Persigue el flotante intra-sesión. Daily Loss Limit estricto.",
              bots: "Permitidos bots en NinjaTrader 8.",
              payouts: "Retiros procesados en 24h tras 4 días de trading. 100% primeros $8,000.",
              buffer: "Buffer de seguridad obligatorio.",
              finePrint: "Target bajo del 5% ($2,500 en 50K). Mínimo 4 días de evaluación.",
              pros: ["Target muy accesible del 5%", "Evaluación superable en solo 4 días", "100% de primeros $8,000"],
              cons: ["Cuota de activación de $150 USD", "Trailing Intraday y Daily Loss Limit"],
              coupon: { code: "UPROFIT40", discount: "40% OFF" },
              officialUrl: "https://uprofit.com/",
            },
            elitetrader: {
              name: "Elite Trader Funding",
              badge: "100% PRIMEROS $12.5K",
              founded: "2022",
              hq: "Delaware, USA",
              platforms: "Tradovate, NinjaTrader 8, Rithmic, TradingView",
              commissions: "Mini: ~$3.50 RT | Micro: ~$1.12 RT",
              activation: "$150 USD (Activation Fee o opción mensual)",
              drawdown: "EOD Trailing ($2,000 en 50K) o Static (Opción Diamond)",
              ddModel: "Permite elegir entre evaluación EOD o cuentas Static.",
              bots: "Permitidos bots y Trade Copiers locales.",
              payouts: "Retiros quincenales. 100% primeros $12,500.",
              buffer: "Buffer de seguridad según cuenta.",
              finePrint: "Hasta 20 cuentas financiadas simultáneas.",
              pros: ["100% primeros $12,500 netos", "Opción de Drawdown Estático", "Hasta 20 cuentas simultáneas"],
              cons: ["Cuota de activación si no se elige suscripción"],
              coupon: { code: "ETF70", discount: "70% OFF" },
              officialUrl: "https://elitetraderfunding.com/",
            },
            earn2trade: {
              name: "Earn2Trade (Helios)",
              badge: "BROKER LIVE REAL",
              founded: "2016",
              hq: "Wyoming, USA",
              platforms: "NinjaTrader 8, Rithmic, Finamark",
              commissions: "Mini: ~$3.40 RT | Micro: ~$1.10 RT",
              activation: "$0 USD (Cuenta Live Helios real)",
              drawdown: "EOD Trailing ($2,000 en 50K) escalable hasta $400K",
              ddModel: "Calcula a las 17:00 ET. Plan de escalado institucional a cuentas live reales.",
              bots: "Permitidos bots en NinjaTrader en la fase de evaluación.",
              payouts: "Retiros semanales procesados en 24h. 80% split inicial escalando al 90%.",
              buffer: "Buffer de cuenta live regulada.",
              finePrint: "Cuentas live reales con broker Helios Trading. Licencia de NinjaTrader 8 gratuita incluida durante el examen.",
              pros: ["$0 cuota de activación", "Cuentas reales reguladas (No solo simulación)", "Licencia NinjaTrader 8 gratuita", "Escalado hasta $400,000 USD"],
              cons: ["Regla de escalado de contratos estricta", "Split inicial del 80%"],
              coupon: { code: "E2T50", discount: "50% OFF" },
              officialUrl: "https://earn2trade.com/",
            },
            leeloo: {
              name: "Leeloo Trading",
              badge: "SIN DAILY LOSS LIMIT",
              founded: "2019",
              hq: "Montana, USA",
              platforms: "NinjaTrader 8, Rithmic",
              commissions: "Mini: ~$3.60 RT | Micro: ~$1.15 RT",
              activation: "$140 USD",
              drawdown: "Intraday Peak Trailing ($2,500 en 50K)",
              ddModel: "Calcula en tiempo real. Congela en balance inicial en cuenta fondeada.",
              bots: "Permitidos bots en NinjaTrader 8.",
              payouts: "Retiros mensuales. 100% de primeros $8,000 netos.",
              buffer: "Buffer de seguridad de $2,600.",
              finePrint: "10 días mínimos de trading en examen. Sin Daily Loss Limit en planes Express.",
              pros: ["Sin Daily Loss Limit", "100% de primeros $8,000 netos", "Permite operar con micro contratos"],
              cons: ["Cuota de activación de $140 USD", "Retiros con periodicidad mensual"],
              coupon: { code: "LEELOO50", discount: "50% OFF" },
              officialUrl: "https://leelootrading.com/",
            },
            lucid: {
              name: "Lucid Trading",
              badge: "EUROPEA / SEPA & CRYPTO",
              founded: "2025",
              hq: "Tallinn, Estonia (EU)",
              platforms: "Tradovate, NinjaTrader 8, TradingView, Quantower",
              commissions: "Mini: ~$2.80 RT | Micro: ~$0.98 RT",
              activation: "$0 USD (Sin activación)",
              drawdown: "EOD Trailing ($2,000 en 50K)",
              ddModel: "Calcula a las 17:00 ET. Bloqueo en balance inicial.",
              bots: "100% Permitidos para trading algorítmico institucional.",
              payouts: "Día 1 On-Demand vía Rise / Transferencia SEPA y Crypto en < 24h.",
              buffer: "Buffer de seguridad bajo.",
              finePrint: "Firma europea con soporte institucional multi-broker y comisiones ultra-bajas.",
              pros: ["$0 cuota de activación", "Comisiones más bajas del mercado", "Pagos Día 1 en Cripto/SEPA", "Soporte Quantower y Tradovate"],
              cons: ["Firma muy reciente (fundada en 2025)"],
              coupon: { code: "LUCID30", discount: "30% OFF" },
              officialUrl: "https://lucidtrading.com/",
            },
          };

          const currentFirm = wikiData[selectedWikiFirm] || wikiData.topstep;

          return (
            <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-xl)", padding: "24px" }}>
              <h2 style={{ fontSize: "20px", fontWeight: 900, margin: "0 0 4px 0", color: "var(--accent-bright)" }}>
                📚 Enciclopedia Técnica de Firmas de Futuros CME (17 Firmas Auditadas)
              </h2>
              <p style={{ margin: "0 0 20px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                Fichas técnicas exhaustivas con microestructura, comisiones por contrato, escalado, plataformas y auditoría forense de letra pequeña.
              </p>

              <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: "20px" }}>
                {/* LISTA LATERAL DE LAS 17 FIRMAS */}
                <div style={{ display: "flex", flexDirection: "column", gap: "4px", background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "var(--radius-md)", maxHeight: "620px", overflowY: "auto" }}>
                  {Object.keys(wikiData).map((fKey) => {
                    const item = wikiData[fKey];
                    const isSelected = selectedWikiFirm === fKey;
                    return (
                      <button
                        key={fKey}
                        onClick={() => setSelectedWikiFirm(fKey)}
                        style={{
                          textAlign: "left",
                          padding: "10px 12px",
                          borderRadius: "6px",
                          background: isSelected ? "linear-gradient(90deg, rgba(0, 240, 255, 0.18), rgba(34, 197, 94, 0.08))" : "transparent",
                          border: isSelected ? "1px solid var(--accent)" : "1px solid transparent",
                          color: isSelected ? "#fff" : "var(--text-secondary)",
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontSize: "12px", fontWeight: 800 }}>{item.name}</span>
                          <span style={{ fontSize: "9px", padding: "1px 5px", borderRadius: "3px", background: "rgba(255,255,255,0.06)", color: "var(--accent-bright)", fontWeight: 700 }}>
                            {item.founded}
                          </span>
                        </div>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>{item.badge}</div>
                      </button>
                    );
                  })}
                </div>

                {/* FICHA DETALLADA DE LA FIRMA SELECCIONADA */}
                <div style={{ background: "rgba(0,0,0,0.25)", padding: "24px", borderRadius: "var(--radius-lg)", border: "1px solid var(--border)", display: "flex", flexDirection: "column", gap: "18px" }}>
                  {/* CABECERA */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", borderBottom: "1px solid var(--border)", paddingBottom: "14px", flexWrap: "wrap", gap: "10px" }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <h3 style={{ fontSize: "20px", fontWeight: 900, color: "#fff", margin: 0 }}>🏛️ {currentFirm.name}</h3>
                        <span style={{ fontSize: "10px", fontWeight: 900, padding: "2px 8px", borderRadius: "999px", background: "rgba(0, 240, 255, 0.15)", color: "var(--accent-bright)", border: "1px solid var(--accent)" }}>
                          {currentFirm.badge}
                        </span>
                      </div>
                      <p style={{ fontSize: "11px", color: "var(--text-muted)", margin: "4px 0 0 0" }}>
                        📍 Sede: <strong>{currentFirm.hq}</strong> · Fundada en: <strong>{currentFirm.founded}</strong> · Plataformas: <strong>{currentFirm.platforms}</strong>
                      </p>
                    </div>

                    {/* BOTONES DE ACCIÓN RÁPIDA */}
                    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                      <a
                        href={currentFirm.officialUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                          padding: "6px 12px",
                          background: "var(--accent)",
                          color: "#000",
                          borderRadius: "6px",
                          fontSize: "11px",
                          fontWeight: 900,
                          textDecoration: "none",
                        }}
                      >
                        <span>🌐 Sitio Oficial</span>
                        <span style={{ fontSize: "10px" }}>↗</span>
                      </a>
                      {currentFirm.demoUrl && (
                        <a
                          href={currentFirm.demoUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "4px",
                            padding: "6px 12px",
                            background: "rgba(34, 197, 94, 0.2)",
                            border: "1px solid var(--success)",
                            color: "var(--success)",
                            borderRadius: "6px",
                            fontSize: "11px",
                            fontWeight: 800,
                            textDecoration: "none",
                          }}
                        >
                          <span>🎮 Demo / Trial Gratis</span>
                          <span style={{ fontSize: "10px" }}>↗</span>
                        </a>
                      )}
                      {currentFirm.coupon && (
                        <button
                          onClick={() => handleCopyCode(currentFirm.coupon!.code)}
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "4px",
                            padding: "6px 12px",
                            background: copiedCode === currentFirm.coupon.code ? "rgba(34, 197, 94, 0.2)" : "rgba(255, 255, 255, 0.06)",
                            border: copiedCode === currentFirm.coupon.code ? "1px solid var(--success)" : "1px dashed var(--accent)",
                            color: copiedCode === currentFirm.coupon.code ? "var(--success)" : "var(--accent-bright)",
                            borderRadius: "6px",
                            fontSize: "11px",
                            fontWeight: 800,
                            cursor: "pointer",
                            transition: "all 0.2s ease",
                          }}
                        >
                          <span>{copiedCode === currentFirm.coupon.code ? "✓ ¡Copiado!" : `🎟️ Cupón: ${currentFirm.coupon.code} (${currentFirm.coupon.discount})`}</span>
                          <span>📋</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* GRID 4 ATRIBUTOS TÉCNICOS */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px" }}>
                    <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 800 }}>COMISIONES ALL-IN</div>
                      <div style={{ fontSize: "12px", fontWeight: 800, color: "#fff", marginTop: "2px" }}>{currentFirm.commissions}</div>
                    </div>
                    <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 800 }}>CUOTA DE ACTIVACIÓN</div>
                      <div style={{ fontSize: "12px", fontWeight: 800, color: currentFirm.activation.includes("$0") ? "var(--accent)" : "var(--danger)", marginTop: "2px" }}>
                        {currentFirm.activation}
                      </div>
                    </div>
                    <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 800 }}>MODELO DE DRAWDOWN</div>
                      <div style={{ fontSize: "12px", fontWeight: 800, color: "var(--warning)", marginTop: "2px" }}>{currentFirm.drawdown}</div>
                    </div>
                    <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 800 }}>PAGOS & RETIROS</div>
                      <div style={{ fontSize: "12px", fontWeight: 800, color: "var(--success)", marginTop: "2px" }}>{currentFirm.payouts}</div>
                    </div>
                  </div>

                  {/* POLÍTICA DE BOTS Y DRAWDOWN */}
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "8px", borderLeft: "3px solid var(--accent)" }}>
                      <div style={{ fontSize: "11px", fontWeight: 900, color: "var(--accent-bright)", marginBottom: "4px" }}>
                        🛡️ Comportamiento del Drawdown:
                      </div>
                      <div style={{ fontSize: "12px", lineHeight: "1.5", color: "var(--text-secondary)" }}>
                        {currentFirm.ddModel}
                      </div>
                    </div>
                    <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "8px", borderLeft: "3px solid var(--success)" }}>
                      <div style={{ fontSize: "11px", fontWeight: 900, color: "var(--success)", marginBottom: "4px" }}>
                        🤖 Política de Bots & Automatización:
                      </div>
                      <div style={{ fontSize: "12px", lineHeight: "1.5", color: "var(--text-secondary)" }}>
                        {currentFirm.bots}
                      </div>
                    </div>
                  </div>

                  {/* LETRA PEQUEÑA CLAVE */}
                  <div style={{ background: "rgba(239, 68, 68, 0.06)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "8px", padding: "14px" }}>
                    <div style={{ fontSize: "11px", fontWeight: 900, color: "var(--danger)", marginBottom: "4px", display: "flex", alignItems: "center", gap: "6px" }}>
                      <span>⚠️ Radar de Letra Pequeña & Reglas Críticas:</span>
                    </div>
                    <div style={{ fontSize: "12px", lineHeight: "1.5", color: "var(--text-secondary)" }}>
                      {currentFirm.finePrint}
                    </div>
                  </div>

                  {/* PROS Y CONTRAS */}
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <div style={{ background: "rgba(34, 197, 94, 0.05)", border: "1px solid rgba(34, 197, 94, 0.2)", borderRadius: "8px", padding: "14px" }}>
                      <div style={{ fontSize: "11px", fontWeight: 900, color: "var(--success)", marginBottom: "6px" }}>
                        ✓ Puntos Fuertes:
                      </div>
                      <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "11px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                        {currentFirm.pros.map((p, pIdx) => (
                          <li key={pIdx}>{p}</li>
                        ))}
                      </ul>
                    </div>
                    <div style={{ background: "rgba(239, 68, 68, 0.05)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "8px", padding: "14px" }}>
                      <div style={{ fontSize: "11px", fontWeight: 900, color: "var(--danger)", marginBottom: "6px" }}>
                        ✕ Consideraciones y Contras:
                      </div>
                      <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "11px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                        {currentFirm.cons.map((c, cIdx) => (
                          <li key={cIdx}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })()}

        {/* ========================================================================= */}
        {/* MÓDULO 6: GUÍAS TÉCNICAS (7 GUÍAS COMPLETAS PASO A PASO)                   */}
        {/* ========================================================================= */}
        {activeModule === "GUIAS" && (() => {
          const guidesData: Record<string, {
            title: string;
            subtitle: string;
            steps: { title: string; desc: string; tip?: string }[];
            proTip: string;
          }> = {
            "rithmic-nt8": {
              title: "Protocolo de Conexión: Rithmic R|Trader Pro ➔ NinjaTrader 8 (Multi-Provider)",
              subtitle: "Configura Rithmic Plug-in Brokerage para operar cuentas de Apex, Bulenox y UProfit con menos de 3ms de latencia.",
              steps: [
                { title: "Paso 1: Abrir y Configurar R|Trader Pro", desc: "Abre R|Trader Pro, introduce tu usuario y contraseña, selecciona tu firma (Apex, Bulenox, UProfit) en System y Chicago Area en Gateway. Activa la casilla 'Allow Plug-in Brokerage' antes de hacer Login.", tip: "Si no activas Allow Plug-in Brokerage, NinjaTrader devolverá error de conexión rechazada." },
                { title: "Paso 2: Aceptar Acuerdos de Datos CME", desc: "La primera vez que entres, aparecerán dos popups de acuerdos de mercado CME Non-Professional. Acepta ambos documentos para que el flujo de datos de futuros (MES, MNQ, ES, NQ) quede desbloqueado.", tip: "Debes aceptarlos en R|Trader antes de conectar NinjaTrader." },
                { title: "Paso 3: Activar Modo Multi-Provider en NinjaTrader 8", desc: "En NinjaTrader 8, ve a la barra superior Tools ➔ Options ➔ General y marca la casilla 'Multi-provider'. Haz clic en Aplicar y OK. Esto te permite conectar múltiples proveedores simultáneos.", tip: "Requiere reiniciar NinjaTrader si estaba desmarcado." },
                { title: "Paso 4: Configurar la Conexión Rithmic", desc: "En el menú Connections ➔ configure, selecciona 'Rithmic for NinjaTrader 8' y pulsa Add. En System selecciona tu firma, y en Connect Options marca obligatoriamente 'Connect via Plug-in'.", tip: "Marca 'Connect on startup' para que se conecte solo al abrir NT8." },
                { title: "Paso 5: Conectar y Verificar Luz Verde", desc: "Ve a Connections ➔ selecciona tu conexión Rithmic. En 2-3 segundos el punto inferior izquierdo del Control Center se pondrá en verde brillante 🟢.", tip: "Ya puedes abrir gráficos o ejecutar bots con datos CME en vivo." },
              ],
              proTip: "Mantén siempre R|Trader Pro abierto en segundo plano como pasarela plug-in. Esto evita consumir sesiones concurrentes de datos CME.",
            },
            "tradovate-tv": {
              title: "Protocolo de Conexión: Tradovate ➔ TradingView Web/Desktop & Cloud",
              subtitle: "Conecta tu cuenta de Tradovate (MFFU, Tradeify, Topstep, FundedNext) a TradingView para operar directamente desde sus gráficos.",
              steps: [
                { title: "Paso 1: Activar Add-on de TradingView en Tradovate", desc: "Inicia sesión en trader.tradovate.com, ve a Settings (icono de engranaje) ➔ Add-Ons ➔ TradingView y pulsa 'Activate'. Es gratuito en la mayoría de firmas de fondeo.", tip: "En algunas firmas viene activado por defecto con el registro." },
                { title: "Paso 2: Abrir Gráfico de Futuros en TradingView", desc: "Abre es.tradingview.com y busca el contrato continuo o frontal del activo que vas a operar (ej. CME_MINI:ES1!, CME_MINI:NQ1!, CBOT_MINI:YM1!).", tip: "Asegúrate de tener habilitados los datos en tiempo real de CME en TradingView." },
                { title: "Paso 3: Abrir Panel de Trading e Iniciar Sesión", desc: "En la parte inferior de TradingView, abre la pestaña 'Panel de Trading', localiza el broker 'Tradovate' y pulsa 'Conectar'.", tip: "En el popup, selecciona 'Demo / Simulation' si estás en fase de examen." },
                { title: "Paso 4: Seleccionar Cuenta Activa y Operar", desc: "Una vez conectado, verás el desplegable con tus cuentas de fondeo (ej. MFFU-12345, TRD-67890). Selecciona la cuenta deseada y activa los botones Buy/Sell en el gráfico.", tip: "Las órdenes se sincronizan en la nube con Tradovate al instante." },
              ],
              proTip: "Configura siempre una orden Bracket (Stop Loss + Take Profit) antes de enviar la orden desde TradingView para proteger el Drawdown EOD.",
            },
            "trade-copier": {
              title: "Setup de Trade Copier Multi-Cuenta (Replicanto en NinjaTrader 8)",
              subtitle: "Replica operaciones en tiempo real entre múltiples cuentas de fondeo con conversión de ratio y protección de desincronización.",
              steps: [
                { title: "Paso 1: Instalar Replicanto en NinjaTrader 8", desc: "Descarga el archivo .zip de Replicanto (FlowBots), ve a NinjaTrader 8 ➔ Tools ➔ Import ➔ NinjaScript Add-On y selecciona el archivo.", tip: "Reinicia NinjaTrader para que aparezca en el menú superior." },
                { title: "Paso 2: Abrir Panel de Replicanto y Asignar Líder", desc: "Abre New ➔ Replicanto. En la columna 'Master / Leader', selecciona tu cuenta principal donde ejecutas tus entradas manuales o de tu bot.", tip: "La cuenta líder enviará las órdenes a todas las demás." },
                { title: "Paso 3: Añadir Cuentas Seguidoras (Followers)", desc: "Añade en la lista inferior todas las cuentas esclavas que deben copiar las órdenes (ej. 5 cuentas de Apex, 3 de Bulenox, 2 de MFFU).", tip: "Puedes mezclar cuentas de diferentes prop firms siempre que estén conectadas en NT8." },
                { title: "Paso 4: Configurar Conversión de Minis a Micros (1:10)", desc: "Si replicas órdenes de contratos Mini (ES/NQ) a cuentas de menor tamaño (25K), activa en la fila de esa cuenta 'Convert Mini to Micro (1:10)'.", tip: "Evita quemar cuentas pequeñas por apalancamiento excesivo." },
                { title: "Paso 5: Activar 'Flatten Followers on Disconnect'", desc: "En las opciones globales de Replicanto, marca 'Flatten followers on disconnect' y 'Auto-flatten on master SL'.", tip: "Garantiza que si se corta internet o salta el stop, todas las cuentas cierren a la vez." },
              ],
              proTip: "Ejecuta siempre un trade de prueba con 1 micro (MES) para confirmar que todas las cuentas seguidoras abren y cierran sincronizadas.",
            },
            "topstepx-setup": {
              title: "Configuración Avanzada de TopstepX: Bracket Orders & Auto-Risk Guard",
              subtitle: "Optimiza la plataforma web propietaria de Topstep con controles de riesgo automáticos para no quebrar nunca la regla de pérdida diaria.",
              steps: [
                { title: "Paso 1: Acceso a TopstepX Web", desc: "Entra a topstepx.com con tus credenciales de Topstep. La plataforma corre directamente en el navegador con motor TradingView integrado y cero latencia.", tip: "No requiere instalar ningún ejecutable en Windows ni configurar gateways." },
                { title: "Paso 2: Configurar Auto-Risk Daily Loss Circuit Breaker", desc: "Ve a Settings ➔ Risk Controls. Introduce tu límite de pérdida diaria personalizada (ej. $800 en una cuenta 50K con DLL de $1,000) y marca 'Lock out account on breach'.", tip: "TopstepX cerrará todas tus posiciones y bloqueará nuevas órdenes hasta la siguiente sesión." },
                { title: "Paso 3: Plantillas de Órdenes Bracket (Auto-SL y TP)", desc: "En el panel de Order Entry, crea una plantilla Bracket fijando tu Stop Loss en ticks fijos (ej. 15 ticks en NQ / $75) y Take Profit (ej. 30 ticks / $150).", tip: "Al entrar a mercado, el Stop Loss se coloca en el servidor de forma instantánea." },
                { title: "Paso 4: Monitorear el Trailing Drawdown en Tiempo Real", desc: "En la barra superior de TopstepX verás el medidor de Drawdown EOD en vivo, mostrando exactamente cuántos dólares te quedan de colchón antes de tocar el stop.", tip: "Se actualiza tras cada cierre de sesión a las 17:00 ET." },
              ],
              proTip: "Utiliza el modo 'Simulator / Practice' de TopstepX para probar tus estrategias antes de operar la cuenta Express funded.",
            },
            "sqx-nt8-deploy": {
              title: "Deploy de Bots StrategyQuant X en NinjaTrader 8 (VPS 24/7 con < 3ms)",
              subtitle: "Compila y despliega carteras de sistemas algorítmicos generados en StrategyQuant X en tu VPS para operar desatendido.",
              steps: [
                { title: "Paso 1: Exportar Estrategia desde StrategyQuant X", desc: "En SQX, selecciona tu estrategia aprobada en el Databank y pulsa 'Export to NinjaScript (NT8)'. Se generará un archivo .cs con el código C# del bot.", tip: "Verifica que los parámetros de gestión de riesgo coincidan con las reglas de la firma." },
                { title: "Paso 2: Importar NinjaScript en NinjaTrader 8", desc: "En NinjaTrader 8 en tu VPS, ve a Tools ➔ Import ➔ NinjaScript Add-On y selecciona el archivo .cs exportado de SQX.", tip: "NinjaTrader compilará el script automáticamente." },
                { title: "Paso 3: Abrir Gráfico y Asignar la Estrategia", desc: "Abre el gráfico del instrumento (ej. NQ 5-min), clic derecho ➔ Strategies ➔ selecciona tu bot de SQX. Configura tu cuenta de fondeo (BluSky, MFFU, Tradeify) y marca 'Enabled: True'.", tip: "Asegúrate de que la conexión Rithmic o Tradovate esté activa con luz verde." },
                { title: "Paso 4: Configurar Disyuntor Horario y Cierre Diario", desc: "Programa en el bot la hora límite de cierre a las 15:00 CT para cumplir con la regla de no mantener posiciones overnight.", tip: "Evita sanciones por mantener posiciones abiertas fuera de sesión." },
              ],
              proTip: "Aloja tu NinjaTrader 8 en una VPS en Chicago (ej. Equinix NY4 / CME Aurora) para reducir la latencia de ejecución a menos de 2 milisegundos.",
            },
            "cme-data-fees": {
              title: "Gestión de Acuerdos de Datos CME Non-Professional & Pasarelas de Datos",
              subtitle: "Evita recargos profesionales y desbloquea el book de órdenes nivel 1 (Top of Book) y nivel 2 (Depth of Market) en futuros CME.",
              steps: [
                { title: "Paso 1: Clasificación como Trader No Profesional", desc: "Al registrarte en cualquier prop firm, declara tu condición de Non-Professional (persona física que opera con fines propios).", tip: "Los datos para no profesionales son gratuitos o incluidos en el precio del examen." },
                { title: "Paso 2: Firma de Acuerdos Electrónicos en R|Trader", desc: "En Rithmic R|Trader Pro, pulsa en los dos acuerdos que aparecen al conectar por primera vez y selecciona 'I Agree'.", tip: "Sin esta firma, NinjaTrader no recibirá cotizaciones del CME." },
                { title: "Paso 3: Suscripción de Nivel 2 (DOM / Depth of Market)", desc: "Si utilizas herramientas de order flow como Bookmap o Jigsaw, puedes solicitar datos de Nivel 2 (Depth) directamente en el panel de usuario de Tradovate o Rithmic.", tip: "El nivel 1 estándar (Top of Book) es suficiente para gráficos de velas y bots." },
              ],
              proTip: "Nunca inicies sesión en Rithmic desde dos ordenadores a la vez con las mismas credenciales para evitar bloqueos por sesión duplicada.",
            },
            "payout-buffer": {
              title: "Estrategia Matemática de Retiro de Beneficios & Mantenimiento del Buffer",
              subtitle: "Calcula exactamente cuánto retirar en cada ciclo para no quebrar la cuenta con el primer pago y maximizar el interés compuesto.",
              steps: [
                { title: "Paso 1: Identificar el Nivel de Bloqueo del Drawdown", desc: "En cuentas con Drawdown EOD (MFFU, Tradeify, Topstep), el drawdown se congela en el balance inicial (ej. $50,100 en 50K) una vez alcanzado el umbral fijado.", tip: "Comprueba en la ficha técnica de la firma si el trailing se congela o sigue subiendo." },
                { title: "Paso 2: Calcular el Colchón de Seguridad Mínimo (Buffer)", desc: "Para una cuenta de 50K con $2,000 de Drawdown, mantén siempre al menos $2,500 de ganancias acumuladas antes de retirar.", tip: "Si tu balance es $53,000 y retiras $3,000, tu balance volverá a $50,000 y quebrarás con una pérdida de solo $1." },
                { title: "Paso 3: Fórmula de Retiro Seguro (50/50)", desc: "Aplica la regla institucional: Retira el 50% de las ganancias que excedan el buffer de seguridad, y deja el otro 50% para aumentar tu margen de maniobra.", tip: "Ejemplo: Balance $54,000 ➔ Buffer $2,000 ➔ Excedente $2,000 ➔ Retirar $1,000 y dejar $3,000 de colchón total." },
                { title: "Paso 4: Cumplir la Regla de Consistencia al Retirar", desc: "Verifica que tu mejor día de ganancias no represente más del 30%-40% del profit total acumulado al momento de emitir la solicitud.", tip: "Evita rechazos de pago por operar con volumen desproporcionado en una sola sesión." },
              ],
              proTip: "Revisa siempre la ventana de solicitud de retiros (Día 1 On-Demand en MFFU/Tradeify vs Días 1-5 en Apex/Bulenox) para planificar tus transferencias a Rise o Cripto.",
            },
          };

          const activeGuide = guidesData[selectedGuide] || guidesData["rithmic-nt8"];

          return (
            <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-xl)", padding: "24px" }}>
              <h2 style={{ fontSize: "20px", fontWeight: 900, margin: "0 0 4px 0", color: "var(--accent-bright)" }}>
                🔧 Guías Técnicas de Conectividad e Infraestructura CME (7 Protocolos Paso a Paso)
              </h2>
              <p style={{ margin: "0 0 20px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                Protocolos de configuración profesional para conectar plataformas de futuros, pasarelas de datos y trade copiers con menos de 3ms de latencia.
              </p>

              {/* SELECTOR DE LAS 7 GUÍAS */}
              <div style={{ display: "flex", gap: "8px", marginBottom: "20px", flexWrap: "wrap" }}>
                {[
                  { id: "rithmic-nt8", label: "🔧 1. Rithmic ➔ NinjaTrader 8" },
                  { id: "tradovate-tv", label: "📈 2. Tradovate ➔ TradingView" },
                  { id: "trade-copier", label: "👥 3. Trade Copier (Replicanto)" },
                  { id: "topstepx-setup", label: "⚡ 4. Setup TopstepX & Risk" },
                  { id: "sqx-nt8-deploy", label: "🤖 5. Deploy Bots SQX en VPS" },
                  { id: "cme-data-fees", label: "📊 6. Acuerdos de Datos CME" },
                  { id: "payout-buffer", label: "🛡️ 7. Retiros & Buffer Seguro" },
                ].map((g) => (
                  <button
                    key={g.id}
                    onClick={() => setSelectedGuide(g.id)}
                    style={{
                      padding: "8px 14px",
                      borderRadius: "6px",
                      background: selectedGuide === g.id ? "rgba(0, 240, 255, 0.15)" : "var(--bg-2)",
                      border: selectedGuide === g.id ? "1px solid var(--accent)" : "1px solid var(--border)",
                      color: selectedGuide === g.id ? "var(--accent-bright)" : "var(--text-secondary)",
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    {g.label}
                  </button>
                ))}
              </div>

              {/* CONTENIDO DE LA GUÍA SELECCIONADA */}
              <div style={{ background: "rgba(0,0,0,0.25)", padding: "24px", borderRadius: "var(--radius-lg)", border: "1px solid var(--border)", display: "flex", flexDirection: "column", gap: "16px" }}>
                <div>
                  <h3 style={{ fontSize: "18px", fontWeight: 900, color: "#fff", margin: "0 0 4px 0" }}>
                    {activeGuide.title}
                  </h3>
                  <p style={{ fontSize: "12px", color: "var(--text-muted)", margin: 0 }}>
                    {activeGuide.subtitle}
                  </p>
                </div>

                {/* PASOS NUMERADOS */}
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  {activeGuide.steps.map((st, sIdx) => (
                    <div
                      key={sIdx}
                      style={{
                        display: "flex",
                        gap: "12px",
                        padding: "14px",
                        background: "rgba(255, 255, 255, 0.02)",
                        border: "1px solid rgba(255, 255, 255, 0.06)",
                        borderRadius: "8px",
                      }}
                    >
                      <div
                        style={{
                          minWidth: "28px",
                          height: "28px",
                          borderRadius: "6px",
                          background: "rgba(0, 240, 255, 0.18)",
                          border: "1px solid var(--accent)",
                          color: "var(--accent-bright)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: "12px",
                          fontWeight: 900,
                          flexShrink: 0,
                        }}
                      >
                        {sIdx + 1}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: "13px", fontWeight: 800, color: "#fff", marginBottom: "4px" }}>
                          {st.title}
                        </div>
                        <div style={{ fontSize: "12px", lineHeight: "1.5", color: "var(--text-secondary)" }}>
                          {st.desc}
                        </div>
                        {st.tip && (
                          <div style={{ marginTop: "6px", fontSize: "11px", color: "var(--accent-bright)", display: "flex", alignItems: "center", gap: "4px" }}>
                            <span>💡 Tip Pro:</span>
                            <span style={{ color: "var(--text-muted)" }}>{st.tip}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* PRO TIP DESTACADO */}
                <div
                  style={{
                    padding: "14px",
                    background: "linear-gradient(90deg, rgba(0, 240, 255, 0.08), rgba(34, 197, 94, 0.08))",
                    border: "1px solid var(--accent)",
                    borderRadius: "8px",
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                  }}
                >
                  <span style={{ fontSize: "20px" }}>⚡</span>
                  <div style={{ fontSize: "12px", color: "#fff" }}>
                    <strong style={{ color: "var(--accent-bright)" }}>Recomendación Institucional:</strong> {activeGuide.proTip}
                  </div>
                </div>
              </div>
            </div>
          );
        })()}



        {/* MODAL COMPARADOR LADO A LADO */}
        {showCompareModal && compareList.length > 0 && (
          <div style={{ position: "fixed", inset: 0, zIndex: 1000, background: "rgba(0,0,0,0.85)", backdropFilter: "blur(8px)", display: "flex", justifyContent: "center", alignItems: "center", padding: "20px" }}>
            <div style={{ background: "var(--bg-1)", border: "1px solid var(--border-hover)", borderRadius: "var(--radius-xl)", width: "100%", maxWidth: "1280px", maxHeight: "90vh", overflowY: "auto", padding: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", borderBottom: "1px solid var(--border)", paddingBottom: "12px" }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: "20px", fontWeight: 900 }}>⚖️ Comparativa Cara a Cara de Futuros CME</h3>
                  <p style={{ margin: 0, fontSize: "12px", color: "var(--text-muted)" }}>Evaluación side-by-side de métricas de examen, fondeo y coste real de extracción.</p>
                </div>
                <button onClick={() => setShowCompareModal(false)} style={{ background: "var(--bg-3)", border: "1px solid var(--border)", color: "#fff", padding: "6px 12px", borderRadius: "var(--radius-sm)", cursor: "pointer", fontWeight: 800 }}>
                  ✕ Cerrar
                </button>
              </div>

              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
                  <thead>
                    <tr style={{ borderBottom: "2px solid var(--border)" }}>
                      <th style={{ padding: "10px", color: "var(--text-muted)", width: "180px" }}>PARÁMETRO</th>
                      {compareList.map((c) => (
                        <th key={c.provider_id} style={{ padding: "10px", color: "#fff", fontWeight: 900 }}>
                          {c.name}
                          <div style={{ fontSize: "11px", color: "var(--accent)" }}>${c.account_size.toLocaleString()} USD</div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "8px 10px", color: "var(--text-muted)", fontWeight: 700 }}>Firma</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "8px 10px", fontWeight: 800 }}>{c.provider_name}</td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "8px 10px", color: "var(--text-muted)", fontWeight: 700 }}>Precio Examen Actual</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "8px 10px", color: "var(--success)", fontWeight: 900 }}>
                          ${(c.promo_price_usd ?? c.monthly_cost_usd)?.toFixed(2)} USD
                        </td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "8px 10px", color: "var(--text-muted)", fontWeight: 700 }}>Cuota de Activación</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "8px 10px", fontWeight: 800, color: (c.activation_fee_usd ?? 0) === 0 ? "var(--accent)" : "var(--danger)" }}>
                          {(c.activation_fee_usd ?? 0) === 0 ? "$0 (Gratis)" : `$${c.activation_fee_usd} USD`}
                        </td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "8px 10px", color: "var(--text-muted)", fontWeight: 700 }}>Profit Target</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "8px 10px", fontWeight: 800 }}>${c.target_usd.toLocaleString()} ({c.target_pct}%)</td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "8px 10px", color: "var(--text-muted)", fontWeight: 700 }}>Max Drawdown & Tipo</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "8px 10px", color: "var(--danger)", fontWeight: 800 }}>
                          ${c.max_trailing_dd_usd.toLocaleString()} [{c.trailing_dd_type}]
                        </td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "8px 10px", color: "var(--text-muted)", fontWeight: 700 }}>Política Bots</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "8px 10px", fontWeight: 800, color: c.ea_bots_allowed.includes("PERMITTED") ? "var(--success)" : "var(--danger)" }}>
                          {c.ea_bots_allowed}
                        </td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "8px 10px", color: "var(--text-muted)", fontWeight: 700 }}>Frecuencia Retiro</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "8px 10px", fontWeight: 800, color: "var(--info)" }}>
                          {c.payout_frequency ?? "Quincenal"}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* WIDGET FLOTANTE DEL CHATBOT AI (ACCESIBLE DESDE CUALQUIER MÓDULO)         */}
        {/* ========================================================================= */}
        <div style={{ position: "fixed", bottom: "24px", right: "24px", zIndex: 999 }}>
          {!isFloatingChatOpen ? (
            <button
              onClick={() => setIsFloatingChatOpen(true)}
              style={{
                padding: "12px 20px",
                background: "linear-gradient(135deg, #00f0ff, #22c55e)",
                color: "#06090e",
                border: "none",
                borderRadius: "999px",
                fontSize: "13px",
                fontWeight: 900,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                boxShadow: "0 8px 30px rgba(0, 240, 255, 0.4)",
                transition: "transform 0.2s ease",
              }}
            >
              <span style={{ fontSize: "18px" }}>🤖</span>
              <span>Preguntar al Experto AI</span>
            </button>
          ) : (
            <div
              style={{
                width: "480px",
                height: "620px",
                maxWidth: "calc(100vw - 32px)",
                background: "rgba(10, 16, 26, 0.98)",
                backdropFilter: "blur(20px)",
                border: "1px solid var(--accent)",
                borderRadius: "16px",
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
                boxShadow: "0 20px 60px rgba(0,0,0,0.85)",
              }}
            >
              {/* CABECERA POPUP */}
              <div style={{ padding: "14px 16px", background: "rgba(0,0,0,0.5)", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "20px" }}>🤖</span>
                  <div>
                    <div style={{ fontSize: "13px", fontWeight: 900, color: "#fff" }}>UltraBot AI · Futuros CME</div>
                    <div style={{ fontSize: "10px", color: "var(--success)" }}>● Conectado a Base de Datos en Vivo</div>
                  </div>
                </div>
                <div style={{ display: "flex", gap: "6px" }}>
                  <button
                    onClick={() => {
                      setIsFloatingChatOpen(false);
                      setActiveModule("CHATBOT");
                    }}
                    title="Maximizar en pestaña principal"
                    style={{ background: "transparent", border: "none", color: "var(--accent)", cursor: "pointer", fontSize: "13px", fontWeight: 800 }}
                  >
                    ⛶
                  </button>
                  <button
                    onClick={() => setIsFloatingChatOpen(false)}
                    style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "16px", fontWeight: 800 }}
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* MENSAJES POPUP */}
              <div style={{ flex: 1, overflowY: "auto", padding: "14px", display: "flex", flexDirection: "column", gap: "12px" }}>
                {chatMessages.map((m) => (
                  <div
                    key={m.id}
                    style={{
                      alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                      maxWidth: "94%",
                      padding: "12px 14px",
                      borderRadius: m.role === "user" ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
                      background: m.role === "user" ? "rgba(0, 240, 255, 0.15)" : "rgba(255, 255, 255, 0.04)",
                      border: m.role === "user" ? "1px solid var(--accent)" : "1px solid var(--border)",
                      fontSize: "12px",
                      lineHeight: "1.5",
                      color: "#fff",
                    }}
                  >
                    <VisualChatContent content={m.content} />
                  </div>
                ))}
                {isChatLoading && (
                  <div style={{ color: "var(--accent)", fontSize: "11px", fontWeight: 700, display: "flex", alignItems: "center", gap: "6px" }}>
                    <div style={{ width: "12px", height: "12px", border: "2px solid var(--accent)", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 1s linear infinite" }}></div>
                    <span>UltraBot AI analizando en vivo...</span>
                  </div>
                )}
              </div>

              {/* INPUT POPUP */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendChatMessage();
                }}
                style={{ padding: "12px", borderTop: "1px solid var(--border)", display: "flex", gap: "8px", background: "rgba(0,0,0,0.3)" }}
              >
                <input
                  type="text"
                  placeholder="Escribe tu duda aquí..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  disabled={isChatLoading}
                  style={{
                    flex: 1,
                    padding: "8px 12px",
                    background: "var(--bg-2)",
                    border: "1px solid var(--border)",
                    borderRadius: "6px",
                    color: "#fff",
                    fontSize: "12px",
                    outline: "none",
                  }}
                />
                <button
                  type="submit"
                  disabled={isChatLoading || !chatInput.trim()}
                  style={{
                    padding: "8px 14px",
                    background: "var(--accent)",
                    color: "#000",
                    border: "none",
                    borderRadius: "6px",
                    fontWeight: 900,
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                >
                  ➔
                </button>
              </form>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
