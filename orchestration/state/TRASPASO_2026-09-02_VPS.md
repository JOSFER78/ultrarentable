# TRASPASO — estado para continuar en una sesión nueva (2026-09-02, 18:30 UTC, desde el VPS)

Este documento sucede a `TRASPASO_CLAUDE_CODE_2026-09-02.md`, que escribió el agente anterior
desde el PC de Emilio. Aquel sigue siendo válido para todo lo que cuenta del PC (worktrees, ramas
`agy-*`, WIP sin auditar); **este añade lo hecho después en el VPS y corrige lo que ya no aplica**.
Léelos en ese orden: primero éste, y el anterior cuando necesites el detalle del PC.

---

## 0. Lo primero que tiene que hacer quien entre

1. **Sincronizar antes de opinar.** El trabajo viaja entre el PC de Emilio y este VPS a través de
   `origin/main`. El checkout local puede estar decenas de commits por detrás; ya pasó el 02-09
   (111 commits de diferencia) y llevó a concluir en falso que "no había trabajo previo".
   ```bash
   cd "/home/ubuntu/workspace/pro/trading/01 Ultrarentable"
   git fetch origin main && git log --oneline HEAD..origin/main | head -20
   ```
2. **Inventario de carga del VPS** (regla sellada: estabilizar antes de producir).
   ```bash
   uptime; free -h; ps aux --sort=-%cpu | head -8
   .venv/bin/python -m services.ops.gobernanza_recursos estado
   ```
3. Leer, en este orden: este fichero → `orchestration/state/current_phase.md` →
   `orchestration/state/plan_maestro.md` → el bloque de la fase en la que vayas a trabajar.

---

## 1. Dónde está cada cosa

| Qué | Dónde |
| :--- | :--- |
| **Plan maestro (índice de fases)** | `orchestration/state/plan_maestro.md` |
| **Cada fase, en su propio fichero (fuente de verdad)** | `orchestration/state/plan/bloques/Fxx_*.md`, con frontmatter YAML (`estado`, `aparcado`, `depende_de`…). Al avanzar una fase se edita SU bloque y se refleja la fila del índice. Nunca se reescribe el plan entero ni se crean planes paralelos; lo sustituido va a `orchestration/state/archive/` |
| **Foto del ciclo actual** | `orchestration/state/current_phase.md` |
| **Reglas invariantes** | `orchestration/state/plan/bloques/REGLAS_INVARIANTES.md` |
| **Decisiones que esperan a Emilio** | `orchestration/state/VENTANA_EMILIO.md` (issue #22) |
| **Traspaso anterior (detalle del PC)** | `orchestration/state/TRASPASO_CLAUDE_CODE_2026-09-02.md` |
| **Operación del VPS (SSOT de carga)** | `orchestration/OPERACION_VPS.md` — **leer antes de lanzar nada** |
| **Operación de la web local del PC** | `orchestration/OPERACION_WEB_LOCAL.md` |
| **Operación de agentes agy/Orca** | `orchestration/OPERACION_AGENTES.md` (carril retirado, ver §5) |
| **Motor de backtest** | `services/validation/engine/event_backtest_engine.py`; versión en `services/engine_version.py` (**5.18.0**) |
| **Minería gobernada** | `scripts/cola_mineria.py` sobre `services/queue/durable_job_queue.py`; campaña directa: `scripts/mine.py` |
| **Gobernanza de recursos** | `services/ops/gobernanza_recursos.py` (funciona en Linux; el traspaso anterior lo describía sólo para Windows) |
| **Telemetría de campañas** | `orchestration/results/telemetria/` |
| **Datasets** | `data/normalized/*.json` + su manifiesto. El conteo válido es el de disco, no el de la BD |
| **BD canónica** | `services/api/app/config.py::STATE_DB_PATH` (fuera del repo) |

---

## 2. Situación real, sin adornos

**Estrategias FONDEO certificadas: 0. Meta-estrategias: 0.** No ha cambiado. Lo que sí ha
cambiado hoy es que por fin hay una medición limpia de POR QUÉ.

### Campaña E2 (bloque B03), ES 5 minutos — TERMINADA el 02-09 a las 18:08 UTC

Evidencia: `orchestration/results/telemetria/embudo_FONDEO_ES_5m_arquetipos_20260902T180821Z.json`

```
motor 5.18.0 · 420 configuraciones · espacio completo (truncado = False)
familias: REVERSION_ATR 108 · SQUEEZE_BREAKOUT 96 · SESSION_MOMENTUM 72
          STREAK_EDGE 72 · OPENING_RANGE_BREAKOUT 36 · VWAP_REVERSION 36
resultado: 0 certificadas 11/11 · las 420 mueren ya en IS
causas:    sin ventaja BRUTA 400 · sin ventaja SOLO por coste 20 · pocas operaciones 0
```

**Lectura, y es importante para decidir el siguiente paso:** la narrativa de que a FONDEO le
faltaban barras u operaciones queda **descartada por los datos** — ninguna configuración murió por
operar poco. 400 de 420 no tienen ventaja ni antes de pagar costes. Las 20 excepciones son todas de
`SESSION_MOMENTUM`: sí tenían ventaja bruta y se la comió la fricción. Ese es el único hilo del que
tirar en esta familia (menos operaciones, marco temporal mayor, filtros de sesión), y es justo lo
que mide la campaña de 15 minutos.

### Campaña E2, ES 15 minutos — EN CURSO

Lanzada 18:15 UTC, mismas 420 configuraciones y 6 familias, IS=50.026 / Val=16.675 / OOS=16.676
barras. Salida en `orchestration/results/telemetria/B03_E2_15m.stdout.txt`; al terminar escribe su
propio `embudo_FONDEO_ES_15m_arquetipos_*.json`.

```bash
tail -5 orchestration/results/telemetria/B03_E2_15m.stdout.txt
pgrep -af "mine.py --track fondeo --symbol ES --tf 15m" || echo "terminada"
```

Se lanzó desacoplada (`setsid nohup`) bajo gobernanza, así que **sobrevive al cierre de la sesión**:
no hay que relanzarla si la conversación se corta.

---

## 3. Lo hecho hoy en el VPS (commits en `main`)

| Commit | Qué |
| :--- | :--- |
| `5d824f63f` | La web ya no se sirve con `next dev`. `ultrarentable-web.service` (systemd `--user`) ejecuta `/home/ubuntu/ultra-web-wrapper.sh`, que compila sólo si falta `.next/BUILD_ID` y arranca `next start -p 3005`. El wrapper viejo está en `cuarentena/web_wrapper_2026-09-02/` con SHA-256 |
| `568dcf723` | Evidencia de la autorreparación del discovery (28 h atascado por estrangulación del cgroup) |
| pendiente de commit | `apps/web/lib/firebase.ts` (comentario de cabecera) y la telemetría de E2 |

### Firebase: la causa real de que el login no funcionase

La web mezclaba **dos proyectos**: autenticación en `goalskid-app` y base de datos en `pecemi`. Eso
no puede funcionar: un ID token emitido por un proyecto no vale como `auth` en las reglas de la base
de datos de otro, y además `pecemi` no tenía ninguna regla para la rama `ultrarentable` (todo
denegado). El popup de Google podía abrirse, pero el perfil nunca se leía ni se guardaba.

**Configuración actual, ya aplicada en la cuenta de Emilio** (proyecto **02 ULTRAFONDEO**,
`traderbot-josfer`, número 358873317228):

- Proveedor Google: habilitado.
- Dominios autorizados: `localhost`, `127.0.0.1`, `traderbot-josfer.firebaseapp.com`,
  `traderbot-josfer.web.app`, `ultrafondeo.web.app`, `143.47.35.167`, `143-47-35-167.sslip.io`.
- Realtime Database `traderbot-josfer-default-rtdb` con reglas publicadas para
  `ultrarentable/users`: cada usuario lee y escribe **sólo su ficha**;
  `josferestudio@gmail.com` es superadministrador (lee todas y autoriza); un usuario no puede
  subirse a sí mismo los privilegios (`is_superadmin`, `is_authorized`, `status=AUTHORIZED`,
  `role=superadmin` sólo los concede el superadmin).
- `apps/web/.env.local` (fuera de git) con las 7 variables `NEXT_PUBLIC_FIREBASE_*` de ese
  proyecto. Copia de la configuración anterior en el scratchpad de la sesión.
- `apps/web/lib/firebase.ts` **no tiene valores por defecto**: si falta una variable, error
  explícito (doctrina REAL-ONLY). La inicialización es perezosa para que `next build` no dependa
  de que existan las claves.
- Verificación: `grep -rho "traderbot-josfer" apps/web/.next/static | sort -u` y, en el navegador,
  el chunk de `/login` debe contener `traderbot-josfer.firebaseapp.com`.

**El Super Admin forjado ya no existe** (lo quitó el agente anterior en `68bc6ddf9`; comprobado que
no queda rastro de `josfer_superadmin_master_01` en el bundle). La primera vez que Emilio entre con
Google se creará su ficha real y quedará como superadmin por email.

---

## 4. Cómo se arranca y se comprueba cada pieza (VPS)

```bash
cd "/home/ubuntu/workspace/pro/trading/01 Ultrarentable"

# Web (build de producción; NUNCA next dev)
systemctl --user status ultrarentable-web.service      # sirve :3005
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3005/login

# Web en el puerto del túnel del PC de Emilio (él entra por http://localhost:3000)
cd apps/web && setsid nohup node node_modules/.bin/next start -p 3000 -H 0.0.0.0 >/tmp/web3000.log 2>&1 &

# API FastAPI
systemctl is-active ultrarentable-api.service          # :8000

# Campaña de minería, desacoplada y bajo gobernanza
setsid nohup .venv/bin/python -m services.ops.gobernanza_recursos ejecutar --nombre <NOMBRE> -- \
  .venv/bin/python scripts/mine.py --track fondeo --symbol ES --tf 15m --profile arquetipos \
  --dataset-source dukascopy > orchestration/results/telemetria/<NOMBRE>.stdout.txt 2>&1 &
```

Detalles que cuestan un diagnóstico si no se saben:

- **`next dev` y `next build` comparten `.next`.** Compilar con el servidor de desarrollo vivo
  corrompe `app-paths-manifest.json` (se queda con 4 rutas de 44) y deja media web en 404. Parar el
  servicio ANTES de compilar.
- **nginx publica el 3005** en `http://143.47.35.167/pro/ultrarentable/`, pero manda `/_next/…` a
  otra aplicación (puerto 20128), así que por esa ruta la web sale sin estilos ni JavaScript.
  Arreglarlo exige tocar `/etc/nginx/sites-enabled/pro` con sudo (lo hace Emilio). Mientras tanto,
  la vía buena es el túnel: `http://localhost:3000` desde su PC, que además es dominio autorizado
  en Firebase.
- **Comandos compuestos largos fallan** en esta sesión con `exit 144` sin dejar log. Los pasos
  pesados (parar servicio, mover `.next`, compilar) hay que darlos **uno por comando**.

---

## 5. Qué queda por hacer, en orden

1. **Cerrar E2**: cuando termine la campaña de 15 minutos, leer su embudo y escribir el informe de
   B03 comparando 5m contra 15m, con el foco en si `SESSION_MOMENTUM` sobrevive a la fricción al
   bajar la frecuencia. Cifras sólo desde los JSON de telemetría.
2. **B04 — refutador forense** (issue #24): auditoría independiente de la lectura de E1/E2 antes de
   declarar AGOTADAS las familias de `arquetipos`. Si se confirma que están agotadas, el plan salta
   a **W3.4: diseño de familias nuevas**, que pasa a ser el trabajo principal de FONDEO.
3. **FONDEO**: campaña TRADFI sobre los 184 datasets aprobados con el motor 5.18.0 y censo del
   criterio 1.1 (SELLADO: ≥200 trades OOS, PF OOS ≥1,25, OOS/IS ≥0,5, 11 gates con evidencia, DSR+,
   persistencia por mitades). Exámenes de prop firm (F07) en paper/demo primero.
4. **META-FONDEO** (`services/meta`, bloque B08) sobre las certificadas: necesita ≥2, así que hoy
   está bloqueado por el punto 3.
5. **Web**: siguiente mejora de `/estrategias`, sección por sección contra `docs/19_UI_STYLE_SPEC.md`
   y el mandato de Emilio (sobria, sin paneles ni colorines). La versión anterior está en
   `cuarentena/web_estrategias_v1_20260902/`.
6. **VPS**: cuando Emilio autorice, limpieza y vigía V0 (`deploy/vigia/INSTALAR.md`, bloque B12).

**Descartado, no lo retomes:** el carril Orca/agy (agentes Gemini). Está retirado, igual que
Antigravity. Los bloques B20 (`agy_cerrar.sh` roto) y B22 (vigilante) sólo tienen sentido si se
vuelve a él; el aviso de que `agy_cerrar.sh` está roto ya está puesto en `OPERACION_AGENTES.md`, que
era lo único imprescindible. **ULTRA y META-ULTRA siguen aparcados** (estado congelado en
`PUNTO_GUARDADO_ULTRA.md`); el mandato vigente es 100 % FONDEO.

---

## 6. Estado de la máquina y decisiones que dependen de Emilio

El VPS tiene 4 núcleos, ~23 GB de RAM y 4 GB de swap, y además sirve la API, la web y SQX. Hoy llegó
a **carga 88 con la swap al 100 %** por tener **dos** procesos de discovery a la vez; matando el
duplicado la carga bajó a 2,5 y la web pasó a responder en 5 ms. Vigilar que no vuelvan a
solaparse.

Sigue vivo y consumiendo: `sqx.service` (`sqcli`, ~4 GB de RAM),
`ultrarentable-discovery.service` y el backfill de Dukascopy (I/O, poca CPU).

Esperan decisión de Emilio (`VENTANA_EMILIO.md`, issue #22):

1. Limpieza del VPS — requiere sudo, sólo puede él:
   ```bash
   sudo systemctl stop ultrarentable-discovery.service sqx.service
   ```
   y cortar el cron `improve_cycle.sh` (minuto :40), que revive el bucle de SQX cada 20-30 min.
   Ojo: parar el proceso no basta si no se cortan las tres vías (proceso, unidad `enabled`, cron).
2. Arreglar la ruta de nginx `/pro/ultrarentable/` (ver §4).
3. Licencia de StrategyQuant (la prueba caduca el 05-09-2026).
4. Carril SQX: apartado tras tres rondas de B06 (build de 30 min, 19.924 candidatos, **0** aceptados
   bajo criterio 1.1, coherente con E1). No retomar salvo que él lo pida.

---

## 7. Reglas que mandan (selladas, no se negocian)

- **REAL-ONLY / zero-mocks**: nada sintético, ninguna cifra que no salga de un comando y su salida
  cruda; evidencia en disco con SHA-256; donde falte el dato se escribe `NO DATA`, nunca un valor
  inventado.
- **Criterio 1.1 SELLADO**, no se relaja nunca: ≥200 trades OOS, PF OOS ≥1,25, OOS/IS ≥0,5, 11 gates
  con evidencia, DSR+, persistencia por mitades OOS.
- **Regla #26**: todo cambio que altere las operaciones del motor sube `CURRENT_ENGINE_VERSION`; las
  certificaciones con motor viejo pasan a LEGACY y **nunca** se borran.
- **Nunca `rm`**: todo va a `cuarentena/` con manifiesto SHA-256 y motivo.
- **Carga**: un solo proceso pesado a la vez, vía `gobernanza_recursos`, con `nice -n 19` /
  `ionice -c 3`. Cuentan como pesados las campañas, los backfills, los builds y también los `pytest`
  y verificaciones que lancen los subagentes. La web, siempre en build de producción. Si la máquina
  ya está saturada, se reporta y se espera; no se apila trabajo encima.
- **Git**: push a `main` autorizado expresamente por Emilio en este repo. Commits temáticos y
  descriptivos con el trailer de Claude; nunca árboles incoherentes.
- **Comunicación con Emilio**: en español, **breve y en lenguaje llano**. Qué se ha hecho, si
  funciona y qué falta. El detalle técnico, a los documentos del proyecto, no al mensaje.
