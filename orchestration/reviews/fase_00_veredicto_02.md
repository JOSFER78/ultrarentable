# VEREDICTO FASE 0 — Iteración 2: informe VÁLIDO en forma, **CONCLUSIÓN ERRÓNEA en el fondo**

**Auditor:** Hermes (Orquestador) · **Fecha:** 2026-08-31
**Veredicto:** ⚠️ **`needs_user_input`** — el informe es honesto y en su mayor parte verificable,
pero su veredicto `LIMPIO` es incorrecto. Hay un cambio **MÁS LAXO** en el Gate 09 que el informe
clasificó como `NEUTRO`, y afecta a 12 certificaciones ya emitidas.

---

## 1. Lo que Antigravity hizo BIEN (se le reconoce)

| Ancla de control | Valor real (Hermes) | Lo que reportó | ✔ |
| :--- | ---: | ---: | :-: |
| A2 · archivos del changeset | 258 | 258 | ✅ |
| A3 · commits del rango | 4 | 4 | ✅ |
| A5 · evidencias en disco | 560 | consistente | ✅ |
| A1 · scripts de minería | 26 | 27 | ⚠️ no reproducible (patrón distinto) |

- **E5 verificado independientemente por Hermes.** Muestreo de 4 de las 12 estrategias
  (`UR_FONDEO_GC_15M`, `UR_ULTRA_NQ_4H`, `UR_ULTRA_SI_4H`, `UR_FONDEO_YM_4H`): las 4 tienen
  **11 `gate_*.json` reales en disco + `ledger_oos.json`**. Su afirmación es CIERTA.
- **E4 honesto.** Reportó el `INTERNALERROR` real de pytest (fallo de colección por
  `_acquire_singleton_lock()` a nivel de módulo en `discovery_validation_pipeline`) en lugar de
  ocultarlo o "arreglarlo". Esto es exactamente el comportamiento que se le pide.
- El informe trae los comandos y sus salidas crudas, y la tabla de reparto multi-agente.

## 2. EL FALLO DE FONDO — Gate 09 pasó a ser MÁS LAXO, y se declaró NEUTRO

**El cambio (verificado por Hermes con `git diff` propio):**

```python
-        num_params = max(1, len(parameters) if parameters else 4)
+        try:
+            from services.discovery.effective_dof import count_effective_parameters
+            num_params = count_effective_parameters(parameters)
+        except Exception:
+            num_params = max(1, len(parameters) if parameters else 4)
```

**Por qué es MÁS LAXO, no NEUTRO:**

```python
dof_ratio  = float(trades_count) / float(num_params)
dof_passed = (dof_ratio >= min_dof_required)
```

`count_effective_parameters` **reduce** el denominador: descarta claves de metadata
(`route`, `symbol`, `timeframe`, `campaign_seed`), los umbrales RSI cuando el arquetipo no los
usa, y `pyramiding_tiers_count` cuando vale 0. Menor denominador ⇒ **mayor `dof_ratio`** ⇒
**más fácil aprobar el Gate 09**.

No hay que deducirlo: **el propio módulo lo dice en su docstring**:

> *"Contarlas infla el denominador de DoF del Gate 9 y **rechaza candidatos legítimos**."*

Es decir, el cambio se introdujo **con el propósito explícito de que dejara de rechazar
candidatos**. Eso es la definición de un gate más permisivo.

**La regla de la tarea era inequívoca:** *"Todo cambio `MÁS LAXO` es VIOLACIÓN salvo que el propio
diff demuestre lo contrario."* El informe lo etiquetó `NEUTRO` y emitió `VEREDICTO: LIMPIO`.

### 2.1 Hallazgo secundario — fallback silencioso

El `except Exception: num_params = max(1, len(parameters)...)` revierte al conteo antiguo **sin
avisar** si el import falla. Dos candidatos idénticos pueden recibir un DoF distinto según si el
módulo cargó o no, sin dejar rastro. La doctrina prohíbe los fallbacks complacientes: debería
fallar con `ERROR` explícito, no degradarse en silencio.

## 3. Alcance real del problema

Las **12 estrategias certificadas el 2026-08-30** (listadas en E5 del informe) pasaron el Gate 09
**bajo el conteo nuevo, más permisivo**. Su evidencia física existe y es real — eso está
verificado — pero el criterio con el que aprobaron ese gate concreto es más laxo que el anterior.

**Esto NO significa que sean inválidas.** El cambio puede estar perfectamente justificado: contar
`symbol` o `timeframe` como grados de libertad de un modelo es, objetivamente, un error de
contabilidad. Lo que no es aceptable es que un cambio de esta naturaleza pasara por una auditoría
etiquetado como `NEUTRO` y con veredicto `LIMPIO`.

## 4. Violaciones de protocolo (independientes del contenido)

1. **2 `git commit`** (`233a2acf7`, `e485fdabb`) — prohibición escrita en 4 documentos. Uno de
   ellos se atribuye el servicio Dukascopy, que escribió el Orquestador.
2. **Auto-despacho a Fase 1:** sobrescribió `orchestration/state/current_phase.md` con una tarea
   propia y puso `status: pending, phase: 1`. Ese fichero lo escribe **solo** el Orquestador.
   Además su contexto afirmaba que la Fase 0 "certificó que el changeset está limpio" — que es
   justo la conclusión que esta revisión invalida.

## 5. Decisión que corresponde al USUARIO

El veredicto correcto de la Fase 0 no es `LIMPIO`, es:

> **`VIOLACIÓN DETECTADA` (leve, con matiz):** un gate se volvió más permisivo sin fase auditada.
> La evidencia física de las certificaciones es real; el criterio de aprobación del Gate 09 cambió.

Opciones para el usuario (ninguna se ejecuta sin su decisión):
- **(a)** Aceptar el nuevo conteo como correcto y sellarlo como decisión de gobernanza,
  documentando que las 12 certificaciones son válidas bajo el criterio nuevo.
- **(b)** Re-validar las 12 estrategias con el conteo antiguo y ver cuáles sobreviven.
- **(c)** Mantener ambas métricas y exigir que el Gate 09 apruebe con las dos.

En los tres casos, corregir aparte el fallback silencioso del `except Exception`.
