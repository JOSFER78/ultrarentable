# AUDITORIA LECTURA FASE 0 — Documentos de Gobierno y Arquitectura (Agente A)

> **Proyecto:** Ultrarentable (Trading Cuantitativo Multi-Motor)  
> **Fecha de auditoría:** 2026-08-15  
> **Doctrina:** REAL-ONLY (verificado contra archivos en disco)  
> **Auditor:** Agente A (Docs de Gobierno)

---

## 1. Documentos Auditados y Rutas Verificadas en Disco

| Documento | Ruta en Disco | Tamaño | Propósito |
|---|---|---|---|
| Directiva Maestra | `AGENTS.md` | 2.796 bytes | Reglas de operación, bootstrap multiagente y principios REAL-ONLY |
| Estado Vivo | `ESTADO.md` | 4.479 bytes | Registro del estado de avance, cuellos de botella y próximos pasos |
| Marco Multiagente | `MULTIAGENTE_Y_SEGUIMIENTO.md` | 7.436 bytes | Protocolo de orquestación, squad y bitácoras |
| Guía General | `README.md` | 10.443 bytes | Manual de arquitectura, modos Ultra vs Fondeo y servicios |
| Plan Maestro SQX | `docs/Estado/auditoria/15_PLAN_MAESTRO_ESTABLE_GENERADOR.md` | 8.355 bytes | Plan consolidado de reconfiguración del generador anti-overfit |
| Auditoría Kamikaze | `plan_implementacion/AUDITORIA_CANDIDATOS_KAMIKAZE.md` | 12.384 bytes | Scorecard de calidad de las 24 estrategias históricas iniciales |
| Guía Experto SQX | `plan_implementacion/GUIA_EXPERTO_USAR_SQUANT.md` | 22.248 bytes | Parámetros nativos, variables de generación y optimización |
| Orquestación Motor | `plan_implementacion/ORQUESTACION_MOTOR_BUSQUEDA_20260809.md` | 2.570 bytes | Integración del controlador con SQX y base de datos |
| Bitácora Previa | `plan_implementacion/bitacora/2026-08-09.md` | 5.901 bytes | Registro de sesión previa (desbloqueo de SQX y backup) |
| Prop Firms Free Trial | `docs/Fondeo/prop_firms_cuenta_gratis.md` | 12.794 bytes | Análisis de 10 prop firms y reglas de evaluación |

---

## 2. Qué Pretende el Proyecto (Visión vs Realidad)

1. **La Promesa Original:**
   - Construir un generador y validador de estrategias algorítmicas con dos ramas:
     - **Modo Ultra:** Estrategias hiperagresivas ("kamikaze") buscando retornos extremos (≥1000%) en crypto perps (BingX).
     - **Modo Fondeo:** Estrategias estables con drawdown controlado y alta consistencia para superar exámenes en firmas de fondeo (Prop Firms) y cobrar payouts de $3.000–$4.000.
2. **La Realidad Cuantitativa Demostrada:**
   - **0 candidatos aprobados de 77 backtests** (95 estrategias generadas en total).
   - **Mejor candidato real:** `~2.24% IS retorno` en BTCUSDT H1.
   - **0 candidatos de miles de %**: La búsqueda kamikaze con fitness de retorno neto puro y sin cross-checks produjo puro sobreajuste (ejemplo: `Strategy 1.1.43` con PF IS 1.56 que colapsó a PF OOS 0.80).
   - **Incompatibilidad de modos:** Los modos ULTRA y FONDEO tienen objetivos matemáticos y restricciones de riesgo opuestos. Buscar 1000% en 5 meses de BTC es incompatible con las reglas de daily loss ≤ 2.5–3% y trailing drawdown ≤ 5–6% de las prop firms.

---

## 3. Discrepancias y Deudas de Documentación

1. **Handoff doc 16 inexistente:** `AGENTS.md` y prompts citaban `docs/Estado/auditoria/16_HANDOFF_ESTADO_EJECUCION.md`, pero en disco el análisis concluyó en `15_PLAN_MAESTRO_ESTABLE_GENERADOR.md` y la auditoría XML en `17_verificacion_xml.md`.
2. **Estatus de la Reconfiguración XML:** La reconfiguración se detuvo el 2026-08-09 con 6 de 10 cambios aplicados. Los 4 cambios pendientes (Ranking ReturnDDRatio, WFO use=true, filtro de sesión en params y PopulationSize) impidieron correr el generador fondeo corregido.
3. **Secretos en Docs:** `README.md` contenía mención de tokens de Obsidian que fueron desaconsejados por seguridad.

---

## 4. Conclusión del Agente A

El proyecto tiene una base documental y teórica sólida, pero arrastraba una contradicción de diseño: prometía "miles de %" mientras intentaba calificar para fondeo. La decisión obligatoria de priorizar **FONDEO-primero** y **congelar ULTRA** alinea la teoría con la viabilidad matemática real.
