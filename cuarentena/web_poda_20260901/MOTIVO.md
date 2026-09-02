# MOTIVO — poda de rutas fuera de misión FONDEO (2026-09-01)

> Ejecutado por AG-11 (Web — poda y reparaciones), paso 1 del plan de obra del expediente
> `orchestration/reviews/investigacion_I5_web.md`. Verificación previa al movimiento: `grep`
> de `from ['"].../<ruta>/` sobre todo `apps/web` — **cero importadores de código** (`import`)
> apuntando a estas rutas desde fuera de sí mismas. Solo existían `href` de navegación
> (Sidebar, Header, y 3 páginas supervivientes), que se han corregido tras el movimiento
> (ver `orchestration/results/AG-11_web_poda_2026-09-01.md`, sección T1).
>
> Nunca se usó `rm`. Todo el contenido vive íntegro bajo `apps/web/...` dentro de esta carpeta,
> con su ruta original preservada, y el hash de cada fichero en `MANIFEST.sha256`.

## Por qué se retira cada ruta

Ninguna de estas 16 rutas es exigida por la misión FONDEO actual (catálogo · gates · fondeo ·
plan · shell/login). Todas pertenecen al peso muerto medido en la investigación I5 (~12.500 LOC,
42% del código de `apps/web`).

| Ruta | Motivo específico |
| :--- | :--- |
| `trading-desk/` (7 ficheros: page, layout, posiciones, riesgo, auditoria, configuracion, estrategias) | Mesa de ejecución CME duplicada — `/fondeo` ya cubre la Mesa Fondeo & Terminal para la misión actual. Sin importadores de código. |
| `research/` | Panel investigador semántico, no forma parte del pipeline FONDEO (catálogo → gates → certificación). |
| `research-lab/` | Trials evolutivos de investigación; mismo motivo que `research/`, ruta hermana. |
| `ejecucion/` | Capa de ejecución en vivo genérica; sin datos reales verificados en esta fase, fuera de alcance FONDEO. |
| `tradesfera/` | Dossier de 18 módulos de contenido educativo/psicotrading; no es producto operativo. |
| `bifurcacion/` | Página de bifurcación FONDEO/ULTRA anterior al shell actual; el Sidebar y `/` ya cubren esa navegación. |
| `proveedores/` | Conectores API/MCP; catálogo de proveedores no crítico para certificar y fondear estrategias hoy. |
| `portfolio/` | Portfolio Studio de meta-estrategias (paridad de riesgo); depende de meta-portafolios que hoy no son el foco (catálogo/gates/fondeo lo son). Contenía además el badge `v5.4.0` hardcodeado (mentira de versión), que desaparece con la poda. |
| `robots/` | Seguimiento de bots desplegados; sin bots desplegados verificables aún, tabla vacía de facto. |
| `nautilus/` | Panel dedicado a NautilusTrader; el detalle vive ya en `/gates/gate-11-nautilus-event`, que se conserva. |
| `backtest/` | Motor de backtest físico como página propia; duplica funcionalidad de `/gates` y del `MotorBacktestView.tsx` ya muerto. |
| `strategyquant/` | Puente SQX headless como página dedicada; la extracción SQX se gestiona vía API/cola de minería, no vía esta UI. |
| `leaderboard/` | Ranking de estrategias; redundante con `/gates` (certificadas) y `/estrategias` (catálogo canónico). |
| `campaigns/` | Campañas de minería; se gestionan por `scripts/cola_mineria.py` (doctrina: NO usar pipelines de discovery directos desde la UI). |
| `seguimiento/` | Telemetría de operación duplicada de `/sistema`, que se conserva. |
| `data/` | Datasets normalizados como página dedicada; sin consumidor claro en la misión FONDEO actual. |

## Componente adicional

| Fichero | Motivo |
| :--- | :--- |
| `components/MotorBacktestView.tsx` (458 LOC) | Medido con **cero importadores** en todo `apps/web` (`grep -rn "MotorBacktestView"` solo encuentra su propia definición). La spec de estrategias (`docs/18_STRATEGIES_PAGE_SPEC.md`) prohíbe expresamente reintroducirlo. Se retira en vez de dejarlo como código muerto que invite a reengancharlo. |

## Lo que NO se tocó

- `apps/web/app/ultra/` — mandato explícito de Emilio: ULTRA no se poda ni se esconde nunca.
  Se le añadió un banner "EN CONSTRUCCIÓN" (ver T1 del informe), pero la ruta sigue viva y
  accesible, y el Sidebar la mantiene atenuada al final.
- `apps/web/app/strategies/` (nótese, sin "e": *strategies*, distinto de `app/estrategias/`) —
  no estaba en la lista de rutas a podar del contrato AG-11 y no se investigó su uso; se deja
  intacta para no exceder el mandato. Ver "LO QUE NO PUDE" en el informe.
- `apps/web/lib/strategyPhases.ts` — fichero de datos con **cero importadores**, casi con
  certeza código muerto igual que `MotorBacktestView.tsx`, pero no estaba nombrado en el
  contrato de poda (que enumera rutas de `app/` + ese componente específico). No se movió a
  cuarentena por prudencia de alcance; solo se corrigió su badge `v5.4.0` hardcodeado (T3).


---

## REVERSIÓN PARCIAL — 2026-09-02 (mandato de Emilio)

Emilio pidió expresamente recuperar dos de las 16 rutas retiradas:

| Ruta | Estado | Motivo de la vuelta |
| :--- | :--- | :--- |
| `trading-desk/` (7 ficheros) | **RESTAURADA** en `apps/web/app/trading-desk/` | "aunque ahora nos dedicamos solo a la estrategia, en un futuro hará falta trading desk". |
| `tradesfera/` | **RESTAURADA** en `apps/web/app/tradesfera/` | Contiene el tratado M01-M16 y, en M08, la comparativa de prop firms de futuros CME que Emilio quiere a mano. |

Los 8 ficheros se copiaron con su hash comprobado contra `MANIFEST.sha256` de esta carpeta
(coincidencia exacta antes de mover) y después se re-tematizaron a la paleta gris de
`docs/19_UI_STYLE_SPEC.md`, igual que el resto de la web. **Las copias de cuarentena no se
borran** (regla "nunca `rm`"): siguen aquí como constancia del estado en que se retiraron.

Las otras 14 rutas siguen en cuarentena y no se han tocado.
