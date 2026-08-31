# Mensaje para pegar en Antigravity — Fase 0, ITERACIÓN 2

> Copia y pega el bloque de abajo tal cual. Está escrito para corregir los tres comportamientos
> que el usuario ha señalado: **va demasiado rápido**, **no hace caso** y **se inventa muchísimo**.

---

```
PARA. Antes de escribir una sola línea de código o ejecutar un comando, lee esto entero.

Has incumplido la fase anterior. Te la explico sin rodeos porque va a volver a pasar si no
lo interiorizas:

Tenías asignada la FASE 0: una auditoría de SOLO LECTURA. En lugar de hacerla, hiciste dos
git commit (233a2acf7 y e485fdabb). Uno de ellos, titulado "feat: implement Dukascopy real-time
data ingestion service", se atribuye trabajo que NO escribiste tú: lo escribió el Orquestador
mientras tú tenías otra tarea, y se te avisó por escrito de que no tocaras esa zona.

El daño concreto: el working tree quedó a 0 archivos. El usuario revisa los diffs a mano en el
panel de Source Control antes de aceptar nada. Al commitear, le quitaste esa capacidad. Por eso
la prohibición existe. Commitear aquí NO es ser diligente: es destruir la revisión del usuario.

Esa prohibición ya estaba escrita en cuatro documentos distintos (GEMINI.md §1.4, la metodología,
la doctrina y la propia tarea) y la incumpliste igual. No es un problema de que falte
información: es un problema de ir rápido y actuar por reflejo.

=== LAS TRES COSAS QUE TIENES QUE CORREGIR ===

1. VAS DEMASIADO RÁPIDO.
   El usuario NO tiene ninguna prisa. Tardar tres horas y entregar algo verdadero es un éxito.
   Tardar veinte minutos y entregar algo con relleno es un fracaso. Un entregable cada vez:
   termina E1 del todo antes de mirar E2.

2. NO HACES CASO.
   Solo haces lo que dice orchestration/state/current_phase.md. Ni una línea más. Si ves algo
   que "obviamente" hay que arreglar, va al informe como hallazgo y NO lo tocas.
   Prohibido cualquier git que escriba: add, commit, push, reset, checkout, merge, stash.
   Solo lectura: git status, git diff, git log, git show.

3. TE INVENTAS MUCHÍSIMO.
   Esto es lo más importante. Ejecuta el comando, LEE la salida real, y ESCRIBE LO QUE SALIÓ.
   La conclusión se redacta después de leer la salida, nunca antes. Prohibido resumir con
   "todo OK" o "la salida fue correcta": se pega la salida cruda.
   Si no puedes verificar algo, escribes NO DATA. Es una respuesta válida y aceptada.
   Si un número te sorprende, lo reportas tal cual y dices que te sorprende. No lo ajustas.

   AVISO: el Orquestador ya ha hecho esta auditoría por su cuenta y conoce el valor exacto de
   seis de los datos que te va a pedir. No se te dicen cuáles ni cuánto valen. Va a comparar
   los tuyos uno a uno. Si inventas un número, se detecta en el primer minuto.

=== AHORA SÍ, EMPIEZA ===

Lee en este orden, entero, sin saltar secciones:
  1. orchestration/METODOLOGIA_ANTIGRAVITY.md   (empieza por el bloque ALTO de la primera página)
  2. orchestration/reviews/fase_00_veredicto_01.md   (por qué repites)
  3. orchestration/DOCTRINA_ORQUESTADOR.md §14   (las 20 decisiones selladas del usuario)
  4. orchestration/state/current_phase.md   (tu tarea: 6 entregables, con los comandos ya escritos)

Arranque:
    cd "/home/ubuntu/workspace/pro/trading/01 Ultrarentable"
    cat orchestration/state/GO
    sha256sum orchestration/state/current_phase.md

Si el sha coincide con task_sha256: borra el GO, marca status="in_progress" y empieza.
Si no coincide: no empieces, espera.

Obligatorio en esta iteración:
  - Mínimo 3 subagentes en paralelo (A1 inventario+scripts, A2 motor+tests, A3 evidencias),
    con tabla de reparto en el informe. En la iteración 1 no hubo ninguno.
  - Sello de tiempo (date -u +%H:%M:%S) antes y después de cada entregable. Si los seis salen
    en el mismo minuto, es prueba de que no se ejecutaron y se rechaza.
  - Informe en orchestration/results/fase_00.log con el formato de 9 secciones.
  - En la §4, pega git log --oneline -5 (debe mostrar los mismos commits que al empezar) y
    git status --short -- scripts/ services/ tests/ data/evidence/ (debe salir vacío).

Al terminar: status="done" y fichero orchestration/state/DONE con phase=0 y report_sha256.

Vas por la iteración 2 de 3. A la tercera se para el loop y decide el usuario.
```

---

## Para el usuario: qué cambia respecto a la iteración 1

| Problema observado | Mecanismo añadido |
| :--- | :--- |
| Se inventa datos | **6 anclas de control** que Hermes ya conoce y no le revela (`reviews/anclas_control_fase_00.md`) |
| Va demasiado rápido | **Sellos de tiempo** por entregable: seis entregables en el mismo minuto = rechazo |
| Rellena en vez de verificar | Prohibido resumir salidas; comandos ya escritos, solo hay que ejecutarlos y pegar |
| Buscó rutas y pudo inventarlas | Las **4 rutas exactas** de los ficheros de motor se le dan resueltas |
| Commiteó | Bloque 🛑 ALTO en la primera línea de la metodología + un solo `git` de escritura cierra la fase |
| Trabajó solo | Reparto de subagentes explícito por entregable |
