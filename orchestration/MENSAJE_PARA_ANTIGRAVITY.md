# Mensaje para pegar en Antigravity

> Copia y pega el bloque de abajo tal cual en Antigravity. No hace falta añadir nada más:
> todo el contexto que necesita está en los archivos que le indica.

---

```
Trabajas en el proyecto Ultrarentable (/home/ubuntu/workspace/pro/trading/01 Ultrarentable).

ANTES DE HACER NADA, lee entero este archivo:

    orchestration/METODOLOGIA_ANTIGRAVITY.md

Es tu procedimiento operativo completo y sustituye a cualquier instrucción anterior que
tengas sobre este proyecto. Léelo de principio a fin, sin saltarte secciones.

Después lee, en este orden:
    1. orchestration/DOCTRINA_ORQUESTADOR.md   (sobre todo la §14: las 20 decisiones que el
                                                usuario ha sellado y que NO son negociables)
    2. orchestration/state/plan_maestro.md      (plan v3 completo, 12 fases)
    3. orchestration/state/current_phase.md     (tu tarea concreta ahora mismo)

Tu tarea actual es la FASE 0: auditoría forense, SOLO LECTURA, del changeset
23c8733a9..245009fef (4 commits, 258 archivos) que ejecutaste fuera del loop entre el
2026-08-30 y el 2026-08-31, tocando el motor de gates de certificación y la autenticación.
El GO ya está publicado.

Arranque obligatorio:

    cd "/home/ubuntu/workspace/pro/trading/01 Ultrarentable"
    cat orchestration/state/GO
    sha256sum orchestration/state/current_phase.md

El sha256 tiene que coincidir con el task_sha256 del GO. Si coincide: borra el fichero GO,
marca status="in_progress" en orchestration/state/status.json y empieza. Si no coincide:
NO empieces, espera y vuelve a comprobar.

Cuatro cosas que te van a hacer repetir la fase, para que las tengas presentes:

1. SI NO LO SABES, ESCRIBE "NO DATA". Nunca lo inventes. Un solo dato inventado invalida
   el informe entero. Entregar menos y verdadero es mejor que entregar más e inventado.

2. Es una fase de SOLO LECTURA. Cero ediciones, cero arreglos "de paso", cero git commit,
   cero rm. Si ves algo que hay que arreglar, va al informe como hallazgo y no lo tocas.

3. MULTI-AGENTE OBLIGATORIO: mínimo 3 subagentes en paralelo (A1 scripts de minería,
   A2 motor de gates y tests, A3 censo de evidencias en disco). El informe debe llevar la
   tabla de qué subagente hizo qué.

4. El informe va en orchestration/results/fase_00.log con el formato de 9 secciones que
   define la metodología. Cada [x] de tu checklist tiene que apuntar al comando real que lo
   demuestra, con su salida cruda pegada. Un [x] sin comando que lo respalde se trata como
   invención.

Aviso: el Orquestador (Hermes) está trabajando EN PARALELO en docs/ y en la ingesta de
datos (services/data_ingestion/, data/). Por eso `git status` te va a mostrar cambios que
no son tuyos. Para demostrar que respetaste el solo-lectura, usa el comando acotado a tu
territorio que viene en current_phase.md. No toques docs/, data/ ni services/data_ingestion/.

Cuando termines de verdad: informe escrito, status="done", y creas el fichero
orchestration/state/DONE con phase=0 y report_sha256=<sha256 del informe>. Hermes lo detecta
en 5 minutos, audita re-ejecutando tus comandos por su cuenta, y publica la siguiente fase.
```

---

## Qué pasa después (no hace falta que se lo digas)

El cron `hermes_sync.sh` comprueba el estado cada 5 minutos y solo despierta a Hermes cuando
hay trabajo real: `DONE` presente, o Antigravity colgado, o `GO` sin arrancar. Hermes audita
re-ejecutando los comandos por su cuenta, escribe el veredicto en `orchestration/reviews/`
y publica automáticamente la siguiente fase con su `GO` (autonomía total, decisión #20).

El usuario no tiene que intervenir salvo que quiera parar el loop o cambiar una decisión.
