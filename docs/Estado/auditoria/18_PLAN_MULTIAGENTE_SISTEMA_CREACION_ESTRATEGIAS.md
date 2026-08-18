# Fase 0 — Planificación e Inventario de Documentación

> **Proyecto:** 01 Ultrarentable · **Fecha:** 2026-08-17
> **Origen:** ejecutado por orquestador (no por subagentes — los subagentes fallaron por red)
> **Regla:** REAL-ONLY, nada hardcodeado, agnóstico a mercado/activo/timeframe

---

## 1. Estado real verificado en disco (17-ago-2026)

| Componente | Estado |
|---|---|
| SQX servicio | `activating` — en proceso de inicio; MCP no respondió en esta medición |
| Backup crítico `pre_reconfig_20260809_105641` | **NO existe en disco** |
| Backups disponibles | `backup_20260809_103910.tar.gz` (81 KB) · `project.cfx.pre_fase2_20260815_1633` (26 KB) |
| `project.cfx` actual | `/home/ubuntu/StrategyQuantX/user/projects/Ultra_Auto_Pilot/project.cfx` (26 338 bytes, contiene `Build-Task1.xml` + `config.xml`) |
| Config XML | 10 cambios planificados: **4 OK** (EvoInSamplePeriod 70, CrossChecks ON, spread=30, slippage=3), **3 parciales** (MC 20 sim, SPP MaxTests 100, Session Layer B), **3 pendientes** (Rankings ReturnDDRatio+conditions, WFO ON 5/20, PopulationSize 100/60) |
| Databanks UAP | `Results_robust_20260809`=0 · `Last generation`=92 (cacheadas) · `Results`=0 · `Initial population`=0 · `Strategies to improve`=0 |

---

## 2. Inventario de documentación (82 documentos catalogados)

### 2.1 Auditoría SQX (20 documentos)

| # | Documento | Fases | Resumen |
|---|---|---|---|
| 00 | `00_INDICE_Y_CABECERA.md` (4 948B, 67L) | F0,F1 | Índice de auditoría + diagnóstico cabecera: 5 errores principal |
| 01 | `01_matriz_causa_raiz.md` (4 562B, 96L) | F1 | Matriz de 5 errores con evidencia XML real |
| 02 | `02_configuracion_actual_sqx.md` (3 237B, 87L) | F1,F3 | Config actual extraída del XML: todos los parámetros reales |
| 03 | `03_diagnostico_plantilla_sqx_real.md` (13 983B, 257L) | F1,F3 | Diagnóstico profundo Build-Task1.xml: 5 errores causa raíz |
| 04 | `04_pipeline_validacion_multimotor.md` (33 988B, 723L) | F1,F2,F4 | Pipeline SQX→Nautilus, 5 etapas, scorecard 3 capas A/B/C, WFA 8 folds 62.5%, MC 10K, SPP ±15%, tolerancias Nautilus |
| 05 | `05_plantilla_sqx_perfiles_ab.md` (28 594B, 648L) | F1,F2,F4 | Plantillas completas Perfil A (Ultra) y B (Fondeo): fitness, building blocks, MM, sesión, filtros, checklist pre-run |
| 06 | `06_plan_accion_multiagente.md` (22 407B, 320L) | F0,F1,F2 | Plan 48-72h con 11 agentes A0-A10, dependencias, paralelización, cronograma, riesgos |
| 07 | `07_plan_control_gui_sqx.md` (3 810B, 65L) | F1,F3 | Plan control GUI SQX con computer_use |
| 08 | `08_auditoria_datos_sqx.md` (5 516B, 111L) | F1 | Auditoría datos SQX: BTCUSDT H1, SPY D1, sin M1 |
| 09 | `09_integracion_obsidian.md` (5 349B, 96L) | F1,F2 | Integración con Obsidian: conocimiento existente |
| 10 | `10_extraccion_serie_trades.md` (3 239B, 66L) | F1,F4 | Extracción serie de trades para validación |
| 11 | `11_analisis_viabilidad_datos.md` (8 909B, 135L) | F1,F2 | Viabilidad WFO con 3.840 barras: 75/25 split, 2-3 folds, trades OOS≥20, trades total≥60, PF_OOS≥1.20 |
| 12 | `12_analisis_reconfiguracion_xml.md` (24 715B, 506L) | F1,F3 | Los 10 cambios XML exactos con fragmentos reales de búsqueda/reemplazo |
| 13 | `13_especificacion_generador_ideal.md` (13 959B, 196L) | F1,F2 | Contrato generador ideal: definición de bala, gates duros, fitness A/B, cross-checks, pipeline SQX→Nautilus |
| 14 | `14_analisis_antioverfit.md` (10 313B, 161L) | F1,F2,F4 | Capa anti-overfit: IS/OOS 70/30, WFA, MC, SPP, 2º motor, umbrales 3 capas A/B/C, scorecard |
| 15 | `15_PLAN_MAESTRO_ESTABLE_GENERADOR.md` (8 183B, 130L) | F0,F1,F2,F3 | Plan maestro 2026-08-09: 5 fases con verificación, 10 cambios XML, riesgos, criterio de éxito |
| 17A | `17A_CAPACIDADES_MCP_SQX.md` (13 214B, 249L) | F1,F3 | Capacidades MCP: 6 tools, latencias 2-33ms, 7 proyectos, 22 databanks, limitaciones |
| 17B | `17B_SUPERFICIE_UI_SQX.md` (12 750B, 283L) | F1,F3 | Auditoría UI: 4 canales (MCP=OK, CFX-ZIP=OK, GUI xdotool=OK, CDP=no, Playwright 5050=no aplica) |
| 17C | `17C_PLAN_100_PORCIENTO_SQX.md` (12 330B, 180L) | F1,F2,F3 | Plan maestro SQX 2026-08-11: matriz capabilities, flujo 7 fases, roadmap P0/P1/P2 |
| 17 | `17_verificacion_xml.md` (18 660B, 450L) | F1,F3 | Auditoría XML: 4 aplicados, 3 parciales, 3 no aplicados; fragmentos exactos de búsqueda/reemplazo |

### 2.2 Laboratorio (12 documentos)

| # | Documento | Fases | Resumen |
|---|---|---|---|
| L04 | `04_STRATEGYQUANT_Y_ALTERNATIVAS.md` (1 520B, 56L) | F1,F2 | SQX como generador especializado vs alternativas; qué no reconstruir |
| L05 | `05_GESTION_DINAMICA_Y_PROTECCION.md` (1 526B, 49L) | F2,F4 | Ratchet adaptativo: hitos 2x/3x/5x, protección 50%/65%/75%, herramientas de gestión |
| LSE | `SEARCH_AND_EVOLUTION.md` (1 279B, 58L) | F1,F2,F3 | Pipeline búsqueda: seed→DSL→VectorBT→cánonico, selección kamikaze (log equity), operadores evolutivos, búsqueda por capas |
| LNAUT | `ESPECIFICACION_COMPLETA_NAUTILUSTRADER_ULTRARENTABLE.md` (11 296B, 380L) | F1,F2,F4 | Especificación NautilusTrader: 12 capas del sistema, stack recomendado, política kamikaze, factories de estrategias, gates de validación |
| LBACK | `CANONICAL_BACKTESTER.md` (1 356B, 49L) | F1,F4 | Contratos backtester canónico: secuencia evento/barra, políticas intrabar PESSIMISTIC/OPTIMISTIC/LOWER_TF_REPLAY, liquidación por exchange |
| LANTI | `ANTI_FALSE_RESULTS.md` (674B, 16L) | F1,F4 | Barreras contra falsos: look-ahead, warmup, invariantes contables, golden tests, comparación diferencial fast vs canónico |
| LDSL | `DSL_SPEC.md` (1 193B, 53L) | F2,F4 | DSL v0.1: gramática, operadores (AND/OR/NOT, GT/LT/CROSS), VALUE (PRICE/INDICATOR/ROLLING), límites técnicos |
| LIDSL | `DSL_IMPLEMENTATION_REPORT.md` (2 394B, 42L) | F2,F4 | Implementación DSL v1.0: Pydantic, IR 3 direcciones, 12/12 tests pasan, hash SHA-256, seguridad sin eval/exec |
| LARCH | `FINAL_ARCHITECTURE_ASSESSMENT.md` (1 800B, 45L) | F0,F2 | Valoración arquitectura: 2 motores necesarios, diversidad evolutiva, modelo liquidación por exchange |
| LCAMP | `CAMPAIGN_CONFIG.md` (676B, 36L) | F2,F3 | Configuración de campaña kamikaze: 5000 población, 100 generaciones, 0.65 mutación, selección kamikaze |
| LTEC | `TECHNOLOGY_DECISIONS.md` (501B, 17L) | F1,F2 | Decisiones tecnológicas del proyecto |
| LHTML | `informe_completo_nautilustrader_ultrarentable.html` (56 329B, 464L) | F1,F2 | Informe completo NautilusTrader (HTML) |

### 2.3 Fondeo (5 documentos)

| # | Documento | Fases | Resumen |
|---|---|---|---|
| FBASE | `BASE_DATOS_EMPRESAS_FONDEO_FUTUROS_2026-08-02.md` (53 606B, 1754L) | F1,F2,F4 | 34 firmas revisadas: Topstep/TradeDay/MFF/Apex/FundedNext/Tradeify/Bulenox, reglas de bots, coste real por $1K DD, fórmula coste completo, promociones, 1754 líneas |
| FINTER | `PROP_FIRMS_DATABASE_INTERACTIVE.md` (3 853B, 52L) | F1,F2 | Interfaz interactiva: cohorte 50K, métrica coste/$1K DD, selector estricto |
| FDEBATE | `DEBATE_MULTIAGENTE_NORMALIZACION_FONDEO.md` (3 998B, 50L) | F1,F2 | Debate 4 agentes: normalización métricas por $1000, corrección mezcla 50K/150K, fórmula coste real |
| FTC | `prop_firms_cuenta_gratis.md` (12 508B, 189L) | F1,F4 | Trials gratis: FundedNext 14d CFD, TradeDay 14d futuros (confirmar bots), ruta híbrida NinjaTrader→TradeDay→FundedNext/Apex |
| FDW | `DATA_WAREHOUSE_PROP_FIRMS_ARCHITECTURE.md` (6 393B, 177L) | F2,F5 | Arquitectura data warehouse para prop firms |

### 2.4 Investigación (14 documentos)

| # | Documento | Fases | Resumen |
|---|---|---|---|
| IMAIN | `informe_master_trading_bots_futuros.md` (14 712B, 644L) | F1,F2,F4 | Investigación bots: evidencia pública (Lucid $8900, Thraxx), middleware (TradersPost, PickMyTrade), prop firms, compliance |
| ICONS | `01_TRADING_BOTS_INVESTIGACION_CONSOLIDADA.md` (12 764B, 631L) | F1,F2,F4 | Investigación consolidada: prop firms, metodología DaviddTech, constraint engine, anti-baneo, middleware, filtros anti-overfitting |
| IINFO | `investigacion_info_trading_bots.md` (13 956B, 305L) | F1,F2 | Investigación info trading bots: prop firms, metodología, constraint engine, compliance |
| ICROS | `corroboracion_hechos_clave.md` (13 142B, 220L) | F1,F2,F4 | Corroboración 12 hechos clave: Lucid, Topstep VPS prohibido, TPT bots prohibido, FundedNext EAs, BingX 500x TradFi, Choppiness 61.8 |
| IPV | `PRODUCT_VISION.md` (1 448B, 48L) | F0,F2 | Visión del producto |
| IFUNC | `FUNCTIONAL_SPEC.md` (2 398B, 77L) | F2 | Especificación funcional |
| ITAR | `TARGET_ARCHITECTURE.md` (677B, 24L) | F2 | Arquitectura objetivo |
| IDATA | `DATA_CATALOG.md` (750B, 43L) | F3 | Catálogo de datos |
| IAGENT | `AGENT_SYSTEM.md` (896B, 36L) | F0,F2 | Sistema de agentes |
| IAPI | `API_SPEC.md` (621B, 31L) | F5 | Especificación API |
| IDEPL | `DEPLOYMENT.md` (565B, 30L) | F5 | Despliegue |
| IWEB | `WEB_MVP.md` (764B, 36L) | F2,F5 | MVP web |
| IACC | `ACCEPTANCE_TESTS.md` (851B, 31L) | F5 | Tests de aceptación |
| IMOD | `MODULE_BOUNDARIES.md` (630B, 38L) | F2 | Límites de módulos |

### 2.5 Archive (20 documentos)

| # | Documento | Fases | Resumen |
|---|---|---|---|
| AFAC | `PHASE_F_AUTONOMOUS_FACTORY_PLAN.md` (3 286B, 60L) | F2,F3,F5 | Plan fábrica autónoma: generación masiva, validación, despliegue |
| AFACREP | `PHASE_F_AUTONOMOUS_FACTORY_REPORT.md` (2 258B, 44L) | F3,F5 | Reporte fábrica autónoma: resultados |
| AFastE | `PHASE_E_FAST_ENGINE_PLAN.md` (2 937B, 54L) | F2,F3 | Plan fast engine: motor de backtest rápido para criba |
| AFastR | `PHASE_E_FAST_ENGINE_REPORT.md` (1 734B, 34L) | F3,F5 | Reporte fast engine: resultados y validación |
| ALEVER | `LEVERAGE_AUTOPILOT_REPORT.md` (976B, 15L) | F2,F4 | Reporte leverage autopilot: mecanismos apalancamiento automático |
| AAUTO | `AUTOPILOT_IMPLEMENTATION_REPORT.md` (1 701B, 35L) | F2,F4 | Reporte implementación autopiloto: estado y resultados |
| ADEC | `AUTOPILOT_DECISION_MODEL.md` (1 476B, 23L) | F2,F4 | Modelo de decisiones autopiloto: criterios y reglas |
| AAQUI | `ARQUITECTURA_FACTORY_AUTONOMA_BINGX.md` (10 383B, 341L) | F2,F5 | Arquitectura fábrica autónoma para BingX |
| ASPEC | `ESPECIFICACION_COMPLETA_BINGX_ULTRARENTABLE.md` (10 832B, 358L) | F1,F2,F3 | Especificación completa sistema ultrarentable para BingX |
| AREAL | `REAL_ONLY_START_HERE.md` (1 054B, 35L) | F0,F1 | Directrices REAL-ONLY para el proyecto |
| AGATE | `REAL_ONLY_ACCEPTANCE_GATE.md` (828B, 19L) | F1,F4 | Puerta de aceptación REAL-ONLY: criterios validación |
| AV51 | `V5_1_IMPLEMENTATION_REPORT.md` (1 213B, 16L) | F3,F5 | Reporte implementación V5.1 |
| AV51T | `V5_1_TEST_EVIDENCE.md` (1 524B, 37L) | F3,F5 | Evidencia de tests V5.1 |
| ASTAR | `START_HERE_AUTOPILOTO_TOTAL.md` (1 874B, 57L) | F0 | Punto de entrada autopiloto total |
| ACORR | `START_HERE_V5_1_CORRECTION.md` (360B, 12L) | F5 | Correcciones V5.1 |
| AV4 | `START_HERE_V4_REVIEW.md` (452B, 12L) | F0 | Revisión V4 |
| AV3 | `START_HERE_V3.md` (399B, 12L) | F0 | Punto de entrada V3 |
| ADATAC2 | `DATA_C2_COMPLETION_REPORT.md` (1 664B, 28L) | F3 | Reporte completación datos C2 |
| ACOMP | `V5_COMPILEALL_OUTPUT_AUDIT.txt` (0B, 1L) | F5 | Salida compilación V5 |
| APHAS2 | `PHASE_2_HISTORICAL_SOURCE_AUDIT.md` (2 439B, 43L) | F1,F3 | Auditoría fuente histórica Fase 2 |
| APHAS1 | `PHASE_1_UNIVERSE_SCANNER_REPORT.md` (3 063B, 64L) | F1,F3 | Reporte scanner universo Fase 1 |

### 2.6 Ultrarentable docs (8 documentos)

| # | Documento | Fases | Resumen |
|---|---|---|---|
| USPEC | `ESPECIFICACION_COMPLETA_BINGX_ULTRARENTABLE.md` (10 832B, 358L) | F1,F2,F3 | Especificación completa sistema ultrarentable para BingX |
| UEXEC | `bingx_ejecucion_real.md` (14 441B, 348L) | F3,F5 | Ejecución real en BingX — Informe de implementación |
| UVAL | `BINGX_VALIDATION_PLAN.md` (276B, 4L) | F3,F4 | Plan de validación para BingX |
| UNAUT | `BINGX_NAUTILUS_ADAPTER.md` (401B, 4L) | F1,F3,F4 | Adaptador Nautilus para BingX |
| UDATA | `BINGX_DATA_PIPELINE.md` (361B, 8L) | F3 | Pipeline de datos para BingX |
| UEXECMODEL | `BINGX_EXECUTION_MODEL.md` (478B, 10L) | F2,F5 | Modelo de ejecución para BingX |
| UCAMP | `BINGX_CAMPAIGN_CONFIG.md` (258B, 4L) | F2,F3 | Configuración de campaña para BingX |
| UAPI | `BINGX_API_ENDPOINTS.md` (676B, 17L) | F1,F5 | Endpoints de API de BingX |

### 2.7 Pruebas (2 documentos)

| # | Documento | Fases | Resumen |
|---|---|---|---|
| USTRESS | `INFORME_STRESS_TEST.md` (880B, 13L) | F3,F5 | Informe stress test de estrategias |
| UREAD | `README_EVIDENCIAS.md` (2 964B, 60L) | F3 | Lectura de evidencias de pruebas |

---

## 3. Planificación de agentes (matriz completa)

### 3.1 Fases y agentes

| Fase | Tiempo | Agentes | Paralelismo | Dependencias |
|---|---|---|---|---|
| **F0** Planificación | 4h | 0.1 Planificador, 0.2 Inventario | ✅ Full paralelo | Ninguna |
| **F1** Análisis Profundo | 12h | 1.1 Analista SQX, 1.2 Analista Métodos Ultra, 1.3 Analista Prop Firms, 1.4 Analista Validación | ✅ Full paralelo (4) | F0.2 |
| **F2** Diseño de Solución | 10h | 2.1 Diseñador Config Ultra, 2.2 Diseñador Config Fondeo, 2.3 Diseñador Edición/Reciclaje, 2.4 Diseñador Pipeline | ✅ Full paralelo | F1.1, F1.2, F1.3, F1.4 |
| **F3** Implementación y Ejecución | 16h | 3.1 Implementador Config SQX, 3.2 Ejecutor Búsqueda Ultra, 3.3 Ejecutor Búsqueda Fondeo, 3.4 Validador Independiente | 3.1 antes que 3.2/3.3; 3.4 después | F2.1, F2.2, F2.3, F2.4 |
| **F4** Sistema de Edición | 12h | 4.1 Implementador Reciclaje, 4.2 Implementador Edición, 4.3 Adaptador Fondeo | ✅ Full paralelo | F3.2, F3.3, F3.4 |
| **F5** Integración y Documentación | 8h | 5.1 Integrador, 5.2 Documentador, 5.3 Validador Final | ✅ Full paralelo | F4.1, F4.2, F4.3 |

**Total estimado: 62 horas** con ejecución secuencial por fase pero paralelismo interno.

### 3.2 Descripción de cada agente

#### Fase 0
- **0.1 Planificador** → Este documento. Define la estructura de agentes, dependencias, tiempos, riesgos.
- **0.2 Inventario** → Este documento (sección 2). Catálogo de 82 documentos con relevancia por fase y brechas.

#### Fase 1 — Análisis Profundo

- **1.1 Analista SQX:** Lee la documentación de SQX (auditoría 01-17, laboratorio 04, 17A, 17B, 17C) y produce un informe técnico de:
  - Capacidades reales de SQX para generación de estrategias
  - Parámetros críticos del generador (population, mutation, crossover, islands, etc.)
  - Cómo configurar SQX para objetivos ultra (miles de %, 500x)
  - Cómo configurar SQX para objetivos de fondeo (constraint de DD estricto)
  - Limitaciones y workarounds identificados en la documentación

- **1.2 Analista Métodos Ultra:** Investiga los métodos para alcanzar retornos extremos:
  - Técnicas de reciclaje automático de margen (compound, reinvestment)
  - Uso de apalancamiento y riesgo para multiplicadores extremos
  - Estrategias de protección y gestión dinámica (ratchet, trailing)
  - Cómo SQX puede implementar o facilitar estos métodos
  - Riesgos y mitigaciones del enfoque ultra

- **1.3 Analista Prop Firms:** Analiza los requisitos de las prop firms:
  - Qué activos operan típicamente (NQ, ES, CL, GC, SI, EURUSD, GBPUSD, etc.)
  - Reglas de riesgo por firma (DD diario, DD total, consistency, etc.)
  - Restricciones de bots/automatización por firma
  - Cómo adaptar SQX para cumplir estos requisitos
  - Estrategias específicas para aprobar evaluaciones

- **1.4 Analista Validación:** Define el protocolo de validación riguroso:
  - IS/OOS split adecuado para distintos escenarios
  - Walk-forward optimization (configuración, folds, criterios)
  - Monte Carlo (configuración, métodos, umbrales)
  - Cross-checks y validación con motor independiente
  - Criterios de aceptación para ultra vs fondeo

#### Fase 2 — Diseño de Solución

- **2.1 Diseñador Config Ultra:** Diseña la configuración SQX para ultra:
  - Fitness function que premie asimetría extrema (miles de %)
  - Configuración genética para exploración agresiva
  - Building blocks y componentes recomendados
  - Parámetros de Money Management para apalancamiento y compound
  - Cross-checks y validación para asegurar robustez
  - Cómo evitar curve-fit mientras se buscan extremos

- **2.2 Diseñador Config Fondeo:** Diseña la configuración SQX para fondeo:
  - Fitness function que optimice probabilidad de aprobar evaluación
  - Configuración de riesgo y DD control estricto
  - Building blocks conservadores
  - Parámetros de tamaño y riesgo
  - Filtros de sesión y régimen
  - Cómo adaptar para diferentes activos (futures, forex, indices, etc.)

- **2.3 Diseñador Edición/Reciclaje:** Diseña el sistema de edición y mejora:
  - Mecanismo de reciclaje automático de margen (compound, reinvestment)
  - Sistema de gestión dinámica (ratchet adaptativo, trailing de equity)
  - Cómo SQX puede implementar o interactuar con estos mecanismos
  - Reglas de activación y protección contra ruina

- **2.4 Diseñador Pipeline:** Diseña el pipeline integrado:
  - Flujos de trabajo para ultra y fondeo
  - Cómo migrar de estrategia ultra a adaptada para fondeo
  - Sistema de versionado y tracking de estrategias
  - Protocolos de despliegue y monitoreo

#### Fase 3 — Implementación y Ejecución

- **3.1 Implementador Config SQX:** Implementa las configuraciones en SQX:
  - Modificar project.cfx con parámetros para ultra (respaldando antes)
  - Modificar project.cfx con parámetros para fondeo (respaldando antes)
  - Verificar cambios aplicados correctamente
  - Configurar databanks para resultados

- **3.2 Ejecutor Búsqueda Ultra:** Ejecuta SQX con configuración ultra:
  - Lanzar ejecución con MCP
  - Monitorear progreso
  - Recolectar resultados cuando estén disponibles
  - Aplicar filtros iniciales de calidad

- **3.3 Ejecutor Búsqueda Fondeo:** Ejecuta SQX con configuración fondeo:
  - Lanzar ejecución con MCP
  - Monitorear progreso
  - Recolectar resultados cuando estén disponibles
  - Aplicar filtros de calidad específicos de fondeo

- **3.4 Validador Independiente:** Valida las mejores estrategias:
  - Re-backtest con datos OOS
  - Análisis estadístico
  - Verificación de robustez (Monte Carlo, WFO, sensibilidad)
  - Comparación entre motores si disponible

#### Fase 4 — Sistema de Edición

- **4.1 Implementador Reciclaje:** Implementa el sistema de reciclaje de margen:
  - Reglas de activación (hitos de equity)
  - Gestión de riesgo (protección de capital, trailing)
  - Cálculo de posición y sizing
  - Integración con SQX

- **4.2 Implementador Edición:** Implementa herramientas de edición:
  - Procedimientos para exportar/importar estrategias SQX
  - Modificación de parámetros clave
  - Sistema de versionado y tracking
  - Re-evaluación de estrategias editadas

- **4.3 Adaptador Fondeo:** Adapta estrategias ultra para fondeo:
  - Reducción de riesgo y DD
  - Ajuste de sizing y apalancamiento
  - Filtros de sesión y régimen
  - Validación en activos típicos de prop firms

#### Fase 5 — Integración

- **5.1 Integrador:** Integra todos los componentes en un sistema cohesivo:
  - Flujos de trabajo automatizados
  - Sistema de seguimiento de estrategias
  - Protocolos de despliegue y monitoreo
  - Alertas y notificaciones

- **5.2 Documentador:** Documenta todo el conocimiento:
  - Guía de uso de SQX para ultra
  - Guía de uso de SQX para fondeo
  - Mejores prácticas y lecciones aprendidas
  - Protocolos de validación recomendados

- **5.3 Validador Final:** Valida que el sistema cumple sus objetivos:
  - Verificar estrategias ultra con retornos extremos verificados
  - Verificar estrategias de fondeo con cumplimiento de requisitos
  - Evaluar calidad del sistema de edición y reciclaje
  - Identificar áreas de mejora

---

## 4. Brechas identificadas (prioridad)

| # | Brecha | Prioridad | Responsable |
|---|---|---|---|
| B1 | Métodos ultra 500x: no hay documento técnico que explique el mecanismo de reciclaje de margen o compound automático para SQX | ALTA | F2.3 |
| B2 | Constraint engine prop firms: no hay engine que traduzca reglas de prop firm a restricciones SQX | ALTA | F2.2 |
| B3 | NautilusTrader como 2º motor: especificado pero NO implementado | ALTA | F3.4 (o F4) |
| B4 | Sistema de edición SQX: SQX no exporta código fuente, no hay procedimiento documentado | MEDIA | F4.2 |
| B5 | Fast engine vs motor canónico: FAST_APPROXIMATE desbloqueado pero Nautilus no implementado | MEDIA | F3.4, F5.1 |
| B6 | Datos históricos ampliados: solo 3.840 barras H1 BTC + SPY D1 33 años | MEDIA | F3.x (si se autoriza) |
| B7 | Portfolio y correlación: no hay sistema para combinar estrategias | BAJA | F4.x |
| B8 | Micro-live y shadow: documentado pero no implementado, requiere confirmación explícita del usuario | BAJA | F5.x |

---

## 5. Riesgos por fase

| Fase | Riesgo | Mitigación |
|---|---|---|
| F0 | Subagentes fallan por red | Orquestador ejecuta F0 directamente (hecho) |
| F1 | Documentación extensa (82 docs, ~250KB) puede saturar contexto | Cada agente se enfoca en subset específico de docs relevantes a su área |
| F2 | Diseños pueden ser inconsistentes entre agentes | Coordinación vía documentos de especificación compartidos; revisión cruzada F1→F2 |
| F3 | SQX puede no producir estrategias con retornos extremos en datos limitados (5.2 meses) | Aceptar resultados parciales; iterar configuración; considerar ampliar datos si se autoriza |
| F3 | Configuración XML incorrecta puede romper SQX | Backup antes de cada cambio; verificación post-cambio; reversibilidad |
| F4 | SQX no permite edición directa de estrategias generadas | Usar CFX mutation para modificar parámetros; exportar a formato intermedio para edición externa |
| F5 | Sistema puede quedar fragmentado | Integración temprana; puntos de integración definidos en F2/F3 |

---

## 6. Puntos de integración entre fases

1. **F1 → F2:** Los 4 analistas de F1 alimentan a los 4 diseñadores de F2 con conocimiento clave. Los diseñadores deben leer los informes de los analistas antes de diseñar.
2. **F2 → F3:** Los diseños de F2 son implementados por F3.1; los diseños de búsqueda son ejecutados por F3.2/F3.3. Los validadores de F3.4 usan los protocolos diseñados en F2.1/F2.2/F2.4.
3. **F3 → F4:** Los resultados de F3.2/F3.3 son analizados por F3.4 y sirven de input a F4.1/F4.2/F4.3. Las estrategias validadas son las que se editan y adaptan.
4. **F4 → F5:** Los sistemas implementados en F4 son integrados por F5.1 y documentados por F5.2; F5.3 valida todo el sistema completo.

---

## 7. Reglas del sistema (no negociables)

1. **REAL-ONLY:** Cada métrica, resultado, y claim debe provenir de ejecución real verificable, no de suposiciones o simulaciones conceptuales.
2. **NADA HARCODEDO:** El sistema debe ser agnóstico a mercado, activo, timeframe, y estrategia. Todas estas son variables de configuración.
3. **SQX como generador principal:** StrategyQuant X es la herramienta central para generar estrategias. El sistema de edición y validación complementa SQX, no lo reemplaza.
4. **Validación independiente obligatoria:** Ninguna estrategia se considera válida sin verificación con métodos independientes (OOS, WFO, MC, motor alternativo).
5. **Separación ultra vs fondeo:** Los flujos de trabajo para estrategias ultra (miles de %, 500x) y de fondeo (DD controlado, cumplimiento de reglas) son separados y no deben mezclarse sin cuidado.
6. **Protección contra ruina:** Cualquier sistema de reciclaje de margen o compound debe incluir protecciones explícitas contra ruina (trailing, drawdown limits, kill switches).
7. **Adaptabilidad a activos:** El sistema debe poder trabajar con cualquier activo que SQX soporte o que tenga datos disponibles, incluyendo los activos típicos de prop firms (NQ, ES, CL, GC, SI, EURUSD, GBPUSD, etc.).

---

## 8. Próximos pasos

1. ✅ Fase 0 completada (este documento)
2. **Fase 1:** Despachar los 4 agentes de análisis en paralelo (F1.1, F1.2, F1.3, F1.4)
3. Revisar resultados de Fase 1 y ajustar Fase 2 si es necesario
4. Despachar Fase 2 con los 4 diseñadores
5. Continuar secuencialmente por F3, F4, F5

**¿Avanzar con Fase 1 ahora?**
