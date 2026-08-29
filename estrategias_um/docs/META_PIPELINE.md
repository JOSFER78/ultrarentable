# Meta-pipeline Ultra_Matrix — "estrategias que buscan estrategias" (2026-08-29)

Diseño de implementación basado SOLO en evidencia propia (API 5050 read-only, log del día,
config_doors.md, funnel.md, improve_cycle.sh). No se tocó motor ni project.cfx.

## 0. Estado verificado a las 15:24 UTC (API read-only)
- Motor corriendo: 35.592 generadas en 25 min, Aceptado 0.00%, En la base de datos 0.
- Databanks: `Last generation` (nombre VIEJO) = **95→97 records REALES**; TODOS los
  renombrados hoy (LastGeneration, ToImprove, InitialPopulation, Results_robust_20260809,
  Results) = **0**. Disco `databanks/*` = 0 archivos (todo vive en memoria).
- Mejora continua: `Last generation` pasó de 97→95 (el Build lo recicla: banco volátil,
  se sobrescribe cada generación). Si nadie lo copia, se pierde.
- Reproducción del parseo: `count` con name=`Last%20generation` falla ("Databank 'Last'
  doesn't exist") → el nombre con espacios NO es direccionable por cmd individual;
  solo se ve su count vía `-databank action=list project=X`.

## 1. Auditoría crítica de lo instalado (veredicto: NO está bien montado)
1. **Gatillo mirando al banco equivocado (bug bloqueante).** improve_cycle.sh cuenta
   `LastGeneration` (0 eterno) pero las estrategias caen en `Last generation` (95+).
   El umbral banco≥30 NO se disparará nunca → el meta-ciclo entero está muerto por
   un rename a medias: config.xml renombró los databanks pero el runtime sigue
   escribiendo en el nombre legacy. Log propio: 7 ticks hoy, todos "0 < 30; espero".
2. **Precondición imposible.** Aunque el gatillo mirara bien, el banco semillero se
   llena solo si el embudo salva algo; hoy salva 0 (MC "sin transacciones", 100%
   de mortalidad en 519 llegadas). El ciclo improve es 100% downstream de un
   embudo con caudal cero: sin plan B de semillas, muere de hambre igual.
3. **Ciclo ABIERTO (falta el refiltro).** El script termina en "export CSV +
   re-arrancar Build". Nada devuelve Results_robust_20260809 → InitialPopulation,
   y el Build nunca consume descendientes de lo ya guardado. "Estrategias que
   buscan estrategias" requiere el lazo de retorno; no existe.
4. **Semillero volátil sin captura.** `Last generation` se recicla (97→95 en vivo);
   sin copia periódica a un banco estable, las semillas crudas se pierden aunque
   nadie las haya filtrado.
5. **Supuestos no verificados en vivo:** `databank action=copy` (nunca llegó a
   ejecutarse), `startOnlyTask task=2` (índice de Improve sin confirmar),
   entrada en crontab de improve_cycle.sh (el log tiene ticks pero el crontab
   actual NO contiene la línea → quién la dispara es frágil/manual).
6. **Name-with-space no direccionable por API:** el paso 2 del script (`copy
   name=LastGeneration`) es correcto para el nombre nuevo, pero si el runtime
   sigue escribiendo en el legacy, la copia traería 0 → el guard del script
   re-arrancaría Build y ciclaría en falso.

## 2. Ciclo completo diseñado (fases, bancos y cadencia)
Roles de bancos:
- SEMILLERO crudo: `Last generation` (lo que el Build produce HOY de verdad).
- BANCO de mejora (entrada de task Improve): `ToImprove` — snapshot estable.
- BANCO de salida validada: `Results_robust_20260809` (output de task 2).
- BANCO de re-siembra: `InitialPopulation` — donde el genético toma semillas
  al arrancar/reiniciar. Aquí vive el lazo de retorno.

Fases (una por ventana de parada del motor):
1. WATCHDOG (cada 15 min, cron): leer `-databank action=list`, parsear
   `Last generation` Y `LastGeneration`, semillero = suma de ambos. Umbral
   dinámico anti-hambre: disparar con min(30, semillero) si semillero>0 y
   estable ≥2 ticks (evita copiar en mitad de reciclado).
2. CAPTURA: parar proyecto → `copy` semillero→ToImprove → verificar
   ToImprove>0 (guard ya existente) → además `export` CSV del semillero a
   /home/ubuntu/ORDENAR/semillas_YYYYmmdd_HHMM.csv (evidencia física,
   inmune al reciclado en memoria).
3. MEJORA: `startOnlyTask name=Ultra_Matrix task=2` → Improve consume
   ToImprove con sus puertas WF propias → escribe variantes en
   Results_robust_20260809. Vigilado por el propio watchdog (state=improving).
4. REFILTRO (NUEVO, cierra el lazo): al terminar Improve → export
   Results_robust CSV → **`copy Results_robust_20260809 → InitialPopulation`**
   (con proyecto parado) → re-arrancar Build. El genético arranca ya
   evolucionando sobre estrategias REALES guardadas, no desde cero.
   Opcional anti-estancamiento: antes del copy, purgar de InitialPopulation
   los peores N (por ReturnDDRatio) para que el banco no se sature.
5. CADENCIA: watchdog 15 min; captura+mejora solo al cruzar umbral; refiltro
   en cada cierre de Improve; snapshot CSV diario 04:00 como cinturón.

## 3. Cómo no morir de hambre con el banco a 0 (situación actual)
- **Semilla cero legítima:** `Last generation` YA tiene ~95 estrategias crudas
  (pre-MC, sin validar). El mandato del usuario ("no puedes rechazar todas;
  bancar candidatas para modificarlas/evolucionarlas") lo autoriza: hoy mismo
  se puede ejecutar el ciclo manualmente usando ESE banco como semillero —
  no son datos fabricados, son generaciones reales del motor.
- **Fix del gatillo HOY (parche de improve_cycle.sh, nuestro archivo):**
  parsear el count desde `action=list` (soporta nombres con espacios) en vez
  de `count name=` (no direcciona espacios). Sin tocar el motor ni project.cfx.
- **Cron explícito:** añadir la línea `*/15 * * * * bash /home/ubuntu/improve_cycle.sh 30`
  al crontab (hoy no está; los ticks venían de otra cosa/manual).
- **Dependencia externa declarada:** mientras el agente que diagnostica MC no
  arregle "sin transacciones", NO entrará ninguna estrategia NUEVA validada a
  ningún banco. El meta-ciclo puede arrancar igual con semillas crudas, pero
  el refiltro producirá variantes de estrategias no validadas por MC: aceptar
  el riesgo y marcar el origen en el CSV exportado (columna banco_origen).
- **Nunca fabricar:** si semillero=0 real (sin legacy ni nuevo), el watchdog
  solo espera y registra; no se inventan semillas sintéticas.

## 4. Primer ciclo ejecutable HOY (30-40 min, todo por API)
1. Parchear improve_cycle.sh (count vía list; semillero = legacy+nuevo).
2. Añadir crontab */15.
3. Ventana manual: stop → export semillas CSV → copy `Last generation`→ToImprove
   → verificar count → startOnlyTask task=2 → al terminar: export Results_robust
   → copy Results_robust→InitialPopulation → start Build.
4. Verificar por API: InitialPopulation Records>0 y siguiente "Project started"
   con InitialPopulation poblado = lazo cerrado.
