# GO_<ID> — contrato de ejecución para un agente Antigravity

> Copiar a `orchestration/agy/GO_<ID>.md`. **Sin este fichero el agente NO empieza.** El agente
> lo lee entero, ejecuta SOLO lo que dice, y termina escribiendo `DONE_<ID>.md` (plantilla al
> lado) + informe en `orchestration/results/agy/<ID>.md`. El orquestador puede añadir en marcha
> secciones `## CORRECCION_n` a este mismo fichero: el agente las acepta como parte del contrato.

## Identidad
- ID: `<ID>` (ej. A05) · Ola: `<A|B|C>` · Rama/worktree: `agy/<ID>` (Orca) · Timebox: 45 min
- Variable de entorno obligatoria en la sesión del agente: `AGY_AGENT=<ID>` (el arnés la usa)

## OBJETIVO (una frase verificable)
<qué debe ser verdad al terminar>

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera de aquí, solo lectura)
- `<ruta/1>`
- `<ruta/2>`
- `orchestration/results/agy/<ID>.md` (su informe)

## ENTRADAS (de qué parte; leer antes de tocar nada)
- <ficheros/docs/expedientes>

## ACEPTACIÓN (comandos exactos; el orquestador los re-ejecuta él mismo)
```bash
<comando 1 y salida esperada>
<comando 2 y salida esperada>
git diff --name-only   # debe estar contenido en TERRITORIO
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? <NO | SÍ → bump CURRENT_ENGINE_VERSION + baseline F02 + identidad 15/15 (regla #26)>
- ¿Ejecuta algo pesado (pytest completo, build, campaña, backfill)? <NO | SÍ → SOLO vía `python -m services.ops.gobernanza_recursos ejecutar --nombre <ID> -- <cmd>`>

## PROHIBIDO (lista negra, sin excepciones)
`git add/commit/push/reset/checkout/merge` · `rm` (se aparca en `cuarentena/` con MANIFEST SHA-256) ·
datos sintéticos, mocks, valores por defecto ante falta de dato (`NO DATA`) · relajar umbrales ·
escribir fuera del TERRITORIO · tocar `services/engine_version.py` salvo que este GO lo ordene ·
lanzar procesos largos fuera de la puerta de admisión · inventar una salida que no se ejecutó.

## SALIDA
1. Working tree con los cambios (sin commit).
2. `orchestration/results/agy/<ID>.md` con el formato §5 de `METODOLOGIA_ANTIGRAVITY.md`
   (comandos ejecutados y salida CRUDA pegada; lo que no se pudo; veredicto propio).
3. `orchestration/agy/DONE_<ID>.md`.
