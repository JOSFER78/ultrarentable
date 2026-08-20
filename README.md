# 🎯 Ultrarentable — Laboratorio Cuantitativo de Estrategias (BingX + Fondeo CME)

> **Fuente Única de Verdad y Guía de Entrada al Proyecto.**
> Todos los servicios corren 24/7 en el VPS Linux. 
> La carpeta `docs/` es la **bóveda central de datos, investigación cuantitativa, auditorías y especificaciones de Obsidian**.

---

## 1. 📂 Estructura Limpia del Proyecto

El repositorio ha sido purgado de copias temporales y archivos obsoletos, quedando estructurado de forma modular y estricta:

```text
01 Ultrarentable/
├── apps/
│   └── web/                     # Frontend Next.js 16 (Command Center & Explorador 5 Gates)
├── services/
│   ├── api/                     # Backend FastAPI, Rutas REST, Motor DSL y Sistema de Auditoría
│   │   └── tests/               # Suite canónica de tests unitarios y de integración (127+ tests)
│   ├── sqx_bridge/              # Cliente y conexión MCP con StrategyQuant X
│   └── background_searcher.py   # Daemon autónomo de descubrimiento 24/7
├── docs/                        # 📚 FUENTE CENTRAL DE DATOS, INVESTIGACIÓN Y OBSIDIAN
│   ├── Investigacion/           # Catálogos cuantitativos, papers y arquitectura objetivo
│   ├── Laboratorio/             # Protocolos anti-falsos resultados, DSL y gestión de riesgo
│   ├── Ultrarentable/           # Especificaciones BingX USDⓢ-M, apalancamiento y mark price
│   ├── Fondeo/                  # Reglas de prop firms CME (Topstep, Apex, Bulenox, FTMO)
│   └── Estado/                  # Auditorías, planes maestros y seguimiento de ejecución
├── data/
│   ├── normalized/              # Datasets históricos normalizados (ETH, SOL, BTC)
│   └── artifacts/               # Scorecards y artefactos de backtest verificados
├── .agents/                     # Directivas maestras y guardarraíles automáticos para agentes IA
├── pyproject.toml               # Configuración del paquete y dependencias Python
└── package.json                 # Configuración del workspace Node.js / Next.js
```

---

## 2. 📚 La Carpeta `docs/` (Investigación y Fuente de Datos)

La carpeta [`docs/`](docs/) es el **cerebro teórico y cuantitativo** del proyecto. Se utiliza como:
1. **Espejo y puente de Obsidian:** Contiene las notas vivas y marcos conceptuales de trading.
2. **Especificaciones de Ejecución Real:** Parámetros de liquidación, comisiones y APIs de BingX y de Prop Firms de futuros CME.
3. **Protocolos Anti-Sobreajuste:** Requisitos de validación ciega (Out-of-Sample, Purged Cross-Validation, Monte Carlo Noise Injection).

---

## 3. 🚀 ESPECIFICACIÓN MAESTRA: ULTRA VS FONDEO (V1.05)

> 📖 **Documento Canónico Inmutable**: Consulta la especificación exhaustiva en [`SPEC_MASTER_ULTRA_VS_FONDEO.md`](SPEC_MASTER_ULTRA_VS_FONDEO.md).

| Dimensión | Ruta ULTRA (Hiper-Rentable Asimétrico) | Ruta FONDEO (Prop Firms / Apex / Topstep) |
| :--- | :--- | :--- |
| **Capital Inicial Base** | **$\$1.000\text{ USD}$** (Subcuenta Bala Sacrificable) | **$\$50.000\text{ USD}$** (Cuenta Institucional) |
| **Riesgo Base por Trade** | **$7.5\%$** de la Equidad Disponible ($5.0\% - 10.0\%$) | **$0.5\% - 1.0\%$** ($\$250 - \$500\text{ USD}$) |
| **Sizing & Compounding** | **Interés Compuesto Dinámico (Equity Compounding)** | **Lotes Fijos / Contratos CME (1 o 2 contratos)** |
| **Piramidación** | **1 a 3 tramos en ganancia $\ge +1.5R$ (Stop en BE)** | **Prohibida (Exposición Lineal Fija)** |
| **Drawdown Permitido** | **Hasta $80.0\%$** (Quiebra de bala en $85\% - 100\%$) | **Máximo $4.0\% - 4.5\%$** (Límite estricto Prop Firm) |
| **Mecanismo de Bóveda** | **Ratchet Vault**: 50% de ganancia a Bóveda tras $+200\%$ | No aplica (Administrado por Prop Firm) |
| **Universo de Activos** | **23 Activos Globales (112 datasets)**: BTC, ETH, SOL, SUI, DOGE, AVAX, BNB, LINK, XRP, ADA, DOT, NEAR, APT, MATIC, PEPE, NQ, ES, YM, RTY, GC, SI, CL, EURUSD. | **Futuros Regulados CME & Forex Spot**: NQ, ES, YM, RTY, GC, CL, 6E, EURUSD. |
| **Validación en Gates** | Retornos porcentuales fraccionales $r_t$, Monte Carlo geométrico | Retornos aditivos en dólares fijos nominales |

---

## 4. 🖥️ Servicios y Monitorización (VPS 24/7)

| SERVICIO | PUERTO | ACCESO | COMANDO DE ESTADO |
| :--- | :---: | :--- | :--- |
| **Frontend Next.js** | `3000` | `http://localhost:3000` | `systemctl --user status ultrarentable-web` |
| **Backend FastAPI** | `8000` | `http://localhost:8000` | `systemctl --user status ultrarentable-api` |
| **StrategyQuant X MCP** | `8081 / 5050` | `http://localhost:8081/mcp` | `systemctl --user status strategyquantx` |

---

## 5. 🛡️ Doctrina REAL-ONLY

- **Cero Mocks / Cero Datos Sintéticos:** Prohibido inventar métricas, resultados o números aleatorios.
- **Invariantes Contables:** Comisiones, slippage y tasas de funding siempre computadas de forma realista.
- **Tests Canónicos:** Toda verificación de código se ejecuta con `.venv/bin/pytest services/api/tests/`.
