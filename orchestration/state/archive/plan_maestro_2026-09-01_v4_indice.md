# PLAN MAESTRO v4 — DE LA MALEZA A LOS MILES DE % (índice por bloques)

> **Sustituye a v3** (`archive/plan_maestro_2026-08-31_v3_motor_primero.md`). El texto íntegro de
> la v4 monolítica está en `archive/plan_maestro_2026-08-31_v4_monolitico.md`.
> **Desde 2026-08-31 el plan vive por BLOQUES** en `plan/bloques/`: un fichero por fase, con
> cabecera YAML (`id`, `estado`, `depende_de`, `desbloquea`, `verificacion_global`, `actualizado`)
> para editarlos, controlarlos y mejorarlos individualmente, y para que la web (F09) los renderice
> sin duplicar estados a mano. **La fuente de verdad de cada fase es su fichero de bloque.**
> **Ejecutor: Hermes (Orquestador).** Antigravity queda fuera del camino crítico (decisión del
> usuario 2026-08-31). Decisiones selladas: `DOCTRINA_ORQUESTADOR.md §14 y §15`.

---

## MANDATO ACTIVO (2026-09-01) — SOLO FONDEO

> **El 100 % del trabajo va a FONDEO y a las META-ESTRATEGIAS DE FONDEO.** Orden literal de
> Emilio: *"debes adaptar todo a de momento solo buscar estrategias fondeo y fondeo meta. DEBES
> DEJAR EN PARA FUTURO ULTRA"*.
>
> **ULTRA y META-ULTRA quedan APARCADOS, no abandonados.** Las fases F05 (envolvente ULTRA) y F06
> (router de meta-estrategias ULTRA) conservan su contenido íntegro y llevan `aparcado: true` en
> su cabecera. Su estado completo —lo hecho y lo que faltaba— está congelado en
> `state/PUNTO_GUARDADO_ULTRA.md`. Se retoman cuando FONDEO tenga estrategias certificadas.
>
> La tesis de la envolvente de balas que se explica arriba **sigue siendo válida y sellada**: es
> el camino a los miles de % de ULTRA. Simplemente no es el trabajo de ahora.

---

## LA TESIS DEL PLAN (leer esto antes que las fases)

**Los miles de % no salen de encontrar una señal de entrada mágica.** No existe. Salen de esto:

```
       edge real y robusto          envolvente de balas          resultado
   (PF 1,3-1,6, verificado)   ×   (pirámide + reciclaje +   =   convexidad
    repetible, no espectacular      apalancamiento aislado)      asimétrica
```

Una estrategia con PF 1,4 y 30 % anual es aburrida. Esa misma estrategia, ejecutada con balas
sacrificables de 1R que piramidan sobre las ganadoras, reciclan el capital cosechado y toleran
80 % de DD flotante, produce colas derechas de tres cifras. **La convexidad es una propiedad de
la gestión de capital, no de la señal.**

De ahí el orden del plan, que es innegociable: primero **limpiar**, después **backtest realista**,
después **descubrir edges robustos** en volumen, después **doparlos con inteligencia**, y solo
entonces **la envolvente ULTRA**. En paralelo desde el descubrimiento, **FONDEO**.

**Lo que hoy hay en el catálogo NO sirve de materia prima** (hallazgo 01). Certificadas vigentes: **0**.

---

## ESTADO DE LOS BLOQUES

| Bloque | Fase | Estado | Depende de | Fichero |
| :--- | :--- | :--- | :--- | :--- |
| F00 | Limpieza del código | **EN_CURSO** (web: 16 rutas duplicadas a cuarentena; detectados 9 módulos homónimos vivos y DOS pipelines de validación con umbrales distintos) | — | `plan/bloques/F00_limpieza.md` |
| F01 | Saneamiento del catálogo | **HECHO** (0 supervivientes de 728) | F00 | `plan/bloques/F01_censo_catalogo.md` |
| F02 | Motor de backtest realista | **PARCIAL** (motor **5.17.0**; 2.3 HECHO: reglas prop sobre equity flotante en 5.15.0; comisión de forex corregida en 5.16.0; las tres releases con identidad 15/15) | F00 | `plan/bloques/F02_motor_realista.md` |
| F03 | Campaña de descubrimiento masiva | **EN_CURSO** (4h/1h y 15m barridas: 0 certif.; motor 5.17.0 con 6 arquetipos EVENTO — 5.14.0 + ORB/VWAP_REVERSION intradía; E2 ES 5m/15m HECHA 02-09 con 5.18.0: 840/840 muertas en IS, AGOTADA con matiz SESSION_MOMENTUM; bug comisión MES→motor 5.19.0 y E2c pendientes) | F01, F02 | `plan/bloques/F03_campana_descubrimiento.md` |
| F04 | Motor de mejora inteligente | PENDIENTE | F03 | `plan/bloques/F04_mejora_inteligente.md` |
| F05 | Envolvente ULTRA (motor de balas) | **APARCADO** — ver mandato activo |  F04 | `plan/bloques/F05_envolvente_ultra.md` |
| F06 | Meta-estrategias: el router | **APARCADO** — ver mandato activo |  F05 | `plan/bloques/F06_meta_router.md` |
| F07 | FONDEO: exámenes 3-8 días | PENDIENTE | F03 | `plan/bloques/F07_fondeo_examenes.md` |
| F08 | Verificación end-to-end y paper | PENDIENTE | F06, F07 | `plan/bloques/F08_verificacion_paper.md` |
| F09 | Front limpio | **PARCIAL** (16 rutas retiradas; el plan se lee de los bloques en `/plan`) | F08 | `plan/bloques/F09_front_limpio.md` |
| F10 | Operaciones e infraestructura (tareas para agentes) | EN_CURSO | — | `plan/bloques/F10_operaciones_infra.md` |
| — | Riesgos | VIGENTE | — | `plan/bloques/RIESGOS.md` |
| — | Reglas invariantes | VIGENTE | — | `plan/bloques/REGLAS_INVARIANTES.md` |

## OBJETIVOS DE RENTABILIDAD — SELLADOS (2026-08-31)

Hasta esta fecha el plan v4 no contenía ningún objetivo de rentabilidad **verificable**: "miles
de %" era prosa, y el objetivo de FONDEO no existía escrito en ninguna parte. El criterio 1.1
mide robustez, **no rentabilidad**, así que el sistema podía certificar como buena una
estrategia robusta pero pobre. Corregido:

| Track | Objetivo sellado | Se mide sobre | Techo de riesgo | Bloque |
| :--- | :--- | :--- | :--- | :--- |
| ULTRA | **~100 % mensual** (miles % anuales, decisión #5) | mediana de la distribución | reportar P(ruina) junto a la cifra | F05 |
| FONDEO | **≥20 % mensual SOSTENIBLE** | mediana de la distribución | **P(romper cuenta) ≤ 20 %** a 6 meses | F07 |

Reglas comunes a ambos: se mide sobre la **mediana**, nunca sobre la media (las colas derechas
la inflan); se reporta siempre con **p5, p95 y probabilidad de ruina**; son filtros
**POSTERIORES** al criterio 1.1, que sigue SELLADO y no se relaja; y si ninguna estrategia
llega, **se reporta la cifra real alcanzada** — ajustar costes, datos o gates para alcanzar el
número es violación grave de la doctrina.

En FONDEO, ante el conflicto entre maximizar ROI por cartucho y mantener la cuenta viva, manda
la **rentabilidad mensual sostenible** (decisión del usuario). El sistema venía optimizando ROI
por cartucho, que lleva a estrategias distintas.

---

Estados posibles de un bloque: `PENDIENTE` · `EN_CURSO` · `PARCIAL` · `HECHO` · `BLOQUEADO` · `VIGENTE` (doctrinal).

**Cómo se actualiza:** se edita el fichero del bloque (contenido y/o `estado` del frontmatter) y
se refleja la fila de esta tabla. Nada más. Un cambio de fase no exige reescribir el plan entero.
