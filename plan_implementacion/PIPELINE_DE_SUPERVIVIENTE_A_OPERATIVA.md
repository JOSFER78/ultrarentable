# PIPELINE DE SUPERVIVIENTE A OPERATIVA (Fase 5)

> **Proyecto:** Ultrarentable · **Fecha:** 2026-08-15  
> **Doctrina:** REAL-ONLY · **Prioridad:** FONDEO-PRIMERO

---

## 1. Árbol de Decisiones: De Candidata Aprobada en SQX a Orden en Mercado

```mermaid
flowchart TD
    A["1. SQX Generación & Filtrado Interno (10 Cambios CFX)"] --> B["2. Scorecard Fondeo Canónico (5 Gates)"]
    B -->|Falla algún gate| Reject["Descarte Definitivo (Sin ajustes kamikaze)"]
    B -->|Pasa 5 gates (ej. Strategy 1.0.54)| C["3. Validación Adversarial en Python (Fast Engine)"]
    
    C --> D{"¿Pasa Stress Test de Slippage y Comisiones?"}
    D -->|No| Reject
    D -->|Sí| E["4. Exportación y Preparación de Ejecución"]
    
    E --> F1["Ruta BingX (DSL / REST API)"]
    E --> F2["Ruta Futuros CME (NinjaTrader / Tradovate)"]
    
    F1 --> G["5. Paper Trading en Vivo (7 días VPS)"]
    F2 --> G
    
    G --> H{"¿Desviación Live vs Backtest < 15%?"}
    H -->|No| Review["Revisión de Latencia / Slippage"]
    H -->|Sí| I["6. Despliegue en Cuenta de Evaluación con KILL-SWITCH"]
```

---

## 2. Protocolo de Control de Riesgo y Kill-Switch de Emergencia

Para proteger la cuenta de evaluación de prop firm (o el capital asignado) contra anomalías de mercado o fallos técnicos, se establecen 4 niveles de salvaguarda automatizada:

| Nivel de Protección | Condición de Activación | Acción Automática Inmediata |
|---|---|---|
| **Kill-Switch 1: Pérdida Diaria (DLL)** | Pérdida en el día alcanza **-$1.000 USD (2.0%)** | Cierre de posiciones abiertas a mercado, cancelación de órdenes pendientes y bloqueo de nuevas órdenes hasta las 00:00 UTC. |
| **Kill-Switch 2: Racha de Pérdidas** | **3 stops seguidos** en una misma sesión | Pausa obligatoria de 4 horas; reevaluación del régimen de volatilidad. |
| **Kill-Switch 3: Drawdown Trailing** | Equity retrocede **-$1.750 USD (3.5%)** desde el pico | Reducción del tamaño de posición al 50% (o parada total si es cuenta 50K). |
| **Kill-Switch 4: Latencia / Desconexión** | Sin heartbeat del broker o API > **5 segundos** | Intento de cierre de emergencia vía REST o fallback a stop-loss hard en broker. |

---

## 3. Plan de Despliegue para la Primera Estrategia (`Strategy 1.0.54`)

1. **Paso 1 — Registro en BD:**
   - Registrar `Strategy 1.0.54` en `ultrarentable.sqlite3` (`strategies` y `backtests`) con sus métricas verificadas (PF IS 1.38, PF OOS 1.75, 29 trades OOS).
2. **Paso 2 — Validación en Motor Python:**
   - Correr la validación adversarial con `quality_gates.py` y `ledger.py` verificando que soporta 5 pips de spread y 3 pips de slippage.
3. **Paso 3 — Fase Paper Trading:**
   - Activar el servicio de ejecución en modo simulación para verificar generación de señales en tiempo real coincidente con el gráfico H1.
4. **Paso 4 — Despliegue en Fondeo:**
   - Configuración en la plataforma de la prop firm con sizing estricto de 1 microcontrato (MES/MNQ) y riesgo fijado en $200 por trade.
