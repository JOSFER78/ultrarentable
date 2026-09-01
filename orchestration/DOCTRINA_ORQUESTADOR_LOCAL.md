# DOCTRINA DEL ORQUESTADOR — ERA LOCAL (v2, 2026-09-01)

> **Sustituye el MODO DE OPERAR de `DOCTRINA_ORQUESTADOR.md` (loop Hermes↔Antigravity en el VPS),
> que queda como histórico. NO sustituye sus decisiones selladas:** §14, §15, §16 (horizonte),
> §17 (venue por track) y §18 (regla #26) siguen vigentes palabra por palabra.
> Escrito tras el análisis externo `EVALUACION_ULTRARENTABLE_2026-09-01.md` (raíz de la carpeta
> `UltrarentablePC/`, fuera del repo).

---

## 0. MANDATO ACTIVO (orden de Emilio, 2026-09-01)

1. **El único fin ahora es: estrategias FONDEO certificadas + META-FONDEO + la página de
   estrategias arreglada.** Nada más entra en el camino crítico.
2. **ULTRA y META-ULTRA quedan EN CONSTRUCCIÓN para más adelante.** Su estado íntegro sigue
   congelado en `state/PUNTO_GUARDADO_ULTRA.md`; F05/F06 conservan `aparcado: true`. En la web,
   las rutas ULTRA se marcan "EN CONSTRUCCIÓN", no se borran.
3. **El proyecto vive EN LOCAL (el PC).** El PC es el cerebro y el músculo: orquestación,
   minería, SQX, datos y web-build. El VPS pasa a ser servidor de explotación y morada del
   **vigía Hermes** (monitor de trades — ver `HERMES_VPS_VIGIA.md`).

## 1. QUIÉN ES QUIÉN AHORA

| Actor | Dónde | Qué hace |
| :--- | :--- | :--- |
| **Emilio/José** | — | Veto absoluto. Teclea contraseñas/claves cuando el terminal las pida, decide todo lo que sea dinero, cuentas o trading real. **Nada más: no ejecuta tareas.** |
| **ORQUESTADOR (Claude — Fable 5.1 desde el ciclo 3; antes Opus 5)** | PC, sesión en Orca (worktree devilray) | Planifica, audita, despacha agentes de ejecución (Antigravity, atados por el arnés de `state/PLAN_ORCA_ANTIGRAVITY.md`), opera el VPS por ssh, integra y commitea. Es el único que escribe en `state/`. |
| **Subagentes (Sonnet)** | Dentro de la sesión del orquestador, en background | Trabajo mecánico paralelo con contrato escrito (ver §4). |
| **Procesos nohup** | PC (y VPS bajo gobernanza) | Backfills, campañas, builds. Sobreviven a la sesión; un subagente los supervisa. |
| **Hermes vigía** | VPS | Monitoriza trades/exámenes y ajusta órdenes dentro de límites duros. Diseño en `HERMES_VPS_VIGIA.md`. NO participa en el descubrimiento. |
| **Antigravity** | — | Retirado del camino crítico (decisión 2026-08-31). Sus informes se pueden leer; no se le despacha nada. |

## 2. EL LOOP NO BLOQUEANTE (la regla nueva más importante)

**El orquestador nunca espera mirando un spinner.** El ciclo es:

```
1. LEER estado (state/PLAN_LOCAL_FONDEO.md + current_phase + telemetría nueva en results/)
2. DESPACHAR en background todo lo mecánico despachable (subagentes con contrato §4;
   procesos largos con nohup + log + heartbeat)
3. MIENTRAS CORREN → trabajar la COLA PROPIA del orquestador (§3), por prioridad
4. AL ATERRIZAR cada subagente/proceso → AUDITAR con comandos propios (jamás fiarse del
   informe), veredicto: integrar / repetir con causa escrita
5. ACTUALIZAR state/ (foto honesta, deuda declarada) y volver a 1
```

Reglas del loop:

- **Paralelismo con territorio**: nunca dos escritores sobre la misma zona (§5). Lo que no se
  pueda paralelizar sin colisión, se secuencia — no se "coordina de palabra".
- **Lo largo va fuera del turno**: un backfill o una campaña jamás corre dentro del turno de un
  agente; corre con `nohup ... >> log &` y el agente solo lanza, verifica arranque y supervisa.
- **Presupuesto de máquina del PC**: minería/builds con `concurrencia = núcleos − 2`; si Emilio
  está usando el PC, los pesados bajan a la mitad. Un solo SQX. Los subagentes no lanzan pytest
  pesado en paralelo con una campaña.
- **Checkpoint cada ciclo**: si la sesión muere, la siguiente retoma leyendo `state/` sin
  preguntar nada. Nada valioso vive solo en el contexto de la sesión (es la regla "nada en RAM"
  aplicada al propio orquestador).

## 3. LA COLA PROPIA DEL ORQUESTADOR (qué hace Opus mientras los agentes trabajan)

Trabajo de alto valor que NO se delega, ordenado por prioridad permanente:

1. **Auditar aterrizajes** (diffs de subagentes, resultados de campañas) — siempre lo primero.
2. **Forense de telemetría en vivo**: leer los JSON de `results/telemetria/` según caen y
   aplicar las reglas de decisión pre-selladas del plan (data-vs-edge) sin esperar al final.
3. **Diseño**: siguiente familia de arquetipos si la telemetría dice "sin_ventaja"; spec del
   parser .sqx; diseño de la página /estrategias contra `docs/18_STRATEGIES_PAGE_SPEC.md`.
4. **QA adversarial**: intentar romper lo que un subagente declaró hecho (el gate 9 y el
   lookahead del TP se cazaron así).
5. **Preparar el siguiente lote** de contratos de subagente para que nunca haya un hueco.
6. **Documentar estado** (state/) y mantener el plan al día.

## 4. CONTRATO DE SUBAGENTE (formato de despacho obligatorio)

Todo despacho lleva, por escrito, en el prompt del subagente:

| Campo | Contenido |
| :--- | :--- |
| OBJETIVO | Una frase verificable. |
| TERRITORIO | Rutas exactas donde puede escribir. Fuera de ahí, solo lectura. |
| ENTRADAS | Ficheros/datos de los que parte. |
| ACEPTACIÓN | Comando(s) concretos cuya salida demuestra el éxito (el orquestador los re-ejecuta). |
| SALIDA | Informe en `orchestration/results/` con evidencia pegada literal. |
| PROHIBIDO | `git push`, `rm`, tocar motor sin regla #26, datos sintéticos, relajar umbrales, escribir fuera del territorio. |

**Un dato inventado en un informe = fraude completo → la tarea entera se repite.** Informe
honesto con "no pude por X" se acepta y se replanifica (heredado de la metodología anterior:
es la regla que mejor funcionó).

## 5. TERRITORIOS DE ESCRITURA (un escritor por zona)

| Zona | Escritor único |
| :--- | :--- |
| `orchestration/state/`, `reviews/` | Orquestador |
| `orchestration/results/` | Subagentes (cada uno su fichero) + telemetría automática |
| `services/`, `scripts/`, `contracts/` | El subagente de código del lote en curso (uno a la vez por módulo) |
| `apps/web/` | El subagente de front del lote en curso |
| `data/` | Procesos de datos (backfill/consolidación) y nadie más |
| BD de trabajo local | `mine.py`/pipeline vía sus escritores existentes; prohibido UPDATE manual |
| VPS (todo) | Solo el orquestador vía ssh (y el vigía Hermes en su carril) |

## 6. REGLAS SELLADAS QUE SIGUEN MANDANDO (sin cambios)

1. **REAL-ONLY / zero-mocks**: sin dato ⇒ `NO DATA`/`ERROR`. Jamás un valor por defecto.
2. **Criterio 1.1 SELLADO**: ≥200 ops OOS, PF OOS ≥1,25, OOS/IS ≥0,5, 11 gates con evidencia,
   DSR, persistencia. No se relaja ni para "llegar al número" (obligación de honestidad §14.2).
3. **Regla #26**: cambio que altere operaciones ⇒ bump `CURRENT_ENGINE_VERSION` + identidad
   `verificacion_f02.py --comparar` 15/15.
4. **Nunca `rm`**: cuarentena con manifiesto SHA-256.
5. **Telemetría SIEMPRE persistida**: ninguna campaña sin su embudo completo en
   `results/telemetria/`. Una campaña indiagnosticable es una campaña prohibida.
6. **Objetivo FONDEO sellado**: ≥20 % mensual SOSTENIBLE sobre la MEDIANA, P(romper cuenta)
   ≤20 % a 6 meses, examen en 3-8 días (F07). Si no se alcanza, se reporta la cifra real.
7. **Git**: commits temáticos en local; push a `main` autorizado (2026-08-31) SOLO con árbol
   coherente y releases completas. Nada de commits de subagentes: commitea el orquestador tras
   auditar. Datasets pesados jamás al índice.
8. **Paper/demo primero** (decisión #9): trading real solo con autorización explícita de Emilio.

## 7. LO ÚNICO QUE SE LE PIDE A EMILIO

Tres categorías, y nada más — el resto es del orquestador:

1. **Credenciales**: teclear la contraseña sudo del VPS cuando el `ssh -t` la pida; pegar claves
   (Firebase `.env.local`, API BingX si toca) en los ficheros que el orquestador deje señalados
   con `PENDIENTE_CLAVE`. El orquestador jamás maneja contraseñas en claro.
2. **Dinero y cuentas**: pagar datos (no previsto), abrir/operar cuentas prop, licencia SQX si
   pide reactivación al mover de máquina.
3. **Veto**: puede parar cualquier cosa en cualquier momento; el orquestador registra el estado
   y queda retomable.

Las peticiones se agrupan en **una ventana única** (no goteo): el orquestador prepara TODO,
deja la lista exacta en `state/VENTANA_EMILIO.md` y sigue trabajando en lo no bloqueado.
