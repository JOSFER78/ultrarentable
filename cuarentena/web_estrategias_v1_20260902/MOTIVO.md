# MOTIVO DE CUARENTENA — apps/web/app/estrategias/ (v1)

**Fecha:** 2026-09-02  
**Agente:** B17 (Ola B, Tarea task_27108c33fa40 / W5 / GO_B17)  
**Directivas asociadas:** Mandato de Emilio (2026-09-02: "sin paneles enormes ni colorines ni nada de hecho con IA"), docs/19_UI_STYLE_SPEC.md, docs/18_STRATEGIES_PAGE_SPEC.md, Criterio REAL-ONLY  

---

## 1. Identificación de los artefactos aparcados

1. **`page.tsx` (v1 inicial)**:
   - Ruta original: `apps/web/app/estrategias/page.tsx`
   - Tamaño: 1.910 LOC (~75 KB)
   - SHA-256: `1113ca93c67712eef00d63b98859c751d0805a8c58c6268b5355c4415408a459`
   - Destino en cuarentena: `cuarentena/web_estrategias_v1_20260902/page.tsx`

2. **`SQXToolsPanel.tsx` (v1 componentes de prueba)**:
   - Ruta original: `apps/web/app/estrategias/SQXToolsPanel.tsx`
   - Tamaño: 383 LOC (~16 KB)
   - SHA-256: `a74e69a59aa00f8eb7be69cd6162e894047e205965545f7b9edc850e4ca79275`
   - Destino en cuarentena: `cuarentena/web_estrategias_v1_20260902/SQXToolsPanel.tsx`

---

## 2. Motivo técnico y de producto

1. **Exceso de decoraciones y paneles AI:** La versión previa de `page.tsx` acumulaba 1.910 líneas con múltiples tarjetas, bordes redondeados (6-8px), paneles excesivos y estilos no alineados con la estética terminal sobria (Orca / Claude Code) requerida por el mandato de Emilio.
2. **Colores prohibidos en componentes no integrados:** `SQXToolsPanel.tsx` contenía clases tailwind de colores arbitrarios (`cyan`, `emerald`, `rose`, `slate`, `bg-[#090d16]`) y sombras (`shadow-xl`), violando la especificación monocroma estricta de `docs/19_UI_STYLE_SPEC.md`.
3. **Reescritura sobria canónica (GO_B17):** La página maestra `/estrategias` se reescribe como una interfaz monocroma, densa, sin adornos ni tarjetas, en una sola columna ≤ 1100 px, con línea de estado honesta y tablas/listas planas para M1-M4, ≤ 700 líneas y consumo canónico idéntico de la API.
4. **Preservación:** De acuerdo con la directiva de no destrucción (nunca `rm`), ambos archivos originales se aparcan íntegros en esta cuarentena con su manifiesto SHA-256 verificado.
