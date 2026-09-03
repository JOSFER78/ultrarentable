# VENTANA EMILIO — lo único que necesito de ti (abierta 2026-09-01; actualizada 2026-09-02, ciclo 3)

> **Estado del ciclo 3 (orquestador Fable 5.1 en Orca, 2026-09-02):** los ciclos 1-2 están
> commiteados en `main`; el arnés de los agentes está activo y **probado en la rama real de un
> agente** (un agente de humo encontró que el arnés original no ataba nada y se corrigió: lista
> blanca `ORQ_COMMIT=1`, hooks fuera de los worktrees). La **Ola A** se despacha con hasta 10
> agentes en vuelo (9 `agy` + el refutador A02 en `codex`), cada uno en su worktree `agy-<ID>`,
> con su contrato `orchestration/agy/GO_<ID>.md`. Dónde mirar: Panel de agentes y Tareas de
> Orca; informes en `orchestration/results/agy/`. **Nada de lo de abajo ha cambiado: sigue
> siendo lo único que necesito de ti, y la licencia SQX caduca en 3 días.**

> Regla de la casa: **una sola ventana, no goteo.** Todo lo que sigue está preparado para que te
> cueste minutos. Mientras tanto sigo trabajando en todo lo que NO depende de ti, que es la mayor
> parte. Tú tienes veto absoluto: escribe "PARA" y todo queda registrado y retomable.
>
> **Buenas noticias antes de la lista**: tres cosas que el plan daba por necesarias resultaron NO
> serlo. Las verifiqué una a una y te ahorran trabajo (§4).

---

## 0. NUEVO 2026-09-02 (noche) — cinco cosas, en orden de urgencia

**0.1 Autorizar el censo del criterio 1.1 en la base del VPS (1 minuto).** Las 5 estrategias que la web
enseña como "aprobadas con motor vigente" son ULTRA, con motor 5.13.0/5.16.0 (el vigente es 5.18.0) y
25-68 operaciones fuera de muestra (el criterio exige ≥ 200). El censo en seco (`scripts/censo_f01.py`,
19:41 UTC) confirma: 728 candidatas, 0 supervivientes, exactamente esas 5 reclasificables a
`LEGACY_NO_CERTIFICADO` (nada se borra; queda rastro en `audit_events`). Mi guardián bloqueó la escritura
en la base canónica. Opción A: me escribes "autorizado el censo" y lo aplico. Opción B: lo pegas tú:
```bash
ssh oracle-vps
cd "/home/ubuntu/workspace/pro/trading/01 Ultrarentable"
.venv/bin/python scripts/censo_f01.py --aplicar --out orchestration/results/censo_f01_2026-09-02_vps.md
```
Después la web dirá "0 estrategias listas", que es la verdad de hoy.

**0.2 El VPS está saturado por herramientas tuyas, no del proyecto (medido 19:36-19:38 UTC):** carga 13 sobre
4 núcleos y swap con 63 MB libres de 4 GB. Lo que consume: el agente Hermes (`hermes serve`, `tirith`,
`fetch_cloud.py` de Hetzner), un Chromium de Playwright bajo `node dist/api.js`, un Brave headless con
depuración remota, `cleanlinux_gui.py`/`cleanlinux-daemon.py`, y cuatro procesos `agy` zombis colgando de
`antigravity_bridge.py`. Yo no mato nada que no sea mío. Mientras eso siga, la gobernanza no admite ni el
build de la web ni campañas en el VPS. Si vas a cambiar de servidor (vi Hetzner en tus pestañas), este
inventario te sirve para dimensionar: el proyecto solo necesita API + web + una campaña a la vez.

**0.3 Dos sesiones de Claude Code editan el mismo checkout de `main` en tu PC** (esta y `ultrarentablepc-30`).
Nos hemos repartido ficheros por mensaje, pero cada instrucción tuya sobre la web conviene dársela a una sola
sesión. Propuesta: portada y `/estrategias` = esta sesión; menú lateral, resto de páginas y `lib/` = la otra.

**0.4 Identidad git del VPS.** Los commits hechos desde el VPS salen como `Hermes User <hermes@localhost>`.
Si quieres que salgan a tu nombre: `git config --global user.name "JOSFER78" && git config --global user.email "josferestudio@gmail.com"` en el VPS.

**0.5 Sigue pendiente lo de abajo** (limpieza del VPS con sudo, nginx, licencia SQX que caduca el 05-09).

---

### 0.6 Quién edita la web (decisión pendiente, 03-09 01:05 UTC)

Tres editores sobre el mismo checkout: tu Antigravity en VS Code, la sesión Claude `ultrarentablepc-12` y la
sesión Claude orquestadora. Propuesta por defecto (ya aplicada hasta que digas otra cosa): mientras trabajes en
VS Code, `apps/web` entero es de Antigravity; la sesión `-12` se queda con `services/api` y verificación de
solo lectura; la orquestadora con `orchestration/` y `services/` (motor). Si prefieres que la web la lleve una
sesión Claude, dilo y Antigravity deja de tocar `apps/web`. Las dos cosas a la vez pierden trabajo.

## 1. LO ÚNICO BLOQUEANTE — autorizar la limpieza del VPS (2 minutos)

**Qué pasa**: el VPS sigue exactamente igual de ahogado que el 2026-09-01 por la mañana, y lo he
medido yo hace un rato por ssh:

```
Mem: 23Gi total · 16Gi usados · swap 4,0Gi de 4,0Gi (60 KiB libres)
load average: 3,22 sobre 4 núcleos
sqcli (StrategyQuant)             58,9 % CPU · 4,5 GB RAM  ← lleva desde las 07:04
discovery_validation_pipeline     13,6 % CPU · 1,6 GB RAM  ← lleva desde las 07:59
memory.events del discovery: high = 7.575.123 frenazos
```

Ese último número es el importante: los 713.626 frenazos que documentaba el informe se han
convertido en **7,5 millones**. La máquina lleva 10 horas estrangulándose a sí misma.

**Lo que NO necesito**: tu contraseña. Lo comprobé — el usuario `ubuntu` del VPS tiene sudo **sin
contraseña** (`sudo -n true` → OK). El plan asumía que hacía falta y no hace falta.

**Lo que SÍ necesito**: permiso. Mi sesión tiene un guardián de seguridad que bloquea ejecutar
`sudo` remoto por ssh, y es correcto que lo bloquee: no voy a saltármelo. Elige una de las dos:

**Opción A (recomendada) — me autorizas y lo hago yo, con evidencia antes/después.**
Dime "autorizado limpiar el VPS" y lo ejecuto. Si tu Claude Code te ofrece añadir una regla de
permiso para `ssh oracle-vps`, acéptala.

**Opción B — lo pegas tú.** Abre un terminal y pega esto tal cual (son los comandos exactos de la
sección A de `orchestration/OPERACION_VPS.md`, sin una coma cambiada):

```bash
ssh oracle-vps
sudo systemctl stop ultrarentable-discovery.service
sudo systemctl disable ultrarentable-discovery.service
sudo systemctl stop sqx.service
pkill -f run_continuous_pipeline
pkill -f discovery_validation_pipeline
crontab -l > ~/crontab_backup_20260901.txt
crontab -e     # comenta la línea del minuto :40 (improve_cycle.sh) poniéndole '#' delante
exit
```

Qué NO toca: `ultrarentable-api.service` sigue vivo (es lo que sirve la web), y tus otros
proyectos del VPS (qwenproxy, Hermes, los crons `matiza_*`, `sync_sanitizer`, `vps_auto_clean`)
**no se tocan** — los he visto y no son míos.

Qué se gana: la máquina deja de estrangularse, la swap empieza a liberarse, y desaparece el
"eslabón 9" que lleva días bloqueando la cadena entera.

---

## 2. CLAVES DE FIREBASE — para arreglar el login de la web (5 minutos)

**Está confirmado leyendo el código**, no es sospecha. `apps/web/lib/firebase.ts` líneas 5-13
mezcla DOS proyectos distintos en la misma configuración:

```
apiKey / authDomain / projectId / storageBucket  →  goalskid-app        (¡otro proyecto tuyo!)
databaseURL                                      →  pecemi-default-rtdb (¡y otro más!)
```

Y **no existe** `apps/web/.env.local`, así que esos valores de emergencia son los que se usan de
verdad. Por eso el login se queda colgado con el watchdog de 6 segundos: está autenticando contra
`goalskid-app` y leyendo la base de datos de `pecemi`.

**Lo que necesito**: las 7 claves del proyecto Firebase que SÍ toca usar (creo que es
`traderbot-josfer`, con el hosting `ultrafondeo`, pero **confírmamelo tú**). Se sacan de la consola
de Firebase → Configuración del proyecto → Tus apps → Configuración del SDK.

Te dejaré el fichero preparado con los huecos marcados `PENDIENTE_CLAVE` en cuanto el agente de web
llegue a ese carril; solo tendrás que pegar los valores. **Yo nunca manejo tus claves en claro.**

Si prefieres, dime solo **cuál es el proyecto correcto** y me encargo del resto de la reparación
(quitar los fallbacks mezclados, que falle con error explícito en vez de en silencio).

---

## 3. ⏳ LICENCIA DE STRATEGYQUANT X — CADUCA EL 2026-09-05, EN 3 DÍAS (decisión de dinero, es tuya)

**Esto ya no es un "puede que sí". Lo he ejecutado yo en tu PC y esta es la salida literal:**

```
StrategyQuant X Pro Build 144 (Trial license) - valid until 05.09.2026, license 46587B
SQX version: 144.2953   ·   Hardware ID: CBC66D20B937
Volume profile subscription verified: active=false
```

**La licencia de SQX en este PC es una PRUEBA que expira el 5 de septiembre de 2026** — dentro de
cuatro días. No es una licencia de pago. (La del VPS, según los propios documentos del repo, ya
había expirado el 18-08-2026, así que no hay un "seat" que liberar: no hay ninguna licencia
comprada en ninguna de las dos máquinas.)

**Por qué importa tanto**: el carril SQX es, según el análisis externo y mi propia lectura, *la
apuesta con más probabilidad de romper el 0 de estrategias certificadas* — generar reglas nuevas
de verdad en lugar de seguir barriendo por fuerza bruta plantillas agotadas. Y tenemos 2.035
estrategias ya generadas esperando. Si la prueba caduca sin decidir nada, ese carril se para.

**Lo que necesito de ti — una decisión, no una tarea:**

| Opción | Qué implica |
| :--- | :--- |
| **A. Comprar licencia** | El nivel "Pro" es el que ya estamos probando y cubre lo que necesitamos (Builder, Optimizer, Improver, Walk-Forward, WF Matrix, Monte Carlo, System Parameter Permutation). **No hace falta "Ultimate"** — lo único que añade y nos tocaría es QuantAnalyzer y el Portfolio Master sin límite, y ninguno está en el camino crítico de FONDEO |
| **B. Exprimir los 4 días** | Te preparo y lanzo los experimentos decisivos ANTES del día 5 (el A/B de configuración del Builder ya está diseñado y costeado: 30-90 min de máquina). Sacamos el máximo de la prueba y decidimos comprar con datos en la mano, no a ciegas |
| **C. No comprar** | El carril SQX se cierra. Habría que apostar todo a diseñar familias de reglas nuevas a mano, que es más lento y con menos probabilidad de encontrar ventaja |

**Mi recomendación: B y luego decidir.** Cuatro días dan de sobra para saber si SQX produce algo
que sobreviva a nuestros 11 gates. Comprar antes de saberlo es comprar a ciegas; dejar caducar sin
probar es tirar la única baza nueva que tenemos. **Dime si autorizas que lance esos experimentos**
y los pongo en marcha (consumen máquina, no dinero).

Dato adicional del inventario, por si pesa en la decisión: el repo daba por hecho que el Builder
era estéril por tener `MaxTradesPerDay = 1`. **Es falso**: el valor real en las tres copias de
configuración es `0` (sin límite). La causa que sí queda confirmada es el desajuste de nombre del
databank (`LastGeneration` sin espacio contra `Last generation` con espacio), que hacía que el
ciclo contara siempre cero. Es decir: el motor probablemente **sí producía** y nadie lo estaba
recogiendo.

---

## 4. Lo que el plan daba por necesario y NO lo es (verificado, te lo ahorras)

| Lo que el plan pedía | Realidad medida hoy | Conclusión |
| :--- | :--- | :--- |
| Tu contraseña sudo del VPS | `sudo -n true` responde OK: es **sin contraseña** | **No hace falta.** Solo el permiso del §1 |
| Configurar el ssh PC→VPS contigo delante (W0.3) | Ya funciona: la clave `id_rsa_openclaw` está puesta y `ssh oracle-vps` entra solo | **HECHO**, sin ti |
| Instalar WSL2 + Ubuntu para poder trabajar | No hay ninguna distro instalada... pero **no hace falta**: el entorno Python 3.11.8 ya está montado y funcionando en Windows nativo (`import services` OK, motor 5.17.0) | **No hace falta.** Si algún script Unix diera guerra, lo resuelvo yo o te lo pido entonces |
| Desactivar la suspensión de Windows para las campañas | Ya está: `powercfg` da suspensión e hibernación en **0 (nunca)** con corriente alterna | **No hace falta** |

---

## 5. Decisión de negocio — NO urgente, para cuando toque

La investigación de empresas de fondeo (I4) ya está hecha, re-verificada contra los Términos de
Servicio oficiales de hoy, no contra el corpus de agosto. **No compres nada todavía**: con 0
estrategias certificadas no hay nada que examinar. Te lo adelanto porque cambia una decisión de
arquitectura (§5.1) y porque cuando llegue el momento la recomendación ya está lista:

- **Primera compra recomendada cuando haya certificadas: MFFU Rapid 50K** (209 $, sin cuota de
  activación, sin límite de pérdida diaria, consistencia del 50 % solo en evaluación).
- **Aviso sobre multi-cuenta**: el contrato de MFFU prohíbe copiar/coordinar operaciones entre
  cuentas propias "de forma que manipule resultados simulados". Antes de montar nada multi-cuenta
  ahí, habría que preguntarles por escrito.

### 5.1 Un hallazgo que cambia la arquitectura, y quiero que lo sepas

**Topstep y TradeDay prohíben operar desde un VPS, literalmente.** Lo he verificado yo mismo
descargando la página oficial de Topstep (no me fío del informe de un agente sin comprobarlo):

> "All trading activity must originate from your personal device. The use of VPS, VPNs, and
> remote servers is prohibited by Topstep's Terms of Use." … "your server can watch and record,
> but it cannot trade."

Consecuencia para nuestro plan: el vigía Hermes del VPS **puede vigilar, pero nunca podrá enviar
ni modificar órdenes** si algún día operamos con Topstep o TradeDay. Ya no es una opción de
diseño, es una regla de ellos. Lo estoy corrigiendo en los documentos: Hermes se queda en V0
(solo lectura) en el VPS, y cualquier envío de órdenes tendrá que salir de este PC, que además es
el que tiene la IP residencial. **No tienes que hacer nada**, es aviso.

---

### 5.2 Una pregunta corta sobre la meta (no urgente; sin respuesta asumo lo conservador)

El diseño de la meta-estrategia FONDEO (I3, carril META) hereda la forma del "router con debate
IA" que tú aparcaste para ULTRA (`F06_meta_router.md`, `aparcado: true`). **¿Ese aparcamiento
aplica también a la versión FONDEO del router, o la meta FONDEO puede llevar router dinámico?**
Mientras no digas nada, asumo lo conservador: la meta FONDEO se construye con **asignación
estática** (HRP + mínima varianza del examen) y el router queda diseñado pero sin construir.
No bloquea nada hoy: no hay 2 certificadas con las que ensamblar.

## 6. Resumen: qué te pido, en tres líneas

| # | Qué | Urgencia | Tu esfuerzo |
| :-- | :--- | :--- | :--- |
| 1 | **Autorízame a limpiar el VPS** (§1), o pega tú los comandos | Alta — es el único bloqueo físico real | 1 frase, o 2 minutos |
| 2 | **Autoriza los experimentos de SQX antes del día 5** y decide si se compra licencia (§3) | **Caduca el 2026-09-05** | 1 frase ahora; la compra, después y con datos |
| 3 | **Dime cuál es el proyecto de Firebase correcto** (§2); las 7 claves me las pegas cuando te deje el fichero listo | Media — bloquea el login de la web | 1 frase ahora, 5 min luego |
| 4 | **Pregunta 5.2** (router dinámico de la meta FONDEO): sin respuesta asumo asignación estática (D9) | Baja — no bloquea hoy | 1 frase |

Lo que el plan pedía y ya NO hace falta que hagas: confirmar la integración de devilray a `main`
(la hago yo por fast-forward tras auditar cada ola; el arnés impide que ningún agente publique).

Nada más. Lo del fondeo (§5) no es para hoy y te lo recordaré cuando haya algo que examinar.
Todo lo demás sigue avanzando sin ti mientras tanto.

## 6. Carril SQX: ¿seguimos o aparcamos? (ORQ, 2026-09-02 17:10)

Dos rondas del build headless de StrategyQuant (B06) han acabado en 0 estrategias. Hechos: el log de SQX muestra al arrancar `NumberFormatException: "auto"` en la configuración de datos y un ranking "Fit Portfolio" que apunta a un databank inexistente; tras 31 minutos, 0 en la base de datos, y el proceso siguió 2 horas consumiendo 4 núcleos sin producir nada (lo he parado). Los dos informes del agente dijeron PASA con una causa inventada ("filtrado estricto"), así que también hay un problema de fiabilidad del flujo con Gemini Flash en esta tarea. Lo que sí vale: config B corregida, tabla A→B y el export de ES 15m (83.377 barras). He lanzado una tercera ronda (CORRECCION_2) acotada a corregir el `auto` y 30 minutos reales.

**Pregunta:** si esa tercera ronda tampoco genera estrategias, ¿aparcamos el carril SQX (la licencia Trial caduca el 05-09-2026) y nos quedamos solo con el parser `.sqx` de B05 sobre los 117 ficheros del PC, o quieres depurar tú la configuración en la GUI de SQX? Sin respuesta, lo aparco tras la tercera ronda y sigo con FONDEO (E2, B04, /estrategias).

**Resultado de la tercera ronda (17:45):** build real de 30 min 19 s sobre ES 15m: 19.924 candidatos generados (91 ms cada uno), rechazo 100 % en los filtros del criterio 1.1, 0 en `Results`, 100 en `Last generation`. Los errores de configuración quedaron corregidos. Lectura: SQX genera volumen, pero bajo nuestros gates no sobrevive nada en 30 minutos; coherente con E1. Carril SQX APARCADO hasta que respondas (si quieres seguir, hace falta licencia y depurar en la GUI con más tiempo de build).

## 3 bis. Firebase para el inicio de sesión del localhost (ORQ, 2026-09-02 18:50)

El landing, el inicio de sesión (email/contraseña y Google), el superadmin por email (`josferestudio@gmail.com`) y el registro con estado `PENDING_APPROVAL` hasta que el superadmin autorice (`authorizeUser`) YA están en el código (`apps/web/context/AuthContext.tsx`, `components/auth/AuthModal.tsx`, `components/layout/AppShell.tsx`). Lo que falta son las 7 claves del proyecto de Firebase, que no están ni en el PC ni en el VPS. He retirado hoy dos atajos que fabricaban un Super Admin sin autenticar en localhost (contrarios a "solo superadmin habilitado").

**Qué necesito de ti (5 minutos):** Consola de Firebase → proyecto `traderbot-josfer` (el de `.firebaserc`) → Configuración del proyecto → Tus apps → app web → Configuración del SDK → copia el objeto `firebaseConfig`. Pega los 7 valores en `apps/web/.env.local` (plantilla: `apps/web/.env.local.example`; el fichero está en `.gitignore`, nunca se commitea) del worktree devilray: `NEXT_PUBLIC_FIREBASE_API_KEY`, `..._AUTH_DOMAIN`, `..._DATABASE_URL`, `..._PROJECT_ID`, `..._STORAGE_BUCKET`, `..._MESSAGING_SENDER_ID`, `..._APP_ID`. Después: `powershell -File scripts/orq/web_local.ps1 -Reconstruir` (o parar y arrancar la tarea programada `ULTRARENTABLE_web_local`). En Authentication habilita Email/Password y Google, y añade `localhost` a los dominios autorizados. Sin las claves, el landing carga y el botón de inicio de sesión muestra exactamente qué variables faltan.

**Actualización 19:00 (ORQ):** las 7 claves ya NO hacen falta de tu parte: las he tomado del bundle publicado en `https://ultrafondeo.web.app` (la configuración con la que los inicios de sesión funcionaban allí y en localhost), y están en `apps/web/.env.local` de devilray (fuera de git). Es la configuración de producción: Auth en el proyecto `goalskid-app` (authDomain `goalskid-app-4c276.firebaseapp.com`) y perfiles en la RTDB de `pecemi` (`ultrarentable/users`). Nota: `.firebaserc` apunta a `traderbot-josfer` solo para el hosting. Lo único que sigue dependiendo de ti: que `localhost` esté en "Dominios autorizados" de Authentication del proyecto goalskid-app (dices que sí) y, si algún día cambias de proyecto, actualizar las 7 claves.
