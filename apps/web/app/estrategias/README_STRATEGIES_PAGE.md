# Estrategias — contrato de producto

`/estrategias` es la página maestra (decisión sellada #16, `docs/19_UI_STYLE_SPEC.md` §4):
muestra SOLO las estrategias que ya cumplen la definición sellada de "válida para FONDEO"
(ruta FONDEO + motor vigente + ≥200 operaciones OOS + PF OOS ≥1,25 + 11 comprobaciones con
evidencia). Mandato de Emilio (2026-09-02): el usuario no quiere ver las fallidas, solo las
que ya funcionan y todos los datos para llevarlas al Trading Desk de FONDEO. Lo demás sigue
disponible, pero un clic más allá (`/candidatos`, archivo técnico de uso interno).

Debajo, cuatro tarjetas enlazan a los cuatro módulos del pipeline
(`orchestration/state/ARQUITECTURA_MODULAR_ESTRATEGIAS.md`), cada uno con su propia subpágina:

- `/estrategias/generacion` (M1) — StrategyQuant X: estado de conexión, proyectos, crudas
  extraídas y últimas extracciones. Los controles técnicos (`SQXToolsPanel.tsx`) viven aquí,
  plegados por defecto ("Herramientas técnicas · uso interno"), nunca en la maestra.
- `/estrategias/mejora` (M2) — el bucle que prueba y descarta; últimas campañas leídas de
  `orchestration/results/telemetria/embudo_*.json` vía `api-telemetria/route.ts`.
- `/estrategias/valoracion` (M3) — el examen contra reglas de prop firms; objetivos sellados.
- `/estrategias/meta` (M4) — composición de varias certificadas; necesita ≥2 válidas.

Las 4 subpáginas comparten `_bloques/NavBloques.tsx` (navegación entre módulos + vuelta a la
maestra) y `_bloques/comun.tsx` (tipos, `esValidaFondeo`, formato, componentes de presentación).

## Dentro de esta página
- identidad de estrategia;
- activo y timeframe;
- estado de validación (solo lo que cumple la definición sellada, en el bloque principal);
- dataset y hashes de provenance;
- acceso a Candidatos (archivo técnico) y a los 4 módulos del pipeline;
- extracción real desde StrategyQuant (movida a `/estrategias/generacion`).

## Fuera de esta página
- cuentas de trading;
- tamaño de cuenta y capital;
- reglas de prop firm/fondeo (viven en `/estrategias/valoracion` y en `/fondeo`);
- selección de broker/exchange;
- ejecución en vivo;
- gestión de posiciones.

## Principio de identidad
**Strategy identity ≠ execution venue.**

Una estrategia se identifica por su estructura canónica y su evidencia. El venue posterior añade condiciones de ejecución, costes, liquidez y slippage. No se duplica el catálogo por exchange.

## Regla de presentación
La UI nunca convierte un campo ausente en cero ni en una cifra inventada. Usa `sin evidencia`
o `NO DATA` (lenguaje llano, sin siglas técnicas en el texto principal). Ningún gate se pinta
como aprobado a partir del `status`: solo desde evidencia real (`certified.gates` con
`passed === true`).
