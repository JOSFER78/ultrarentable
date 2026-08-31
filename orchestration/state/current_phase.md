# FASE 1 — CONSOLIDACIÓN DE CÓDIGO RESIDUAL Y ESTRUCTURA DE ARCHIVOS

> **ANTES DE EMPEZAR, LEE `orchestration/METODOLOGIA_ANTIGRAVITY.md` ENTERO.** Es tu procedimiento operativo.
> Plan vigente: `orchestration/state/plan_maestro.md` (v3, 2026-08-31).
> Decisiones selladas del usuario: `orchestration/DOCTRINA_ORQUESTADOR.md §14`. **Léelas antes de empezar.**

## Contexto

Tras completar con éxito la auditoría forense de la Fase 0 (que certificó que el changeset de 258 archivos está limpio de datos sintéticos y mantiene la rigurosidad de los 11 gates), la **Fase 1** tiene como objetivo reducir la superficie de mantenimiento del repositorio mediante la consolidación de scripts y reestructuración documental **SIN BORRAR NINGÚN ARCHIVO**.

## Qué tienes que entregar (4 entregables con verificación física)

### E1 — Unificación del CLI de Minería (`scripts/mine.py`)
- Crear un CLI unificado `scripts/mine.py` con interfaz de línea de comandos `argparse`:
  `python3 scripts/mine.py --track {ultra,fondeo} --symbol <SYM> --tf <TF> --profile <PROFILE>`
- Este script absorbe de manera limpia y modular toda la lógica operativa de los ~25 scripts `mine_and_certify_*` sueltos.
- Mover los 25 scripts originales a `cuarentena/scripts_legacy_mining/` usando `git mv` (creando la carpeta si no existe).
- Generar un manifiesto `cuarentena/scripts_legacy_mining/MANIFEST_SHA256.txt` con la ruta original, nueva ruta y hash SHA-256 de cada archivo movido.

### E2 — Reorganización de Documentación Archiva (`docs/archive/`)
- Mover mediante `git mv` todos los documentos `.md` SUPERSEDED o históricos en la raíz de `docs/` hacia `docs/archive/` según la clasificación del SSOT §6.
- **PROHIBIDO borrar archivos.** Utilizar exclusivamente movimientos de Git (`git mv`).

### E3 — Histórico de Seguimiento (`historico/`)
- Mover los informes con veredicto cerrado en `.agents/informe&seguimiento/` hacia `historico/` mediante `git mv`.

### E4 — Actualización del SSOT de Ideas y Plan
- Actualizar `docs/00_MASTER_IDEAS_Y_PLAN.md` §5 reflejando la incorporación formal de las 20 decisiones selladas del usuario (Doctrina §14).

## Método obligatorio
Multi-agente. Mínimo 2 subagentes en paralelo:
- **A1** → Absorción de código en `scripts/mine.py`, `git mv` a `cuarentena/` y generación de manifiesto SHA-256.
- **A2** → Archivo documental (`docs/archive/`, `historico/`) y actualización del SSOT `00_MASTER_IDEAS_Y_PLAN.md`.

## Reglas de esta fase
1. **CERO BORRADOS.** Ningún archivo se elimina; todo código legacy se traslada a `cuarentena/` o `docs/archive/`.
2. **Verificación de ejecutor:** Probar `python3 scripts/mine.py --help` para asegurar sintaxis limpia y cero SyntaxError/ImportError.
3. Al terminar: informe en `orchestration/results/fase_01.log`, actualización de `status.json` y creación del fichero `DONE`.
