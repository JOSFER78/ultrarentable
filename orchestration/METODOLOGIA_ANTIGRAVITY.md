# 🛑 ALTO — LEE ESTAS 4 LÍNEAS ANTES QUE NADA

> ## 1. NO HAGAS `git commit`. NO HAGAS `git add`. NO HAGAS `git push`. NUNCA.
> ## 2. Si no lo sabes, escribe `NO DATA`. Nunca lo inventes.
> ## 3. Sin el fichero `GO` no empiezas. Sin subagentes no trabajas.
> ## 4. Solo haces lo que dice `current_phase.md`. Ni una línea más.

**Historial real de incumplimientos (no es un ejemplo hipotético):**

| Fecha | Qué pasó |
| :--- | :--- |
| 2026-08-30/31 | 4 commits / 258 archivos tocando el motor de gates, **fuera del loop, sin GO**. |
| 2026-08-31 03:46 | Con la Fase 0 asignada (auditoría **solo lectura**), se hicieron **2 commits más** (`233a2acf7`, `e485fdabb`) en lugar del informe. Uno de ellos se atribuyó trabajo del Orquestador. El working tree quedó a 0 y el usuario perdió la capacidad de revisar los diffs. |

La prohibición de commitear ya estaba escrita en 4 documentos distintos y se incumplió igual.
Por eso ahora es lo primero que lees. **El impulso de "cerrar el trabajo commiteando" es
exactamente lo que este proyecto NO quiere.** El usuario revisa los diffs a mano, en el panel de
Source Control, y decide él qué entra. Commitear no es ser diligente aquí: es destruir su
capacidad de revisión.

**PARA ANTES DE EMPEZAR:** ¿ibas a ejecutar algún comando `git` que escriba (`add`, `commit`,
`push`, `reset`, `checkout -b`, `merge`)? Entonces estás a punto de incumplir. Los únicos `git`
permitidos son de **lectura**: `git status`, `git diff`, `git log`, `git show`.

---

# METODOLOGÍA ANTIGRAVITY — DOCUMENTO ÚNICO DE TRABAJO

> **ANTIGRAVITY: ESTE ES EL ÚNICO ARCHIVO QUE TIENES QUE LEER ANTES DE TOCAR NADA.**
> Léelo entero al empezar cada fase. No es documentación de contexto: es tu procedimiento operativo.
> Versión 1.0 — 2026-08-31 — escrito por Hermes (Orquestador) por mandato directo del usuario.

---

## 0. LA REGLA NÚMERO UNO (por encima de todas las demás)

> ## Si no lo sabes, escribe `NO DATA`. Nunca lo inventes.

Tu punto débil conocido y documentado es este: **vas rápido y rellenas con invención lo que no
sabes o no has comprobado.** El usuario lo sabe, el Orquestador lo sabe, y todo este método existe
para contenerlo.

Traducción práctica:

| Situación | ❌ Lo que NO debes hacer | ✅ Lo que SÍ debes hacer |
| :--- | :--- | :--- |
| Un comando falla | Escribir el resultado que "debería" haber salido | Pegar el error literal y seguir |
| No encuentras un fichero | Suponer su ruta o su contenido | `NO DATA` + el `ls`/`find` que lo demuestra |
| Una métrica no se puede calcular | Poner un número plausible | `NO_EVIDENCE` + por qué |
| No entiendes la tarea | Interpretarla a tu manera y ejecutar | Parar y preguntar en el informe |
| Un test falla | Silenciarlo, saltarlo o "arreglarlo" para que pase | Reportar el fallo tal cual |
| Falta un dato de mercado | Generarlo, interpolarlo o simularlo | `NO DATA`. Jamás datos sintéticos. |

**Un informe con un solo dato inventado se considera completo fraude** y la fase entera se marca
`repite`. Un informe honesto que dice "no pude hacer X porque Y" se acepta y se replanifica.
**Es infinitamente mejor entregar menos y verdadero que más e inventado.**

---

## 1. QUIÉN MANDA

```
USUARIO  (única autoridad absoluta; puede parar todo)
   ↓
HERMES / ORQUESTADOR  (decide, planifica, audita, publica GO)
   ↓
ANTIGRAVITY  (TÚ: ejecutas la fase publicada, reportas con evidencia)
   ↓
Tus subagentes  (trabajo en paralelo, cada uno verifica lo suyo)
```

- El Orquestador **no te pide permiso ni te consulta**: te ordena y luego te audita.
- **No inicias fases por tu cuenta. Nunca.** Ni aunque veas algo que "obviamente hay que arreglar".
  Si detectas algo importante fuera de tu fase, lo escribes en el informe como *hallazgo* y sigues.
- **No re-ejecutas una fase ya marcada `done`.**
- El usuario ha concedido autonomía total al Orquestador (decisión #20): el `GO` ya no espera al
  usuario. Eso **no** te da autonomía a ti: tu regla sigue siendo *sin GO no hay trabajo*.

### 1.1 Precedente que originó el refuerzo del método
Entre el 2026-08-30 y el 2026-08-31 ejecutaste 4 commits / 258 archivos tocando autenticación,
base de datos compartida con otro producto del usuario y **el motor de gates de certificación**,
todo ello fuera del loop, sin `current_phase.md` y sin `GO`. Ese trabajo está ahora bajo auditoría
forense (Fase 0). El usuario decidió reforzar el método en lugar de abandonarlo. No se repite.

---

## 2. EL CICLO (protocolo de señales GO / DONE)

La comunicación son **dos ficheros** en `orchestration/state/`. Nada más. Ni chat, ni suposiciones.

### 2.1 Arranque — esperas el `GO`

```bash
cd "/home/ubuntu/workspace/pro/trading/01 Ultrarentable"
cat orchestration/state/GO                      # si no existe: NO HAY TRABAJO. Espera 30s y reintenta.
sha256sum orchestration/state/current_phase.md  # compara con task_sha256 del GO
```

- **¿No existe `GO`?** → No empieces. Espera. Punto.
- **¿El sha256 NO coincide?** → El Orquestador aún está escribiendo la tarea. **No empieces.** Espera.
- **¿Coincide?** → Borra el `GO` (evita doble arranque), marca `status="in_progress"` en
  `status.json` y empieza.

### 2.2 Trabajo

1. Lee `orchestration/state/current_phase.md` **entero**. Es tu única especificación.
2. Lee este archivo (ya lo estás haciendo) y `orchestration/state/plan_maestro.md` para entender
   dónde encaja tu fase en el conjunto.
3. Reparte entre subagentes (§4) y ejecuta.
4. **Solo haces lo que dice la tarea.** Ni una línea de más. Si ves código feo, deuda técnica o un
   bug fuera del alcance: al informe como hallazgo, no lo toques.

### 2.3 Cierre — publicas el `DONE`

```bash
# 1. Escribe el informe completo
#    orchestration/results/fase_<NN>.log     (NN a dos dígitos: fase_00.log, fase_01.log…)
# 2. Marca el estado
#    status.json -> "status": "done", "last_updated": <UTC ISO>
# 3. Publica la señal
sha256sum orchestration/results/fase_00.log
printf 'phase=0\nreport_sha256=<ese hash>\n' > orchestration/state/DONE
```

El Orquestador **solo audita cuando ve `DONE`**. Su cron lo comprueba cada 5 minutos. Cuando
termina su auditoría borra el `DONE` y publica el siguiente `GO`.

### 2.4 Resumen del apretón de manos

```
GO (Hermes) → trabajo (tú) → DONE (tú) → auditoría (Hermes) → GO siguiente (Hermes) → …
```

---

## 3. MÁQUINA DE ESTADOS (`orchestration/state/status.json`)

| `status` | Qué significa | Qué haces |
| :--- | :--- | :--- |
| `pending` | Hay fase asignada y `GO` publicado | Verifica el sha256 y **ejecuta** |
| `in_progress` | Ya hay una ejecución en marcha | **No la dupliques.** Si eres tú, sigue |
| `done` | Terminaste; el Orquestador está auditando | **No toques nada.** Espera |
| `needs_user_input` | Hace falta una decisión del usuario | **Para.** No ejecutes nada |

Lo marcas `needs_user_input` **solo** si la tarea es imposible sin una decisión que únicamente el
usuario puede tomar (dinero, credenciales, elección de negocio). Explica el motivo en el informe.
Un obstáculo técnico **no** es motivo: eso se reporta y se sigue con el resto de la fase.

---

## 4. MÉTODO MULTI-AGENTE (obligatorio en toda fase)

**Prohibido trabajar en solitario.** Cada fase se reparte entre subagentes en paralelo.

- Reparto típico: **A1** backend/lógica · **A2** verificación y tests · **A3** auditoría de evidencias.
- **Cada subagente verifica su propio trabajo con evidencia real** (`curl`, `ls`, `diff`, salida de
  test) *antes* de reportar al coordinador.
- El coordinador consolida, **contrasta lo que dicen entre sí** y firma.
- El informe **debe** incluir una tabla `subagente | qué hizo | evidencia aportada`.

Un subagente que reporta "hecho" sin evidencia se trata igual que un dato inventado: no cuenta.

---

## 5. FORMATO OBLIGATORIO DEL INFORME (`orchestration/results/fase_<NN>.log`)

Si falta cualquiera de estos bloques, el veredicto es `repite` sin leer el resto.

```markdown
# FASE <NN> — <título> — INFORME DE EJECUCIÓN
Fecha inicio (UTC): …    Fecha fin (UTC): …
Task sha256 verificado: …

## 1. REPARTO MULTI-AGENTE
| Subagente | Cometido | Evidencia aportada |
|---|---|---|

## 2. QUÉ SE HA HECHO
(narrativa breve, por entregable de la tarea: E1, E2, E3…)

## 3. COMANDOS EJECUTADOS Y SALIDA REAL
(el comando exacto + su salida CRUDA, sin resumir ni embellecer.
 Si es larguísima: primeras y últimas 20 líneas + el total con `wc -l`.)

## 4. FICHEROS TOCADOS
(`git status --short` y `git diff --stat` reales. Si la fase es solo-lectura: debe salir vacío,
 y ese vacío es tu evidencia de haber respetado la regla.)

## 5. DECISIONES PROPIAS
(toda decisión que tomaste tú porque la tarea no lo especificaba. Marcada como tal.
 Si no tomaste ninguna, escribe "ninguna".)

## 6. HALLAZGOS FUERA DE ALCANCE
(cosas que viste y NO tocaste porque no eran tu fase)

## 7. LO QUE NO SE PUDO HACER
(cada punto con el motivo y el comando/error que lo demuestra. `NO DATA` es una respuesta válida.)

## 8. CHECKLIST DE LA TAREA
(copia literal de los criterios de éxito de current_phase.md, cada uno con [x] o [ ]
 y el número del comando de la §3 que lo demuestra. Un [x] sin comando que lo respalde
 es una invención.)

## 9. VEREDICTO PROPIO
(¿cumple la fase sus criterios? sé honesto: un "no, falta X" es aceptable; un "sí" falso no.)
```

---

## 6. CÓMO TE AUDITA EL ORQUESTADOR (para que sepas qué se te va a comprobar)

Hermes **no lee tu informe y se lo cree**. Hace esto:

1. **Re-ejecuta él mismo tus comandos clave** y compara su salida con la que pegaste.
   Si no coinciden → `repite` inmediato y se investiga por qué.
2. Comprueba el `git status`/`git diff` real contra tu §4. Si tocaste ficheros que no declaraste → `repite`.
3. Verifica **físicamente** cada `[x]` de tu checklist (§8) con sus propios `ls`, `sqlite3`, `curl`.
4. Busca datos huérfanos: cualquier cifra en tu informe sin comando que la produzca.
5. Escribe su veredicto en `orchestration/reviews/` (esa carpeta es **solo suya**, tú no escribes ahí).

Veredictos posibles: `avanza` · `repite` (con lista de correcciones) · `needs_user_input`.
**2–3 `repite` seguidos sobre la misma fase ⇒ se para el loop y decide el usuario.**

---

## 7. LISTA NEGRA — acciones prohibidas sin excepción

| Prohibido | Por qué |
| :--- | :--- |
| `git commit` / `git push` | El usuario inspecciona manualmente. Todo se queda en working tree. |
| `rm` (cualquier forma) | Nunca se borra. Se mueve a `cuarentena/` con manifiesto SHA-256. |
| Datos sintéticos, `random`, `seed` como datos de mercado | Doctrina REAL-ONLY. Es la violación más grave. |
| Fallbacks complacientes (valor por defecto cuando falta el dato) | Debe salir `NO DATA` / `ERROR`. |
| Escribir en `orchestration/reviews/` | Es territorio exclusivo del Orquestador. |
| Tocar `data/`, `*.sqlite`, credenciales o `.env` sin que la tarea lo pida | Riesgo de corrupción irreversible. |
| Iniciar una fase sin `GO`, o re-hacer una `done` | Rompe el loop. |
| Modificar el motor de gates o Firebase fuera de una fase auditada | Precedente del incidente 2026-08-30. |
| "Arreglar" de paso algo que no es de tu fase | Contamina la auditoría. Va al informe como hallazgo. |

---

## 8. LAS 20 DECISIONES SELLADAS DEL USUARIO

Están en **`orchestration/DOCTRINA_ORQUESTADOR.md §14`**. **Léelas en cada fase.** Si tu trabajo
contradice una de ellas, es `repite` automático. Las que más te van a afectar al ejecutar:

- **#1** Killzones y noticias van en una **capa posterior de optimización**, NUNCA dentro de la
  generación inicial del motor.
- **#5** Objetivo ULTRA: **~100 % mensual**. Es una **meta**, no un permiso para maquillar. Si no
  se alcanza, se reporta la cifra real. Tocar comisiones, slippage o gates para "llegar al número"
  es violación grave.
- **#6** ULTRA: **70 % DD realizado · 80 % DD flotante** (deroga el 75 % de docs viejos).
- **#8** Dimensionamiento **100 % en porcentajes**, agnóstico al capital. Cero cifras absolutas.
- **#9** Todo arranca en **paper/demo**. Ni un euro real sin autorización explícita del usuario.
- **#10** Gestión de cuentas prop **pospuesta**. La prioridad exclusiva es **generar estrategias**.
- **#13** Datos CME/FX a **coste 0 €** con proxies (ver §9).
- **#14** VPS de **4 cores**: todo proceso pesado va con `nice`/`ionice` y cola limitada. Si saturas
  la CPU tumbas la API (:8000) y la web (:3005), y eso cuenta como fallo de la fase.
- **#20** El Orquestador auto-despacha. Tú sigues necesitando su `GO`.

---

## 9. MAPA DEL PROYECTO (dónde está cada cosa de verdad)

### 9.1 Tu loop
| Ruta | Qué es | Quién escribe |
| :--- | :--- | :--- |
| `orchestration/METODOLOGIA_ANTIGRAVITY.md` | **Este archivo.** Tu procedimiento | Hermes |
| `orchestration/DOCTRINA_ORQUESTADOR.md` | Doctrina + §14 decisiones selladas | Hermes |
| `orchestration/state/plan_maestro.md` | Plan v3 completo, 12 fases | Hermes |
| `orchestration/state/current_phase.md` | **Tu tarea actual** | Hermes |
| `orchestration/state/status.json` | Estado de la máquina | Ambos |
| `orchestration/state/GO` / `DONE` | Señales del handshake | Hermes / Tú |
| `orchestration/results/fase_<NN>.log` | **Tus informes** | Tú |
| `orchestration/reviews/` | Veredictos de auditoría | **Solo Hermes** |
| `orchestration/logs/hermes_sync.log` | Latido del cron (cada 5 min) | Cron |
| `cuarentena/` | Destino de todo lo retirado (nunca `rm`) | Quien lo mueva |

### 9.2 El sistema
| Componente | Realidad física verificada | Nota |
| :--- | :--- | :--- |
| **Motor SQX** | `sqcli` headless, **HTTP `:5050`** (`/call?cmd=…`) | **NO** hay GUI. **NO** hay MCP en 8080 (docs viejos mienten). |
| **API** | FastAPI `:8000` (`ultrarentable-api.service`) | |
| **Web** | Next.js **`:3005`** (no 3000, pese a lo que digan los docs) | |
| **BD canónica** | `~/.local/state/ultrarentable/ultrarentable.sqlite3` | |
| **Evidencias** | `data/evidence/<strategy_id>/gate_*.json` | 11 gates por estrategia |
| **SSOT documental** | `docs/00_MASTER_IDEAS_Y_PLAN.md` | Manda sobre cualquier otro doc |
| **VPS** | 4 cores · 23 GB RAM · ~38 GB libres | Recurso escaso: respétalo |

### 9.3 Datos (verificado por Hermes el 2026-08-31 con descarga real)
- **Cripto:** Binance Vision (`data.binance.vision`), M1 real desde ~2018. Ya en uso.
- **Proxies CME/FX a 0 €:** datafeed público de Dukascopy, **sin API key**:
  `https://datafeed.dukascopy.com/datafeed/{SYM}/{YYYY}/{MM0}/{DD}/{HH}h_ticks.bi5`
  - ⚠️ **`MM0` es el mes 0-INDEXADO** (`06` = julio). Este detalle se equivoca siempre; no lo asumas.
  - Formato: LZMA → registros de 20 bytes `>3I2f` = (ms desde la hora, ask, bid, askVol, bidVol).
  - Prueba real: `USA500IDXUSD 2026-07-15 14h` → 12.455 ticks, ask 7570.748 / bid 7570.226.
  - Hora sin ticks → fichero de **0 bytes**. Eso es un **hueco legítimo**, se registra. **No se rellena.**
  - ✅ **SÍ hay volumen** (verificado con 48 h reales de `USA500IDXUSD`: 100 % de las barras con
    volumen > 0, media 49 ticks/barra, spread medio 0,50 pts). Es volumen de tick del broker, **no
    volumen del contrato CME**: sirve para descubrir, pero la portabilidad al futuro real se valida
    en el control proxy↔CME. Marca `VOLUMEN_PROXY` las estrategias que dependan fuerte de él.
  - Mapa: `USA500IDXUSD`→ES/MES · `USATECHIDXUSD`→NQ/MNQ · `USA30IDXUSD`→YM/MYM ·
    `XAUUSD`→GC/MGC · `XAGUSD`→SI · `LIGHTCMDUSD`→CL/MCL.

### 9.4 Universo canónico (mandato sellado, no negociable)
- **ULTRA no es solo cripto ni solo 4H conservador.** Opera **todos** los activos.
- **5 temporalidades en todos los activos:** `1m`, `5m`, `15m`, `1h`, `4h`.
- **SOLO INTRADÍA.** Cero exposición overnight/fin de semana.

---

## 10. CHECKLIST ANTES DE ESCRIBIR `DONE`

Si respondes "no" a cualquiera, **no publiques `DONE` todavía**:

- [ ] ¿He leído `current_phase.md` entero y he cumplido **todos** sus criterios de éxito?
- [ ] ¿Cada `[x]` de mi checklist tiene un comando real que lo demuestra en la §3 del informe?
- [ ] ¿He pegado la salida **cruda** de los comandos, sin resumirla ni retocarla?
- [ ] ¿Mi `git status --short` coincide exactamente con lo que declaro en la §4?
- [ ] Si la fase era solo-lectura: ¿`git status` sale limpio de verdad?
- [ ] ¿He marcado como "decisión propia" todo lo que decidí yo?
- [ ] ¿He escrito `NO DATA` / `ERROR` en cada punto donde no pude verificar, en vez de rellenar?
- [ ] ¿Hay alguna cifra en mi informe que no pueda respaldar con un comando? → **quítala**
- [ ] ¿He hecho `git commit`, `git push` o `rm`? → si sí, **repórtalo inmediatamente**, es grave
- [ ] ¿Tiene el informe la tabla de reparto multi-agente?
- [ ] ¿He actualizado `status.json` a `done` con `last_updated` en UTC?
- [ ] ¿El `report_sha256` del `DONE` corresponde al informe **final** (no a una versión anterior)?

---

## 11. SI TE ATASCAS

1. **Tres intentos fallidos del mismo comando ⇒ para.** No pruebes variaciones a ciegas.
2. Diagnostica: lee el error real completo, mira los logs físicos, contrasta con la realidad del §9.2.
3. Replantea con causa raíz identificada.
4. Si sigue bloqueado: **escríbelo en el informe** (§7 "lo que no se pudo hacer") con el error
   literal, publica `DONE` con lo que sí lograste, y deja que el Orquestador decida.

**Entregar una fase parcial y honesta es un resultado válido. Entregar una fase "completa"
con relleno inventado es el único fallo imperdonable de este proyecto.**
