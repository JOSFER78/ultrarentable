# ULTRARENTABLE — SISTEMA DE GOBERNANZA DE VERSIONES, CERTIFICACIÓN Y CONTROL (v5.4.0)

> **ESTADO DEL SISTEMA**: `v5.4.0` (CURRENT_RECOMMENDED / CERTIFICADA)  
> **FECHA DE REVISIÓN**: 24 de Agosto de 2026  
> **DOCTRINA**: ZERO-MOCKS · REAL-ONLY · PROVENANCE-LOCKED · MERKLE-ROOT CERTIFIED  

---

## 1. INTRODUCCIÓN Y POLÍTICA DE VERSIONADO

El sistema cuantitativo **Ultrarentable** opera bajo un régimen formal e inmutable de control de versiones basado en la gobernanza estricta **Single Source of Truth (SSOT)**.

### 1.1 Regla de Progresión Decimal
- El versionado evoluciona de forma estrictamente incremental decimal a decimal (`v5.0.0` $\rightarrow$ `v5.1.0` $\rightarrow$ `v5.2.0` $\rightarrow$ `v5.3.0` $\rightarrow$ `v5.4.0`).
- Cada salto de versión queda indexado criptográficamente con:
  1. **Huella SHA-256 del Código Fuente**: Calculada deterministamente sobre los 7 directorios operativos (`contracts/`, `services/validation/`, `services/backtest/`, `services/strategy_core/`, `services/discovery/`, `services/ultra/`, `services/data/`).
  2. **Metadata de Git Inmutable**: Commit hash completo, commit corto (7 caracteres), autor, mensaje de commit, fecha UTC y rama de control.
  3. **Registro SQLite WAL & Firebase**: Inserción inmutable en la tabla `engine_version_logs` y `version_manifest.json`.

---

## 2. ARQUITECTURA DE CERTIFICACIÓN GLOBAL (11 QUALITY GATES)

### 2.1 Revalidación Obligatoria por Versión
Ninguna estrategia puede figurar como `APPROVED` o `CERTIFIED` sin haber sido sometida al pipeline formal de 11 Quality Gates bajo la versión activa del motor (`v5.4.0`).

$$\text{Candidata Legacy} \xrightarrow[\text{EventBacktestEngine}]{\text{Datasets Normalizados SHA-256}} \text{11 Quality Gates} \begin{cases} \text{100\% PASS} \longrightarrow \textbf{v5.4.0 APPROVED \& CERTIFIED} \\ \text{FAIL} \longrightarrow \textbf{RESEARCH LAB (Vista 4)} \end{cases}$$

### 2.2 Requisitos de Aprobación Estricta:
1. **Gate 1 (Estructura & Sintaxis)**: AST canónico y reglas operativas válidas.
2. **Gate 2 (Backtest con Costes Reales)**: Slippage y comisiones aplicadas según el activo (`CANONICAL_COST_REGISTRY`). Profit Factor OOS $\ge 1.20$.
3. **Gate 3 (Blind Holdout OOS 20%)**: Retención mínima del 50% frente al periodo In-Sample.
4. **Gate 4 (Estrés 3x Slippage)**: Rendimiento positivo y no degradación terminal ante fricción extrema.
5. **Gate 5 (Monte Carlo Geométrico)**: 0.0% probabilidad de ruina en 1,000 iteraciones con remuestreo de retornos fraccionales.
6. **Gate 6 (Prop Firm & CME Risk Limits)**: Max Drawdown $\le 4.5\%$ en ruta FONDEO, Max Drawdown $\le 85\%$ en ruta ULTRA (sin quiebra ni margin call).
7. **Gate 7 (Diversificación & No Dependencia de Outliers)**: Ningún trade individual aporta $>35\%$ del profit total.
8. **Gate 8 (Walk-Forward Efficiency WFE)**: Eficiencia temporal multiventana $\ge 50\%$.
9. **Gate 9 (Estabilidad de Parámetros)**: Meseta de rentabilidad robusta sin overfitting.
10. **Gate 10 (Reconciliación NautilusTrader)**: Validación trade-a-trade event-driven.
11. **Gate 11 (Certificado Merkle Root)**: Emisión de hash SHA-256 inmutable vinculado a la estrategia, dataset y huella del motor.

---

## 3. POLÍTICA DE SEGREGACIÓN ESTRICTA: VISTAS 5 Y 6

### 3.1 Vista 5: Estrategias Aprobadas (`/estrategias/5-estrategias-aprobadas` & `/gates`)
- **Regla Suprema**: En esta vista **SOLO** se muestran estrategias que cuenten con certificación 100% aprobada (`status === 'APPROVED'`, `is_certified === 1` y `engine_version === '5.4.0'`).
- **Cero Mutaciones en Pantalla**: Cualquier estrategia que se encuentre en incubación, reprogramación, fallo de compuertas o margin call es **estrictamente excluida** de la Vista 5 y enviada al backend / Research Lab (Vista 4).

### 3.2 Vista 6: Meta-Estrategia & Cartera Ensamblada (`/estrategias/6-meta-estrategia` & `/portfolio`)
- **Regla Suprema**: Los ensambles de cartera (Equal Risk Contribution ERC, Markowitz, Max Sharpe) se construyen **exclusivamente** a partir del subconjunto de estrategias certificadas de la Vista 5.
- **Aislamiento Total**: Queda prohibido ensamblar carteras con estrategias en investigación o pendientes de re-entrenamiento.

### 3.3 Vista 4: Panel Investigador Semántico & Research Lab (`/estrategias/4-panel-investigador`)
- Es el entorno exclusivo de backend donde residen las estrategias en proceso de mutación, autopsia de fallos (`LearningStore`), optimización paramétrica por microestructura y experimentos 24/7.
- Toda estrategia que no pasa el filtro de producción vive aquí hasta que mute y sea revalidada.

---

## 4. MATRIZ DE DISTRIBUCIÓN DE ESTRATEGIAS (v5.4.0)

| Estado de la Estrategia | Cantidad | Ubicación en Frontend / Backend | Visibilidad en Vistas 5 y 6 |
| :--- | :---: | :--- | :---: |
| **APPROVED & CERTIFIED** | **6** | Vista 5 (Aprobadas) & Vista 6 (Cartera) | **VISIBLE (100% PASS)** |
| **INCUBADORA_REPROGRAMACION** | **70** | Vista 4 (Research Lab) / SQLite WAL | **OCULTO (0% Visibilidad)** |
| **RECHAZADA_MARGIN_CALL** | **103** | Vista 4 (Failure Autopsy) / LearningStore | **OCULTO (0% Visibilidad)** |
| **IN_RESEARCH_MUTATION** | **28** | Vista 4 (ContinuousResearchDaemon) | **OCULTO (0% Visibilidad)** |
| **REJECTED** | **42** | Vista 4 (Failure Knowledge Database) | **OCULTO (0% Visibilidad)** |
| **INVESTIGACION_BTC** | **9** | Vista 4 (Specialized BTC Squeeze Lab) | **OCULTO (0% Visibilidad)** |
| **TOTAL CATALOGADO** | **258** | Motor Cuantitativo v5.4.0 | — |

---

## 5. SINCRONIZACIÓN DE BADGES EN FRONTEND NEXT.JS

1. **Header Superior (`apps/web/components/layout/Header.tsx`)**:
   - Badge Verde Dinámico: `v5.4.0` (proveniente de `useEngineVersion.ts` vía `/api/v1/versions`).
   - Badge Azul Git: `git:<commit_short>` conectado a la historia de Git.
2. **Menú Lateral (`apps/web/components/layout/Sidebar.tsx`)**:
   - Subtítulo de Marca: `QUANT LAB V5.4 (24/7 AUTO)`.
3. **Portada General (`apps/web/app/estrategias/page.tsx`)**:
   - Badge Central: `SSOT v5.4.0`.
   - Navegación directa a las 6 fases del pipeline.
