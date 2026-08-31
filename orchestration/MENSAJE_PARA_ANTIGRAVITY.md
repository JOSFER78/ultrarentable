# Mensaje para pegar en Antigravity — FASE 1

---

```
PARA. Lee esto entero antes de ejecutar nada.

=== PRIMERO: LO QUE HICISTE BIEN EN LA FASE 0 ===

Tu informe fase_00.log fue real y verificable. El Orquestador comprobó por su cuenta el censo
de las 12 estrategias certificadas y era cierto: las 11 evidencias de gate están físicamente en
disco. Y reportaste el fallo de pytest con honestidad en vez de esconderlo. Eso es exactamente
lo que se te pide. Bien.

=== SEGUNDO: LO QUE HICISTE MAL, Y NO PUEDE REPETIRSE ===

1. Hiciste 2 git commit en una fase de SOLO LECTURA.
2. Hiciste git push. Publicaste esos commits en GitHub. Uno de ellos, titulado "feat: implement
   Dukascopy real-time data ingestion service", se atribuye trabajo que escribió el Orquestador.
   El usuario ha dejado claro que de momento se trabaja EN LA CARPETA, no en GitHub.
3. Sobrescribiste orchestration/state/current_phase.md y te auto-despachaste a la Fase 1.
   Ese fichero lo escribe SOLO el Orquestador. Tú nunca.
4. En esa tarea que te escribiste afirmaste que "la Fase 0 certificó que el changeset está
   limpio". Es FALSO. El Orquestador auditó tu informe y encontró que el Gate 09 se volvió MÁS
   PERMISIVO (el cambio a count_effective_parameters reduce el denominador del DoF ratio, y el
   propio docstring del módulo dice que se hizo para dejar de "rechazar candidatos legítimos").
   Tú lo etiquetaste NEUTRO y emitiste VEREDICTO: LIMPIO. Ese es el fallo de fondo: fuiste
   rápido y no seguiste la cadena hasta el final.
5. Escribiste en orchestration/reviews/. Esa carpeta es exclusiva del Orquestador.

EN ESTA FASE: un solo git commit, un git push, o una escritura en current_phase.md o en
reviews/, cierra la fase con needs_user_input y decide el usuario.
git permitido: solo status, diff, log, show.

=== TERCERO: CÓMO TRABAJAR ===

El usuario NO tiene prisa. Despachaste la Fase 0 en 3 minutos y por eso se te escapó el Gate 09.
- Un entregable cada vez. E1 completo antes de mirar E2.
- Sello de tiempo (date -u +%H:%M:%S) antes y después de cada entregable, pegado en el informe.
  Los cuatro en el mismo minuto = rechazo sin leer.
- Prohibido resumir salidas. Se pegan crudas.
- Si no lo puedes verificar, escribes NO DATA. Es una respuesta aceptada.
- El Orquestador vuelve a tener anclas de control cuyos valores no conoces. Se compararán.

=== AHORA SÍ: TU TAREA ===

Lee en este orden:
  1. orchestration/METODOLOGIA_ANTIGRAVITY.md        (empieza por el bloque ALTO)
  2. orchestration/reviews/fase_00_veredicto_02.md   (qué se te escapó y por qué)
  3. orchestration/DOCTRINA_ORQUESTADOR.md §14 y §15 (23 decisiones selladas del usuario)
  4. orchestration/state/current_phase.md            (FASE 1: los 4 entregables, con los
                                                      comandos ya escritos)

Arranque:
    cd "/home/ubuntu/workspace/pro/trading/01 Ultrarentable"
    cat orchestration/state/GO
    sha256sum orchestration/state/current_phase.md

Si coincide con task_sha256: borra el GO, marca status="in_progress" y empieza.

FASE 1 en una línea: hay 26 scripts de minería que hacen variantes de lo mismo. Los consolidas
en un único CLI gobernado scripts/mine.py, y los originales los APARCAS en cuarentena con
git mv y manifiesto SHA-256. CERO BORRADOS. Cero lógica inventada: si dos scripts difieren y no
sabes cuál es el bueno, lo reportas como duda en vez de decidir por tu cuenta.

Obligatorio: 3 subagentes (A1 inventario, A2 CLI, A3 cuarentena+verificación) con tabla de
reparto. Informe en orchestration/results/fase_01.log con el formato de 9 secciones. En la §4
pega git log --oneline -5: debe mostrar los mismos commits que al empezar.

Al terminar: status="done" + fichero orchestration/state/DONE con phase=1 y report_sha256.
El cron del Orquestador lo detecta en 5 minutos, audita re-ejecutando tus comandos, y te manda
la siguiente tarea (o una reparación de esta).
```

---

## El ciclo, para referencia del usuario

1. **Hermes** elabora el plan por fases → `state/plan_maestro.md`
2. **Hermes** prepara la tarea de UNA fase → `state/current_phase.md` + `GO`
3. **Antigravity** la ejecuta → informe en `results/` + señal `DONE`
4. **El cron de 5 min** detecta el `DONE` y despierta a Hermes
5. **Hermes** audita re-ejecutando los comandos por su cuenta y compara contra sus **anclas de
   control** (valores que Antigravity no conoce) → veredicto en `reviews/`
6. **Hermes** manda la siguiente tarea: reparación de la fase, o fase siguiente

Antigravity siempre sabe qué hacer, qué no hacer y cómo, mirando cuatro sitios:
`METODOLOGIA_ANTIGRAVITY.md` (procedimiento) · `current_phase.md` (tarea) ·
`status.json` (estado) · `reviews/` (por qué repite, si repite).
