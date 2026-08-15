# 10. Extracción de la Serie de Trades — Verificación REAL

**Fecha:** 2026-08-09 · **Proyecto:** 01 Ultrarentable
**Método:** Probe real del MCP (8080), web UI (5050), databank en disco y sqx_client.py.
**Estado:** 🟡 **Incompleto por diseño del sistema** (abajo se explica).

---

## 1. Qué expone el MCP (verificado, no supuesto)

Probe con `SQXMCPClient` (ruta canónica del proyecto) lista **8 métodos**:

```
list_projects, list_databanks, list_strategies, get_strategy_stats,
run_project, stop_project, check_connection, initialize
```

**NO existe** ninguna tool de export de trades, ni de descarga/sync de datos, ni de
lectura del report de la GUI. El MCP es mínimo: orquesta proyectos y re-ejecuta el
estado en disco. Por tanto **la lista de trades individuales (PnL por operación,
timestamps de entrada/salida) NO es alcanzable vía MCP.** Confirmado también que la
llamada JSON-RPC bruta `tools/list` al `:8080/mcp` devuelve `400 Bad Request` (el
endpoint espera el handshake MCP completo/SSE), no es una vía alternativa.

## 2. Web UI (puerto 5050)

La web UI interactiva responde HTTP 200 en `/api`, `/swagger`, `/databank`,
`/status`. Es la **GUI real de SQX** (X-Builder). Los trades individuales se ven en
el **Report → Trades** de la GUI, que este endpoint web no expone como JSON/REST
directo. Rutas de databank responden 200 pero sirven la página, no la serie.

## 3. Databank en disco (estado real)

Proyecto `Ultra_Auto_Pilot` — databanks presentes:
`Results_20260809_032803`, `Last generation`, `Initial population`,
`Strategies to improve`, `Results`, `Existing portfolio`.
Los databanks de SQX guardan **resúmenes/estadísticas por estrategia**, no el log
de trades por operación. No hay fichero plano de trades exportable en `user/projects`.

## 4. Implicación para el pipeline de validación

- El **Monte Carlo / Walk-Forward Efficiency sobre serie de trades raw** (flip de
  orden, resampleo de PnL por trade) NO se puede construir solo con lo que el MCP
  entrega hoy.
- Lo que SQX **sí** expone por estrategia vía `get_strategy_stats`:
  métricas IS y OOS (NetProfit, PF, DD, trades, retornos) — suficiente para el
  **gate de calidad OOS, ranking por PF_OOS y conversión de DD a %** que exige la
  doctrina del proyecto (ya implementado en `sqx_router.py /rentable`).
- La única vía para la serie raw es **capturarla de la GUI** (Report → Trades) vía
  `import`/`xdotool` sobre Xvfb `:99`, o ampliar el plugin MCP de SQX con una tool
  de export. Ambas son trabajo futuro, no bloqueante para el gate OOS actual.

## 5. Conclusión

La extracción de la serie de trades no es alcanzable por MCP/web hoy → la validación
de balas se apoya en las métricas IS/OOS que SQX ya reporta por estrategia, más el
**2º motor independiente (NautilusTrader)** como revalidación OOS canónica, según
la doctrina del proyecto. La migración de 25 columnas de `04_pipeline_validacion_multimotor.md`
§6.3 se adapta: alimentar el 2º motor con los trades reconstruidos por SQX-CANDIDATE
vía su formulario (reglas), no con una exportación de trades raw que no existe.

---

*Documento de evidencia propia. Fuentes: probe real MCP `SQXMCPClient.list_tools()`,
`list_databanks()`, web UI 5050, inspección de `user/projects/*/project.cfx`.*
