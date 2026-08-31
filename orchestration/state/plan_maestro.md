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
| F00 | Limpieza del código | **PARCIAL** (C–G ejecutadas; unificaciones en Fase I) | — | `plan/bloques/F00_limpieza.md` |
| F01 | Saneamiento del catálogo | **HECHO** (0 supervivientes de 728) | F00 | `plan/bloques/F01_censo_catalogo.md` |
| F02 | Motor de backtest realista | **PARCIAL** (2.1 HECHO: motor 5.11.0; faltan 2.2/2.3) | F00 | `plan/bloques/F02_motor_realista.md` |
| F03 | Campaña de descubrimiento masiva | **EN_CURSO** (cripto minando con 5.11.0; TRADFI espera backfill) | F01, F02 | `plan/bloques/F03_campana_descubrimiento.md` |
| F04 | Motor de mejora inteligente | PENDIENTE | F03 | `plan/bloques/F04_mejora_inteligente.md` |
| F05 | Envolvente ULTRA (motor de balas) | PENDIENTE | F04 | `plan/bloques/F05_envolvente_ultra.md` |
| F06 | Meta-estrategias: el router | PENDIENTE | F05 | `plan/bloques/F06_meta_router.md` |
| F07 | FONDEO: exámenes 3-8 días | PENDIENTE | F03 | `plan/bloques/F07_fondeo_examenes.md` |
| F08 | Verificación end-to-end y paper | PENDIENTE | F06, F07 | `plan/bloques/F08_verificacion_paper.md` |
| F09 | Front limpio | PENDIENTE | F08 | `plan/bloques/F09_front_limpio.md` |
| — | Riesgos | VIGENTE | — | `plan/bloques/RIESGOS.md` |
| — | Reglas invariantes | VIGENTE | — | `plan/bloques/REGLAS_INVARIANTES.md` |

Estados posibles de un bloque: `PENDIENTE` · `EN_CURSO` · `PARCIAL` · `HECHO` · `BLOQUEADO` · `VIGENTE` (doctrinal).

**Cómo se actualiza:** se edita el fichero del bloque (contenido y/o `estado` del frontmatter) y
se refleja la fila de esta tabla. Nada más. Un cambio de fase no exige reescribir el plan entero.
