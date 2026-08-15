# AUDITORIA LECTURA FASE 0 — Gap Fondeo vs Laboratorio Actual (Agente D)

> **Proyecto:** Ultrarentable (Trading Cuantitativo Multi-Motor)  
> **Fecha de auditoría:** 2026-08-15  
> **Doctrina:** REAL-ONLY (contrastado entre código/datos reales y especificaciones de evaluación)  
> **Auditor:** Agente D (Gap Fondeo vs Laboratorio)

---

## 1. Comparativa Dimensional: Laboratorio Actual vs Examen de Fondeo

| Dimensión | Laboratorio Actual en Repo | Requisito Típico de Prop Firm (50K Combine / Evaluation) | Brecha (Gap) / Impacto |
|---|---|---|---|
| **Instrumento / Mercado** | BingX Perps Crypto (`BTC-USDT`, `ETH-USDT`) | Futuros Regulados CME (`ES`, `NQ`, `MES`, `MNQ`) o CFDs multi-activo | 🔴 **Crítico:** Las firmas de futuros operan en CME; los perps de BingX no son aceptados en combines de futuros. |
| **Horario de Operación** | Continuo 24/7 sin cierre de sesión | Sesiones de futuros (CME RTH 09:30–16:00 EST / cierre diario obligatorio 17:00 EST) | 🔴 **Crítico:** No se pueden dejar posiciones abiertas durante el corte diario de CME ni fines de semana. |
| **Límite de Pérdida Diaria (DLL)** | Inexistente (solo margen y liquidación por contrato) | Estricto: **2.0% – 3.0%** ($1.000 – $1.500 en cuenta de $50.000) | 🔴 **Crítico:** Un solo día de DD de 4% quiebra la cuenta de evaluación. |
| **Drawdown Máximo / Trailing** | Techo de capital o stop de backtest genérico | **4.0% – 6.0%** Trailing intraday o EOD ($2.000 – $3.000 en 50K) | 🔴 **Crítico:** El trailing DD sigue el equity máximo punto a punto; no tolera retrocesos profundos tras ganancias. |
| **Regla de Consistencia** | Ninguna (un solo trade de +30% calificaba en modo kamikaze) | **30% – 50%**: Ningún día puede representar más del 30–50% de la ganancia total | 🔴 **Crítico:** Requiere ganancias distribuidas y repetibles, penalizando trades aislados de "lotería". |
| **Objetivo de Beneficio (Profit Target)** | >1000% (búsqueda kamikaze irreal) | **5.0% – 6.0%** ($3.000 en cuenta de $50.000) | 🟢 **Favorable:** El objetivo de ganancia es mucho más modesto y alcanzable que la quimera de 1000%. |
| **Tamaño de Posición y Riesgo** | Apalancamiento variable 1x–500x | 1–2 microcontratos (MES/MNQ) con riesgo de **0.5% por trade** ($250 max) | 🔴 **Crítico:** Requiere sizing fijo por volatilidad en ticks/puntos, no margen dinámico crypto. |
| **Pila de Ejecución** | API REST BingX / Fast Engine Python | NinjaTrader 8, Tradovate, Rithmic, TopstepX | 🟡 **Media:** SQX genera el código/lógica; la ejecución final se traslada a la plataforma del broker de la firma. |

---

## 2. Hallazgos Cuantitativos sobre los Datos Actuales (3.840 barras H1 BTC)

1. **Limitación Muestral:**
   - 3.840 barras H1 representan únicamente **5,2 meses** de histórico.
   - En 5,2 meses a temporalidad H1, una estrategia razonable genera entre **40 y 70 trades totales**.
   - En una partición OOS del 25% (Fase final de validación), esto produce apenas **10 a 18 trades OOS**, en el límite mínimo de validez estadística.
2. **Imposibilidad del Perfil Kamikaze:**
   - Intentar forzar 1000% de retorno en 5 meses con 40 trades exige un apalancamiento letal que viola instantáneamente la regla de DLL del 2.5% de cualquier prop firm.
3. **Viabilidad del Perfil Fondeo:**
   - Para un objetivo de $3.000 (6%) con max DD de $2.000 (4%), se requiere una estrategia con:
     - **Profit Factor OOS ≥ 1.25 – 1.40**
     - **Win Rate ≥ 45% – 55%** (con ratio R:R ≥ 1.2:1)
     - **Trades totales ≥ 50** (OOS ≥ 20)
     - **Riesgo por operación ≤ 0.5% del balance**.

---

## 3. Conclusión y Recomendación del Agente D

Para cumplir el objetivo de cobrar payouts reales de $3.000–$4.000 en cuentas fondeadas:
1. **Inmediato (Laboratorio):** Reconfigurar SQX con filtros de **FONDEO ESTRICTO** (Fitness = `ReturnDDRatio`, WFO activo, penalización severa de DD > 4%, sin ranking Net Profit).
2. **Transición de Mercado (Fase 4):** Reconocer que la evaluación real se cobrará sobre futuros (MES/MNQ en Topstep/Apex/TradeDay) y preparar el catálogo de reglas de fondeo como único criterio de aprobación.
