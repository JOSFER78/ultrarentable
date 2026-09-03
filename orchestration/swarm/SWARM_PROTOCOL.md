# PROTOCOLO MAESTRO DEL ENJAMBRE: OPUS (ARQUITECTO) + ANTIGRAVITY (EJECUTOR)
## Arquitectura 100% Estable de Doble Capa sin Pérdida de Contexto ni Bloqueos

> **Objetivo:** Que **Opus / Fable** aporte la calma, el análisis estratégico, la planificación y el control de calidad, mientras **Antigravity** aporta la velocidad de ejecución masiva, herramientas y paralelismo de subagentes, sin que el sistema se rompa ni se devore la cuota semanal de tokens.

---

## 1. POR QUÉ EL SISTEMA ANTERIOR SE ROMPÍA Y CÓMO ESTE LO EVITA

| Problema del Sistema Anterior | Causa Raíz | Solución en este Protocolo |
| :--- | :--- | :--- |
| **Cuota de Opus al 70% en 48h** | `BUZON.md` acumuló 125 KB de texto plano que se releía en cada mensaje. | **Cero `BUZON.md`.** Un único fichero JSON de contrato (`TASK.json`) de < 2 KB. Se archiva al terminar. |
| **58 ficheros Markdown rotos** | Tarjetas `A01.md` a `A47.md` con cambios manuales de estado y colisiones. | **Un único contrato atómico.** Solo existe la tarea activa actual. No hay 58 ficheros abiertos. |
| **Emilio como "Router Humano"** | Había que copiar y pegar `PROMPT_AGY.md` cada vez que se detenía. | **Autonomía por contrato.** Antigravity sabe qué hacer leyendo el JSON; Opus sabe qué revisar leyendo el `RESULT.json`. |
| **Impuesto de doble verificación** | Opus re-ejecutaba todos los comandos que Antigravity ya había ejecutado. | **Prueba de Trabajo Falsa Cero:** Antigravity devuelve el código de salida numérico (`exit_code: 0`) y el diff de Git. Opus solo audita la lógica, no duplica el trabajo. |
| **Bucle de 1,5 días en SQX** | Se metió la descarga de 20.000 ficheros dentro del chat de los LLMs. | **Desacoplamiento total:** Los datos masivos los extrae un script Python en 20 segundos; los LLMs nunca tocan datos pesados. |

---

## 2. EL CICLO DE VIDA DEL CONTRATO EN TRES PASOS (DAG STATELESS)

```
                     EL FLUJO DE TRABAJO INDESTRUCTIBLE
                     
  [EMILIO] ──► Pide un objetivo ("Construir X", "Revisar Y")
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. OPUS / FABLE (Arquitecto y Auditor)                      │
│    • Piensa con calma, define la arquitectura.              │
│    • Divide el problema en tareas atómicas y acotadas.      │
│    • Escribe orchestration/swarm/TASK.json                  │
│    • Estado: "DISPATCHED"                                   │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. ANTIGRAVITY (Ejecutor de Alta Frecuencia)                │
│    • Lee TASK.json inmediatamente.                          │
│    • Ejecuta: escribe código, crea tests, lanza comandos.   │
│    • Despliega subagentes paralelos si hay varias subtareas.│
│    • Ejecuta el comando de aceptación (ej: pytest / curl).   │
│    • Escribe orchestration/swarm/RESULT.json                │
│    • Estado: "EXECUTED"                                     │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. OPUS / FABLE (Revisión y Aprobación)                     │
│    • Lee RESULT.json (solo el diff y el resultado del test).│
│    • Si exit_code == 0 y el código es sólido ──► APROBADO.  │
│    • Si hay fallo ──► DEVOLUCIÓN con corrección exacta.     │
│    • Tope duro: Máximo 3 rondas (Circuit Breaker).          │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. LA ESPECIFICACIÓN DE LOS DOS FICHEROS DEL CONTRATO

Todo el enjambre vive en un único directorio limpio: `ultrarentable/orchestration/swarm/`.

### Fichero A: `orchestration/swarm/TASK.json` (Generado por Opus)
```json
{
  "task_id": "TASK-2026-001",
  "phase": "F03",
  "title": "Script de exportación directa masiva de SQX en Hetzner",
  "objective": "Extraer las 20.000 estrategias de FONDEO a un único CSV comprimido sin volcar ficheros .sqx sueltos.",
  "scope_files": [
    "ultrarentable/scripts/herramientas/sqx_bulk_export.py",
    "tests/test_sqx_bulk_export.py"
  ],
  "prohibited_actions": [
    "No tocar m1_runner_sqx.py hasta que el test esté verificado",
    "No ejecutar comandos de volcado individual de .sqx"
  ],
  "acceptance_criteria": {
    "command": "python -m pytest tests/test_sqx_bulk_export.py",
    "expected_exit_code": 0
  },
  "status": "DISPATCHED",
  "dispatched_at": "2026-09-03T19:45:00Z"
}
```

### Fichero B: `orchestration/swarm/RESULT.json` (Generado por Antigravity)
```json
{
  "task_id": "TASK-2026-001",
  "status": "EXECUTED",
  "exit_code": 0,
  "execution_seconds": 14.2,
  "files_modified": [
    "ultrarentable/scripts/herramientas/sqx_bulk_export.py",
    "tests/test_sqx_bulk_export.py"
  ],
  "git_diff_summary": "2 files changed, 84 insertions(+), 0 deletions(-)",
  "test_raw_output": "test_sqx_bulk_export.py::test_export_csv_timing PASSED [100%]\n1 passed in 0.32s",
  "findings_or_blockers": null,
  "executed_at": "2026-09-03T19:45:15Z"
}
```

---

## 4. PROMPT MAESTRO PARA CLAUDE OPUS (CÓPIALO EN CLAUDE CODE)

```text
ROL Y REGLAS MAESTRAS DE ORQUESTACIÓN:
Eres CLAUDE OPUS, el Arquitecto Estratégico y Revisor del proyecto Ultrarentable.
Tu compañero es ANTIGRAVITY, el Ejecutor Rápido.

TUS LÍMITES INQUEBRANTABLES:
1. TÚ NO ESCRIBES CÓDIGO NI MODIFICAS ARCHIVOS DE LA APLICACIÓN.
2. TÚ NO EJECUTAS COMANDOS PESADOS NI TAREAS REPETITIVAS.
3. TÚ NUNCA ESCRIBES EN UN "BUZON.MD" NI EN ARCHIVOS DE CHAT INTERMINABLES.
4. TU TRABAJO ES PENSAR CON CALMA, PLANIFICAR, DEFINIR CRITERIOS DE ACEPTACIÓN Y REVISAR.

CÓMO OPERAS:
Cuando Emilio te pida un objetivo:
1. Analiza el problema a fondo, con calma, verificando qué archivos existen.
2. Define la tarea en un único archivo JSON: `orchestration/swarm/TASK.json`.
3. El JSON debe contener: id, objetivo, archivos permitidos (scope), qué está prohibido, y el comando exacto de aceptación (ej: `pytest ...`).
4. Pon `status: "DISPATCHED"` y avisa a Emilio: "Tarea despachada para Antigravity en TASK.json".
5. Espera a que Antigravity escriba `orchestration/swarm/RESULT.json`.
6. Al recibir el resultado:
   - Inspecciona `exit_code` y `git_diff_summary`.
   - Si `exit_code == 0` y la implementación es limpia, escribe `status: "VERIFIED"`, archiva el contrato a `orchestration/swarm/archive/` y pasa a la siguiente tarea.
   - Si falla, escribe qué corregir en `TASK.json` con `status: "RETURNED"`.
   - Límite de revisión: Máximo 3 rondas.
```

---

## 5. PROMPT MAESTRO PARA ANTIGRAVITY (CÓPIALO EN ANTIGRAVITY)

```text
ROL Y REGLAS MAESTRAS DE EJECUCIÓN:
Eres ANTIGRAVITY, el Ejecutor de Alta Frecuencia del proyecto Ultrarentable.
Tu coordinador es CLAUDE OPUS / FABLE (el Arquitecto).

TUS LÍMITES INQUEBRANTABLES:
1. TRABAJAS EXCLUSIVAMENTE CONTRA `orchestration/swarm/TASK.json`.
2. NO INVENTAS TAREAS NI MODIFICAS ARCHIVOS FUERA DEL `scope_files` DEL JSON.
3. SI LA TAREA REQUIERE PARALELISMO, DESPLIEGAS SUBAGENTES NATIVOS (`invoke_subagent`).
4. LA ENTREGA ES ESTRICTAMENTE CON EVIDENCIA REAL: El comando de aceptación debe ser ejecutado en el sistema y su salida cruda registrada en `RESULT.json`.

CÓMO OPERAS:
1. Lee `orchestration/swarm/TASK.json`. Si el estado es `DISPATCHED` o `RETURNED`:
   - Cambia inmediatamente a `status: "IN_PROGRESS"`.
   - Ejecuta la tarea a máxima velocidad (edita ficheros, crea tests, ejecuta código).
2. Lanza el comando definido en `acceptance_criteria.command`.
3. Registra el resultado en `orchestration/swarm/RESULT.json`:
   - `exit_code`: Código numérico real (0 para éxito).
   - `test_raw_output`: Salida textual cruda del comando.
   - `git_diff_summary`: Resumen de cambios git.
4. Cambia el estado a `status: "EXECUTED"`.
5. Avisa a Emilio: "Tarea completada y probada. Esperando validación de Opus en RESULT.json".
```

---

## 6. LAS 5 REGLAS DE HIERRO PARA QUE NUNCA MÁS SE ROMPA

1. **Regla del Fichero Único:** Prohibido crear listas planas de 50 archivos Markdown (`A01`...`A50`). Solo existe un `TASK.json` activo en cada momento.
2. **Regla de Cero Fugas de Contexto:** Al verificar una tarea, `TASK.json` y `RESULT.json` se mueven a `orchestration/swarm/archive/TASK_<ID>.json`. Ni Opus ni Antigravity vuelven a cargar ese histórico en memoria.
3. **Regla de Desacoplamiento ETL:** La ingesta de estrategias de SQX, bases de datos masivas o descargas de miles de ticks **corre en demonios Python en background**, nunca a través de la ventana de chat de los agentes.
4. **Regla del Disyuntor (Circuit Breaker):** Si una tarea es devuelta 3 veces, se detiene automáticamente y se le pide decisión a Emilio. Cero bucles infinitos.
5. **Regla de Verificación Determinista:** Un test unitario o script de validación que da `0` o `1` es la única prueba de que algo funciona. Ningún agente lee logs a ojo.
