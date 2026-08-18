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

## 3. 🚀 Modos de Operación Cuantitativa

| RUTA | OBJETIVO | APALANCAMIENTO | GESTIÓN DE RIESGO |
| :--- | :--- | :---: | :--- |
| **🔥 ULTRA (BingX Perps)** | Hiperescalado exponencial (+5,000% a +25,000% / año) | **100x ➔ 500x** (Adaptativo) | 95% reinversión de margen flotante + Pyramiding asimétrico |
| **🛡️ FONDEO (CME Futures)** | Reto en $\le 5$ días + Cobros en cuenta fondeada | **1x a 10x** (Sin sobreapalancamiento) | Trailing Drawdown estricto $\le 4\%$ + Consistencia obligatoria |

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
