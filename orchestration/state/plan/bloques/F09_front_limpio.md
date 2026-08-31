---
id: F09
titulo: "Front limpio"
estado: PENDIENTE
depende_de: ["F08"]
desbloquea: []
verificacion_global: "Cero datos inventados en la web: sin dato ⇒ SIN DATOS. Acceso solo autorizados."
actualizado: "2026-08-31"
---

# FASE 9 — FRONT LIMPIO

> *"y luego en front"*.

- Consolidar las 33 páginas actuales en **páginas maestras con subpáginas jerarquizadas**.
- Cero datos inventados: si no hay dato, `SIN DATOS`, nunca un valor de relleno.
- Landing sin autenticar; acceso solo para autorizados por `josferestudio@gmail.com`.
- Firebase se mantiene en PECEMI de momento, pero el `apiKey` sale del código a variable de
  entorno con fallo explícito si falta.
- Trading desk (BingX para ULTRA, gestión de cuentas para FONDEO) **al final**, cuando haya
  algo real que mostrar.

## Integración con el plan por bloques (añadida 2026-08-31)

La página del plan en `apps/web` debe leer estos ficheros de `orchestration/state/plan/bloques/`
(frontmatter YAML: `id`, `titulo`, `estado`, `depende_de`, `desbloquea`, `verificacion_global`,
`actualizado`) y renderizar el grafo de fases con su estado real. Un bloque = una tarjeta
editable. Nada de estados duplicados a mano en el front: la fuente de verdad es el fichero del
bloque.
