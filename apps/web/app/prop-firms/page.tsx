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

export default function WorldClassFuturesPropFirmsPage() {
  const [activeModule, setActiveModule] = useState<MainNavModule>("CATALOGO");
  const [providers, setProviders] = useState<Provider[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
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

  // Fetching de datos de la API
  const fetchCatalog = () => {
    setIsLoading(true);
    fetch("/api/v1/providers?market_type=FUTURES")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) {
          const futuresOnly = data.filter((p) => p.market_type === "FUTURES");
          setProviders(futuresOnly);
          if (futuresOnly.length > 0 && !simSelectedFirmId) {
            setSimSelectedFirmId(futuresOnly[0].provider_id);
          }
        }
      })
      .catch((err) => console.error("Error loading providers:", err))
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
      const res = await fetch("/api/v1/providers/sync", { method: "POST" });
      const data = await res.json();
      setSyncMessage(data.message || "Sincronización de futuros completada con éxito.");
      fetchCatalog();
      setTimeout(() => setSyncMessage(null), 4500);
    } catch (e) {
      setSyncMessage("Error al sincronizar con el backend.");
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

  // Enviar mensaje al Chatbot Experto
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

      const res = await fetch("/api/v1/providers/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: query,
          history: historyPayload,
        }),
      });

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
    } catch (err) {
      const errorMessageObj: ChatMessage = {
        id: `bot-err-${Date.now()}`,
        role: "assistant",
        content: "⚠️ Hubo un problema al conectar con el motor analítico del chatbot. Por favor verifica la conexión.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setChatMessages((prev) => [...prev, errorMessageObj]);
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
      if (sortBy === "SCORE") return (b.trust_score ?? 90) - (a.trust_score ?? 90);
      return 0;
    });
  }, [providers, selectedTier, selectedDrawdown, selectedBotPolicy, onlyZeroActivation, onlyDayOnePayout, searchQuery, sortBy]);

  // Algoritmo del Wizard
  const wizardRecommendations = useMemo(() => {
    return providers.map((p) => {
      const price = p.promo_price_usd ?? p.monthly_cost_usd ?? p.regular_price_usd ?? 50;
      const activation = p.activation_fee_usd ?? 0;
      const totalCost = price + (wizIncludeActivation ? activation : 0);
      const pros: string[] = [];
      const cons: string[] = [];
      let score = Number(p.trust_score ?? 90);

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
      const target = selected?.target_usd ?? 3000;
      const maxDD = selected?.max_trailing_dd_usd ?? 2000;
      const isEOD = selected?.trailing_dd_type.includes("EOD") ?? true;
      const isStatic = selected?.trailing_dd_type.includes("Static") ?? false;

      let passes = 0;
      let ruins = 0;
      let totalDaysPass = 0;
      const iterations = 5000;

      const pWin = simWinRate / 100;
      const winAmt = simRiskPerTrade * simPayoffRatio;
      const lossAmt = simRiskPerTrade;

      for (let i = 0; i < iterations; i++) {
        let balance = 0;
        let peak = 0;
        let day = 0;
        let terminated = false;

        while (day < 60 && !terminated) {
          day++;
          for (let t = 0; t < simTradesPerDay; t++) {
            const isWin = Math.random() < pWin;
            balance += isWin ? winAmt : -lossAmt;

            if (!isEOD && !isStatic) {
              if (balance > peak) peak = balance;
              if (peak - balance >= maxDD) {
                ruins++;
                terminated = true;
                break;
              }
            }

            if (balance >= target) {
              passes++;
              totalDaysPass += day;
              terminated = true;
              break;
            }
          }

          if (isEOD && !terminated) {
            if (balance > peak) peak = balance;
            if (peak - balance >= maxDD) {
              ruins++;
              terminated = true;
            }
          } else if (isStatic && !terminated) {
            if (-balance >= maxDD) {
              ruins++;
              terminated = true;
            }
          }
        }
      }

      setSimResult({
        passRate: Math.round((passes / iterations) * 100),
        ruinRate: Math.round((ruins / iterations) * 100),
        expectedDays: passes > 0 ? Math.round(totalDaysPass / passes) : 0,
        medianProfit: target,
      });
      setIsSimulating(false);
    }, 350);
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
                                      {p.payout_split_pct ?? 90}% (100% 1st 10k)
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
                            <span style={{ fontSize: "10px", fontWeight: 800, padding: "2px 6px", borderRadius: "4px", background: "rgba(34, 197, 94, 0.15)", color: "var(--success)" }}>SCORE {p.trust_score ?? 90}/100</span>
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
                                <div style={{ fontSize: "14px", fontWeight: 900, color: "var(--success)" }}>{p.payout_split_pct ?? 90}% (100% 1st $10k)</div>
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
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--accent)", borderRadius: "var(--radius-xl)", padding: "24px", boxShadow: "0 12px 40px rgba(0, 240, 255, 0.15)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", borderBottom: "1px solid var(--border)", paddingBottom: "14px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <div style={{ width: "42px", height: "42px", borderRadius: "10px", background: "linear-gradient(135deg, var(--accent), #22c55e)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "22px", color: "#000", fontWeight: 900 }}>
                  🤖
                </div>
                <div>
                  <h2 style={{ fontSize: "18px", fontWeight: 900, margin: 0, color: "#fff", display: "flex", alignItems: "center", gap: "8px" }}>
                    UltraBot AI — Consultor Cuantitativo de Futuros CME
                    <span style={{ fontSize: "10px", fontWeight: 900, padding: "2px 8px", borderRadius: "999px", background: "rgba(34, 197, 94, 0.2)", color: "var(--success)", border: "1px solid var(--success)" }}>
                      ONLINE · BASE DE DATOS REAL
                    </span>
                  </h2>
                  <p style={{ margin: 0, fontSize: "11px", color: "var(--text-muted)" }}>
                    Pregunta sobre cualquier firma, política de bots, promociones del día, cálculo de coste de extracción o trampas de letra pequeña.
                  </p>
                </div>
              </div>

              <button
                onClick={() => setChatMessages([chatMessages[0]])}
                style={{ background: "var(--bg-2)", border: "1px solid var(--border)", color: "var(--text-muted)", padding: "6px 12px", borderRadius: "6px", fontSize: "11px", cursor: "pointer", fontWeight: 700 }}
              >
                Limpiar Conversación
              </button>
            </div>

            {/* ZONA DE MENSAJES */}
            <div style={{ height: "460px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "16px", paddingRight: "8px", marginBottom: "16px" }}>
              {chatMessages.map((msg) => (
                <div
                  key={msg.id}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: msg.role === "user" ? "flex-end" : "flex-start",
                  }}
                >
                  <div style={{ fontSize: "10px", color: "var(--text-muted)", marginBottom: "4px", padding: "0 4px" }}>
                    {msg.role === "user" ? "Tú" : "🤖 UltraBot AI"} · {msg.timestamp}
                  </div>

                  <div
                    style={{
                      maxWidth: "85%",
                      padding: "16px 20px",
                      borderRadius: msg.role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                      background: msg.role === "user" ? "linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(59, 130, 246, 0.2))" : "rgba(10, 16, 26, 0.85)",
                      border: msg.role === "user" ? "1px solid var(--accent)" : "1px solid var(--border)",
                      color: "#fff",
                      fontSize: "13px",
                      lineHeight: "1.6",
                      whiteSpace: "pre-wrap",
                      boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
                    }}
                  >
                    {msg.content}

                    {/* CUPONES ACTIVOS SUGERIDOS */}
                    {msg.active_coupons && msg.active_coupons.length > 0 && (
                      <div style={{ marginTop: "12px", paddingTop: "10px", borderTop: "1px solid var(--border)", display: "flex", flexWrap: "wrap", gap: "6px" }}>
                        {msg.active_coupons.map((c, cIdx) => (
                          <button
                            key={cIdx}
                            onClick={() => handleCopyCode(c.code)}
                            style={{
                              padding: "4px 8px",
                              borderRadius: "4px",
                              background: "rgba(99, 225, 180, 0.15)",
                              border: "1px solid var(--accent-dim)",
                              color: "var(--accent-bright)",
                              fontSize: "10px",
                              fontWeight: 800,
                              cursor: "pointer",
                            }}
                          >
                            🏷️ {c.firm}: {copiedCode === c.code ? "✓ Copiado" : `${c.code} (${c.discount})`}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* ACCIONES O PREGUNTAS SUGERIDAS */}
                  {msg.suggested_actions && msg.suggested_actions.length > 0 && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "8px", maxWidth: "85%" }}>
                      {msg.suggested_actions.map((act, aIdx) => (
                        <button
                          key={aIdx}
                          onClick={() => handleSendChatMessage(act)}
                          style={{
                            padding: "4px 10px",
                            borderRadius: "999px",
                            background: "rgba(255, 255, 255, 0.04)",
                            border: "1px solid var(--border)",
                            color: "var(--accent-bright)",
                            fontSize: "11px",
                            fontWeight: 700,
                            cursor: "pointer",
                            transition: "all 0.15s ease",
                          }}
                        >
                          💬 {act}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {isChatLoading && (
                <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--accent)", fontSize: "12px", fontWeight: 700 }}>
                  <span>⏳ UltraBot AI analizando base de datos cuantitativa...</span>
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* INPUT DE ENTRADA DEL CHAT */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendChatMessage();
              }}
              style={{ display: "flex", gap: "10px" }}
            >
              <input
                type="text"
                placeholder="Pregunta lo que sea sobre firmas de futuros (ej. ¿Qué firma me conviene si uso bots y tengo $60?...)"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={isChatLoading}
                style={{
                  flex: 1,
                  padding: "12px 16px",
                  background: "var(--bg-2)",
                  border: "1px solid var(--border-hover)",
                  borderRadius: "var(--radius-md)",
                  color: "#fff",
                  fontSize: "13px",
                  fontWeight: 600,
                  outline: "none",
                }}
              />
              <button
                type="submit"
                disabled={isChatLoading || !chatInput.trim()}
                style={{
                  padding: "12px 24px",
                  background: "var(--accent)",
                  color: "#06090e",
                  border: "none",
                  borderRadius: "var(--radius-md)",
                  fontSize: "13px",
                  fontWeight: 900,
                  cursor: isChatLoading || !chatInput.trim() ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
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
        {/* MÓDULO 5: ENCICLOPEDIA & WIKI                                             */}
        {/* ========================================================================= */}
        {activeModule === "ENCICLOPEDIA" && (
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-xl)", padding: "24px" }}>
            <h2 style={{ fontSize: "20px", fontWeight: 900, margin: "0 0 4px 0", color: "var(--accent-bright)" }}>
              📚 Enciclopedia Técnica de Firmas de Futuros CME
            </h2>
            <p style={{ margin: "0 0 20px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
              Fichas técnicas exhaustivas con microestructura, comisiones por contrato, escalado, plataformas y auditoría forense de letra pequeña.
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "240px 1fr", gap: "20px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px", background: "rgba(0,0,0,0.25)", padding: "10px", borderRadius: "var(--radius-md)", maxHeight: "550px", overflowY: "auto" }}>
                {[
                  { id: "topstep", name: "Topstep (Chicago)", founded: "2012" },
                  { id: "mffu", name: "MyFundedFutures (MFFU)", founded: "2023" },
                  { id: "tradeify", name: "Tradeify (Miami)", founded: "2024" },
                  { id: "apex", name: "Apex Trader Funding", founded: "2021" },
                  { id: "tradeday", name: "TradeDay (Chicago)", founded: "2020" },
                  { id: "takeprofit", name: "Take Profit Trader", founded: "2021" },
                  { id: "bulenox", name: "Bulenox", founded: "2022" },
                  { id: "fundednext", name: "FundedNext Futures", founded: "2024" },
                  { id: "blusky", name: "BluSky Trading (Static)", founded: "2022" },
                  { id: "ticktick", name: "TickTick Trader", founded: "2022" },
                  { id: "oneup", name: "OneUp Trader", founded: "2017" },
                  { id: "fasttrack", name: "Fast Track Trading", founded: "2024" },
                  { id: "uprofit", name: "UProfit Trader", founded: "2019" },
                  { id: "elitetrader", name: "Elite Trader Funding", founded: "2022" },
                  { id: "earn2trade", name: "Earn2Trade (Helios)", founded: "2016" },
                  { id: "leeloo", name: "Leeloo Trading", founded: "2019" },
                  { id: "lucid", name: "Lucid Trading", founded: "2025" },
                ].map((f) => (
                  <button
                    key={f.id}
                    onClick={() => setSelectedWikiFirm(f.id)}
                    style={{
                      textAlign: "left",
                      padding: "8px 12px",
                      borderRadius: "4px",
                      background: selectedWikiFirm === f.id ? "rgba(99, 225, 180, 0.15)" : "transparent",
                      border: selectedWikiFirm === f.id ? "1px solid var(--accent)" : "1px solid transparent",
                      color: selectedWikiFirm === f.id ? "var(--accent-bright)" : "var(--text-secondary)",
                      fontSize: "12px",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    <div>{f.name}</div>
                    <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>Fundada: {f.founded}</div>
                  </button>
                ))}
              </div>

              <div style={{ background: "rgba(0,0,0,0.2)", padding: "20px", borderRadius: "var(--radius-lg)", border: "1px solid var(--border)" }}>
                {selectedWikiFirm === "topstep" && (
                  <div>
                    <h3 style={{ fontSize: "18px", fontWeight: 900, color: "#fff", marginBottom: "4px" }}>🏛️ Topstep — Ficha Enciclopédica Oficial</h3>
                    <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "14px" }}>Fundada en 2012 en Chicago, IL. Firma #1 en solvencia institucional con plataforma TopstepX integrada con TradingView.</p>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px", marginBottom: "14px" }}>
                      <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>COMISIONES ALL-IN</div>
                        <div style={{ fontSize: "13px", fontWeight: 800 }}>Mini: ~$3.80 RT | Micro: ~$1.10 RT</div>
                      </div>
                      <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>CUOTA ACTIVACIÓN</div>
                        <div style={{ fontSize: "13px", fontWeight: 800, color: "var(--danger)" }}>$149 USD (Pass Fee)</div>
                      </div>
                      <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>PAGOS & RETIROS</div>
                        <div style={{ fontSize: "13px", fontWeight: 800, color: "var(--success)" }}>Diarios tras 5d ganadores de más de $200</div>
                      </div>
                    </div>
                    <div style={{ fontSize: "12px", lineHeight: "1.6", color: "var(--text-secondary)" }}>
                      <strong>Letra Pequeña Clave:</strong> Prohibido VPS comercial de data center público o proxies residenciales. Posiciones deben cerrarse a las 15:10 CT (16:10 ET). Trading de noticias permitido sin restricción.
                    </div>
                  </div>
                )}

                {selectedWikiFirm === "mffu" && (
                  <div>
                    <h3 style={{ fontSize: "18px", fontWeight: 900, color: "#fff", marginBottom: "4px" }}>🏛️ MyFundedFutures (MFFU) — Ficha Enciclopédica</h3>
                    <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "14px" }}>Fundada en 2023 en Austin, TX. Modelo Rapid pionero con $0 activación y retiros Día 1 On-Demand.</p>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px", marginBottom: "14px" }}>
                      <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>COMISIONES ALL-IN</div>
                        <div style={{ fontSize: "13px", fontWeight: 800 }}>Mini: ~$2.90 RT | Micro: ~$1.04 RT</div>
                      </div>
                      <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>CUOTA ACTIVACIÓN</div>
                        <div style={{ fontSize: "13px", fontWeight: 800, color: "var(--accent)" }}>$0 USD (Rapid Plan)</div>
                      </div>
                      <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>PAGOS & RETIROS</div>
                        <div style={{ fontSize: "13px", fontWeight: 800, color: "var(--success)" }}>Día 1 On-Demand en 12-24h</div>
                      </div>
                    </div>
                    <div style={{ fontSize: "12px", lineHeight: "1.6", color: "var(--text-secondary)" }}>
                      <strong>Letra Pequeña Clave:</strong> Trailing DD se congela en $50,100 una vez alcanzado el balance de $52,000. 100% de los primeros $10,000 netos. Permitidos bots en VPS sin restricciones.
                    </div>
                  </div>
                )}

                {selectedWikiFirm === "blusky" && (
                  <div>
                    <h3 style={{ fontSize: "18px", fontWeight: 900, color: "#fff", marginBottom: "4px" }}>🏛️ BluSky Trading — Ficha Enciclopédica</h3>
                    <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "14px" }}>Fundada en 2022 en Texas. Especialista en Drawdown Estático Puro (inmutable).</p>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px", marginBottom: "14px" }}>
                      <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>TIPO DRAWDOWN</div>
                        <div style={{ fontSize: "13px", fontWeight: 800, color: "var(--accent)" }}>100% Estático (Static)</div>
                      </div>
                      <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>CUOTA ACTIVACIÓN</div>
                        <div style={{ fontSize: "13px", fontWeight: 800, color: "var(--accent)" }}>$0 USD</div>
                      </div>
                      <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>RETIROS</div>
                        <div style={{ fontSize: "13px", fontWeight: 800, color: "var(--info)" }}>Semanales tras 8 días</div>
                      </div>
                    </div>
                    <div style={{ fontSize: "12px", lineHeight: "1.6", color: "var(--text-secondary)" }}>
                      <strong>Ventaja Matemática:</strong> El nivel de pérdida se fija en $48,000 en la cuenta 50K y jamás sube, permitiendo aguantar retrocesos normales de mercado sin arrastrar el stop de liquidación.
                    </div>
                  </div>
                )}

                {selectedWikiFirm !== "topstep" && selectedWikiFirm !== "mffu" && selectedWikiFirm !== "blusky" && (
                  <div>
                    <h3 style={{ fontSize: "18px", fontWeight: 900, color: "#fff", marginBottom: "4px" }}>🏛️ Ficha Técnica Oficial</h3>
                    <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "14px" }}>Información detallada verificada en tiempo real en la base de datos de Ultrarentable.</p>
                    <div style={{ padding: "12px", background: "rgba(0,0,0,0.3)", borderRadius: "4px", fontSize: "12px" }}>
                      Consulta los datos específicos de examen y fondeado en la pestaña del Catálogo Maestro o ejecuta la simulación Monte Carlo.
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MÓDULO 6: GUÍAS TÉCNICAS                                                  */}
        {/* ========================================================================= */}
        {activeModule === "GUIAS" && (
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-xl)", padding: "24px" }}>
            <h2 style={{ fontSize: "20px", fontWeight: 900, margin: "0 0 4px 0", color: "var(--accent-bright)" }}>
              🔧 Guías Técnicas de Conectividad e Infraestructura CME
            </h2>
            <p style={{ margin: "0 0 20px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
              Protocolos de configuración profesional para conectar plataformas de futuros, pasarelas de datos y trade copiers con menos de 5ms de latencia.
            </p>

            <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
              {[
                { id: "rithmic-nt8", label: "🔧 Guía 1: Rithmic R|Trader Pro ➔ NinjaTrader 8" },
                { id: "tradovate-tv", label: "📈 Guía 2: Tradovate ➔ TradingView Web/Desktop" },
                { id: "trade-copier", label: "👥 Guía 3: Setup de Trade Copier Multi-Cuenta" },
              ].map((g) => (
                <button
                  key={g.id}
                  onClick={() => setSelectedGuide(g.id)}
                  style={{
                    padding: "8px 16px",
                    borderRadius: "6px",
                    background: selectedGuide === g.id ? "rgba(99, 225, 180, 0.15)" : "var(--bg-2)",
                    border: selectedGuide === g.id ? "1px solid var(--accent)" : "1px solid var(--border)",
                    color: selectedGuide === g.id ? "var(--accent-bright)" : "var(--text-secondary)",
                    fontSize: "12px",
                    fontWeight: 800,
                    cursor: "pointer",
                  }}
                >
                  {g.label}
                </button>
              ))}
            </div>

            <div style={{ background: "rgba(0,0,0,0.25)", padding: "20px", borderRadius: "var(--radius-lg)", border: "1px solid var(--border)", fontSize: "12px", lineHeight: "1.6" }}>
              {selectedGuide === "rithmic-nt8" && (
                <div>
                  <h3 style={{ fontSize: "16px", fontWeight: 800, color: "#fff", marginBottom: "8px" }}>Protocolo de Conexión: R|Trader Pro ➔ NinjaTrader 8 (Multi-Provider)</h3>
                  <ol style={{ paddingLeft: "20px", display: "flex", flexDirection: "column", gap: "8px" }}>
                    <li><strong>Paso 1:</strong> Abre R|Trader Pro, ingresa tus credenciales, selecciona tu firma (Apex, Bulenox, UProfit) y activa <code>Allow Plug-in Brokerage</code> en el servidor <code>Chicago Area</code>.</li>
                    <li><strong>Paso 2:</strong> Acepta los dos acuerdos de datos CME Non-Professional en R|Trader Pro antes de abrir NinjaTrader.</li>
                    <li><strong>Paso 3:</strong> En NinjaTrader 8, ve a <code>Tools ➔ Options ➔ General</code> y marca <code>Multi-provider</code>.</li>
                    <li><strong>Paso 4:</strong> En <code>Connections ➔ configure</code>, añade <code>Rithmic for NinjaTrader 8</code> y marca <code>Connect via Plug-in</code>.</li>
                  </ol>
                </div>
              )}

              {selectedGuide === "tradovate-tv" && (
                <div>
                  <h3 style={{ fontSize: "16px", fontWeight: 800, color: "#fff", marginBottom: "8px" }}>Protocolo de Conexión: Tradovate ➔ TradingView</h3>
                  <ol style={{ paddingLeft: "20px", display: "flex", flexDirection: "column", gap: "8px" }}>
                    <li><strong>Paso 1:</strong> En <code>trader.tradovate.com</code>, ve a <code>Settings ➔ Add-Ons</code> y verifica que TradingView esté activo.</li>
                    <li><strong>Paso 2:</strong> En TradingView, abre el gráfico de futuros CME (ej. <code>CME_MINI:ES1!</code>, <code>CME_MINI:NQ1!</code>).</li>
                    <li><strong>Paso 3:</strong> Abre la pestaña inferior <code>Trading Panel</code>, selecciona <code>Tradovate</code> e ingresa tus credenciales en modo <code>Demo / Simulation</code>.</li>
                  </ol>
                </div>
              )}

              {selectedGuide === "trade-copier" && (
                <div>
                  <h3 style={{ fontSize: "16px", fontWeight: 800, color: "#fff", marginBottom: "8px" }}>Setup de Trade Copier Multi-Cuenta (Replicanto NT8)</h3>
                  <ol style={{ paddingLeft: "20px", display: "flex", flexDirection: "column", gap: "8px" }}>
                    <li><strong>Paso 1:</strong> Instala el Add-on de Replicanto en NinjaTrader 8.</li>
                    <li><strong>Paso 2:</strong> Define tu <code>Leader Account</code> (cuenta maestra) y añade las <code>Follower Accounts</code> esclavas.</li>
                    <li><strong>Paso 3:</strong> Si clonas órdenes de minis a cuentas de menor tamaño, habilita <code>Convert Mini to Micro (1:10)</code>.</li>
                    <li><strong>Paso 4:</strong> Activa siempre <code>Flatten followers on disconnect</code> para evitar posiciones desincronizadas huérfanas.</li>
                  </ol>
                </div>
              )}
            </div>
          </div>
        )}

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
                width: "420px",
                height: "560px",
                background: "rgba(10, 16, 26, 0.96)",
                backdropFilter: "blur(16px)",
                border: "1px solid var(--accent)",
                borderRadius: "16px",
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
                boxShadow: "0 20px 60px rgba(0,0,0,0.8)",
              }}
            >
              {/* CABECERA POPUP */}
              <div style={{ padding: "14px 16px", background: "rgba(0,0,0,0.4)", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
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
                      maxWidth: "90%",
                      padding: "10px 14px",
                      borderRadius: m.role === "user" ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
                      background: m.role === "user" ? "rgba(0, 240, 255, 0.2)" : "rgba(255, 255, 255, 0.05)",
                      border: m.role === "user" ? "1px solid var(--accent)" : "1px solid var(--border)",
                      fontSize: "12px",
                      lineHeight: "1.5",
                      color: "#fff",
                      whiteSpace: "pre-wrap",
                    }}
                  >
                    {m.content}
                  </div>
                ))}
                {isChatLoading && (
                  <div style={{ color: "var(--accent)", fontSize: "11px", fontWeight: 700 }}>
                    ⏳ UltraBot AI analizando...
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
