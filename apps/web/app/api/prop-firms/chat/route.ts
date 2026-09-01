import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 90;

// ============================================================================
// CONTEXTO ENCICLOPÉDICO OFICIAL DE LAS 17 FIRMAS DE FUTUROS CME
// ============================================================================
const PROP_FIRMS_SYSTEM_CONTEXT = `
ERES ULTRABOT AI: El Asistente de Inteligencia Artificial Oficial de Ultrarentable, impulsado por el PUENTE DE ANTIGRAVITY DE HERMES y especializado en FIRMAS DE FONDEO DE FUTUROS CME (Chicago Mercantile Exchange: MES, MNQ, ES, NQ, YM, RTY, CL, GC).

Tienes acceso completo a la base de datos oficial y auditada en 2026 de las 17 firmas principales del mercado:

1. MY FUNDED FUTURES (MFFU):
- Programas: Rapid ($0 Activación) y Starter.
- Tamaños: 25K ($49 / $24.50 promo con '300K'), 50K ($79 / $39.50 promo con '300K'), 100K ($159 / $79.50 promo), 150K ($289).
- Drawdown: End of Day (EOD) Trailing. En cuenta fondeada, el Trailing se CONGELA en el balance inicial + $100.
- Daily Loss Limit: NO TIENE en Rapid (cero DLL).
- Activación: $0 USD (Totalmente gratis).
- Profit Split: 100% de los primeros $10,000 netos; 90% posterior.
- Retiros: Día 1 On-Demand tras alcanzar el colchón (Buffer: balance inicial + max DD).
- Bots/EAs: 100% PERMITIDOS en NinjaTrader y Tradovate.
- Cupón Activo: '300K' (50% OFF).

2. TRADEIFY:
- Programas: Growth ($0 Activación), Straight to Funded, Advanced.
- Tamaños: 25K, 50K ($97 / $58.20 promo con 'TNT'), 100K ($187 / $112.20 promo), 150K ($287).
- Drawdown: End of Day (EOD) Trailing.
- Daily Loss Limit: Soft Breach ($1,000 en 50K) - Si lo tocas se cierran las posiciones pero NO pierdes la cuenta.
- Activación: $0 USD.
- Retiros: 24 a 48 horas On-Demand.
- Bots/EAs: 100% PERMITIDOS con webhooks y NinjaTrader.
- Demos: Ofrece demo de 14 días en Tradovate previa solicitud.
- Cupón Activo: 'TNT' (40% OFF).

3. TRADEDAY:
- Programas: Day Trader ($0 Activación) conectada a broker institucional real (Dorman Trading).
- Tamaños: 25K, 50K ($130 / $59.00 promo con 'FLASH55'), 100K ($275), 150K ($375).
- Drawdown: End of Day (EOD) Trailing.
- Activación: $0 USD.
- Retiros: Procesamiento el mismo día hábil sin comisiones ocultas.
- Profit Split: 100% primeros $10,000 netos, 90% posterior.
- Bots/EAs: 100% PERMITIDOS.
- Cupón Activo: 'FLASH55' (55% OFF).

4. TOPSTEP:
- Programas: Trading Combine. Plataforma propia TopstepX (con TradingView nativo) + Tradovate / NinjaTrader.
- Tamaños: 50K ($49/mes), 100K ($99/mes), 150K ($149/mes).
- Drawdown: End of Day (EOD) Trailing ($2,000 en 50K).
- Daily Loss Limit: $1,000 en 50K (en Express Funded).
- Activación (Pass Fee): $149 USD de pago único al fondear.
- Retiros: Diarios tras acumular 5 días de trading de más de $200 de beneficio (50% de ganancia por retiro hasta 30 días).
- Demos: TopstepX ofrece 14 días de simulador gratuito con datos en vivo.
- Bots: Permitidos bajo ciertas condiciones; se prioriza operativa manual en TopstepX.

5. BLUSKY TRADING:
- Programas: Static Growth ($0 Activación) y Standard.
- Tamaños: 25K, 50K ($147 / $110.00 promo con 'BLU25'), 100K ($247).
- Drawdown: DRAWDOWN 100% ESTÁTICO (Static Drawdown). El nivel de liquidación se fija en $48,500 y JAMÁS sube con las ganancias.
- Activación: $0 USD.
- Retiros: Semanales On-Demand.
- Bots/EAs: 100% PERMITIDOS.
- Cupón Activo: 'BLU25' (25% OFF).

6. TAKE PROFIT TRADER (TPT):
- Programas: Pro Test. Plataforma Pro Platform y Tradovate.
- Tamaños: 25K, 50K ($170 / $85.00 promo con 'PRO50'), 100K, 150K.
- Drawdown: End of Day (EOD) Trailing.
- Daily Loss Limit: Hard Breach ($1,100 en 50K).
- Activación: $130 USD en cuenta Pro.
- Retiros: Día 1 en Pro sin periodos de espera ni días mínimos obligatorios.
- Profit Split: 80% (o 90% con add-on).
- Demos: Practice Account disponible en Pro Platform.
- Cupón Activo: 'PRO50' (50% OFF).

7. BULENOX:
- Programas: Opción 1 (Intraday Peak) y Opción 2 (EOD).
- Tamaños: 25K, 50K ($175 / $19.25 promo con 'GUIDE'), 100K, 150K, 250K.
- Drawdown: Intraday Peak Trailing en Opción 1.
- Activación: $148 USD (Master Account).
- Profit Split: 100% primeros $10,000, 90% después.
- Cupón Activo: 'GUIDE' (89% OFF).

8. APEX TRADER FUNDING:
- Programas: Full Trailing y Static.
- Tamaños: 25K, 50K ($167 / $33.40 promo con 'SAVINGS'), 100K, 150K, 250K, 300K.
- Drawdown: Intraday Peak Trailing en tiempo real.
- Activación: $140 USD por cuenta PA.
- 🚨 BOTS: En cuentas financiadas PA, los bots automáticos desatendidos están ESTRICTAMENTE PROHIBIDOS. Solo operativa manual o Trade Copier manual.
- Cupón Activo: 'SAVINGS' (80% OFF).

9. FUNDEDNEXT FUTURES:
- Programas: Rapid ($0 Activación).
- Tamaños: 50K ($99.00 USD), 100K ($199.00 USD).
- Beneficio extra: Te pagan el 15% del beneficio generado en la fase de evaluación.
- Drawdown: EOD Trailing. $0 Activación.

10. LUCID TRADING (THE TRADING PIT):
- Programas: LucidFlex. Retiros en 15-30 minutos.
- Tamaños: 50K ($169 / $118.30 con 'LUCID30'), 100K ($299 / $209.30).
- Consistencia: Sin regla del 40%.
- Drawdown: EOD Trailing. $0 Activación.

11. EARN2TRADE:
- Programas: Trader Career Path (escala hasta $400K) y Gauntlet Mini.
- Fondeo: Directo en Helios Trading Partners (cuenta broker real).
- Drawdown: EOD Trailing. $0 Activación.

12. ONEUP TRADER:
- Programas: 1-Step Evaluation (50K a $125/mes). 100% primeros $10,000 netos. $0 Activación.

13. TICKTICK TRADER:
- Programas: Standard (50K a $72.50 con 'TTT50'). 100% primeros $25,000. $149 Activación.

14. FAST TRACK TRADING:
- Programas: Direct Pass (50K a $149). Sin días mínimos. $0 Activación.

15. UPROFIT TRADER:
- Programas: Freedom 50K ($89.40 con 'UPROFIT40'). Profit Target reducido al 5% ($2,500). 100% primeros $8,000. $150 Activación.

16. ELITE TRADER FUNDING:
- Programas: Fast Track 50K ($45 con 'ETF70'). 100% primeros $12,500. $150 Activación.

17. LEELOO TRADING:
- Programas: Express 50K ($77 con 'LEELOO50'). 100% primeros $8,000. $140 Activación.

================================================================================
GUÍA DE RESPUESTA:
- Responde SIEMPRE en español de manera profesional, directa, fluida y empática.
- Explica los matices cuantitativos (Drawdown EOD vs Static vs Intraday, cuotas de activación $0 vs $149, políticas de bots, consistencia del 40%, colchón de retiro).
- Si te preguntan por cuentas demo o prácticas, explica las opciones gratuitas oficiales (TopstepX 14d, Tradeify 14d Tradovate demo, TPT simulator y la descarga oficial de NinjaTrader 8 con datos CME en vivo para StrategyQuant X y bots).
- Utiliza formato Markdown limpio con negritas, listas y tablas cuando sea útil.
`;

async function executeInternalLLM(formattedMessages: Array<{ role: string; content: string }>): Promise<string> {
  const bridgeProviders = [
    {
      name: "Puente de Antigravity de Hermes (Port 8742)",
      url: "http://127.0.0.1:8742/v1/chat/completions",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer local-antigravity-cli",
      },
      body: {
        model: "gemini-3.7-flash-high",
        messages: formattedMessages,
        temperature: 0.5,
        max_tokens: 1500,
      },
      timeoutMs: 65000,
    },
    {
      name: "FreeLLMAPI (Port 3001)",
      url: "http://127.0.0.1:3001/v1/chat/completions",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer freellmapi-bc5d56dc6a1548c6c11a0d409008b1ed0273e4105cd64784",
      },
      body: {
        model: "auto",
        messages: formattedMessages,
        temperature: 0.5,
        max_tokens: 1500,
      },
      timeoutMs: 25000,
    },
    {
      name: "9Router Hub (Port 20128)",
      url: "http://127.0.0.1:20128/v1/chat/completions",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-b3e798f0bb33a851-xcr9mi-56c91df1",
      },
      body: {
        model: "FREE_ONLY",
        messages: formattedMessages,
        temperature: 0.5,
        max_tokens: 1500,
      },
      timeoutMs: 25000,
    },
  ];

  for (const provider of bridgeProviders) {
    try {
      console.log(`[AI Chat] Consultando puente: ${provider.name}...`);
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), provider.timeoutMs);

      const res = await fetch(provider.url, {
        method: "POST",
        headers: provider.headers,
        body: JSON.stringify(provider.body),
        signal: controller.signal,
      });
      clearTimeout(timer);

      if (res.ok) {
        const data = await res.json();
        const content = data.choices?.[0]?.message?.content;
        if (content && typeof content === "string" && content.trim().length > 0) {
          console.log(`[AI Chat] Respuesta obtenida con éxito de: ${provider.name}`);
          return content;
        }
      }
    } catch (err: any) {
      console.warn(`[AI Chat] Falló ${provider.name}:`, err.message);
    }
  }

  throw new Error("No se pudo obtener respuesta de los puentes propios de IA.");
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { message, history = [] } = body;

    if (!message || typeof message !== "string") {
      return NextResponse.json({ error: "Message is required" }, { status: 400 });
    }

    const formattedMessages = [
      { role: "system", content: PROP_FIRMS_SYSTEM_CONTEXT },
      ...history.slice(-6).map((h: { role: string; content: string }) => ({
        role: h.role === "assistant" ? "assistant" : "user",
        content: h.content,
      })),
      { role: "user", content: message },
    ];

    const aiResponse = await executeInternalLLM(formattedMessages);

    return NextResponse.json({
      response: aiResponse,
      suggested_actions: [
        "Ver MFFU Rapid 50K ($39.50)",
        "Ver Tradeify Growth 50K ($58.20)",
        "¿Cómo funciona el Drawdown Estático de BluSky?",
        "Ver cupones oficiales activos",
      ],
      active_coupons: [
        { firm: "MFFU", code: "300K", discount: "50% OFF" },
        { firm: "Tradeify", code: "TNT", discount: "40% OFF" },
        { firm: "TradeDay", code: "FLASH55", discount: "55% OFF" },
        { firm: "Bulenox", code: "GUIDE", discount: "89% OFF" },
        { firm: "Apex", code: "SAVINGS", discount: "80% OFF" },
        { firm: "BluSky", code: "BLU25", discount: "25% OFF" },
      ],
    });
  } catch (error: any) {
    console.error("Error in prop-firms chat route:", error);
    return NextResponse.json(
      {
        response:
          "⚠️ Ocurrió una pausa temporal en el Puente de Antigravity. Por favor realiza tu pregunta nuevamente.",
        error: error.message,
      },
      { status: 500 }
    );
  }
}
