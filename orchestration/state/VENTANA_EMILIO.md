# VENTANA EMILIO — lo único que necesito de ti (abierta 2026-09-01, ciclo 1)

> Regla de la casa: **una sola ventana, no goteo.** Todo lo que sigue está preparado para que te
> cueste minutos. Mientras tanto sigo trabajando en todo lo que NO depende de ti, que es la mayor
> parte. Tú tienes veto absoluto: escribe "PARA" y todo queda registrado y retomable.
>
> **Buenas noticias antes de la lista**: tres cosas que el plan daba por necesarias resultaron NO
> serlo. Las verifiqué una a una y te ahorran trabajo (§4).

---

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

## 3. ⏳ LICENCIA DE STRATEGYQUANT X — CADUCA EN 4 DÍAS (decisión de dinero, es tuya)

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

## 6. Resumen: qué te pido, en tres líneas

| # | Qué | Urgencia | Tu esfuerzo |
| :-- | :--- | :--- | :--- |
| 1 | **Autorízame a limpiar el VPS** (§1), o pega tú los comandos | Alta — es el único bloqueo físico real | 1 frase, o 2 minutos |
| 2 | **Autoriza los experimentos de SQX antes del día 5** y decide si se compra licencia (§3) | **Caduca el 2026-09-05** | 1 frase ahora; la compra, después y con datos |
| 3 | **Dime cuál es el proyecto de Firebase correcto** (§2); las 7 claves me las pegas cuando te deje el fichero listo | Media — bloquea el login de la web | 1 frase ahora, 5 min luego |

Nada más. Lo del fondeo (§5) no es para hoy y te lo recordaré cuando haya algo que examinar.
Todo lo demás sigue avanzando sin ti mientras tanto.
