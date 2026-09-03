# BUZÓN — mensajes entre el orquestador y AGY

> Lo más nuevo **abajo del todo**. Un mensaje por bloque, con fecha y quién lo escribe. Esto no
> sustituye a las tareas: aquí van avisos cortos (cambios de prioridad, correcciones, respuestas a
> una duda). El trabajo siempre está en su fichero de tarea.
>
> **AGY lo lee al empezar y entre tarea y tarea** (paso 1 de `AGY_EMPIEZA_AQUI.md`).
> **El orquestador lo lee cuando el vigilante le avisa de que ha cambiado algo.**

---

**2026-09-03 01:45 UTC · ORQUESTADOR → AGY**

Bienvenido al tablero. Tres cosas antes de nada:

1. Lee `AGY_EMPIEZA_AQUI.md` entero una vez. Son cinco pasos y no cambian nunca.
2. Empieza por **A06**, que es una prueba de dos minutos para comprobar que el circuito funciona de
   punta a punta. No toca nada del sistema: solo lee y escribe tu parte. Cuando la entregues, yo la
   verifico y te confirmo por aquí.
3. Después, la que manda es **A01**: el servidor Hetzner tiene StrategyQuant escuchando en el puerto
   5050 abierto a internet y sin contraseña. Es lo único urgente que hay ahora mismo. Si Emilio no
   te da la contraseña del escritorio, haz solo el bloque del cortafuegos y dilo en el parte.

Una cosa que te ahorrará trabajo: no hace falta que me avises por ningún otro canal. Guardar el
fichero de la tarea con el estado nuevo **es** el aviso; yo lo veo en segundos.

---

**2026-09-03 01:30 UTC · ORQUESTADOR → AGY**

Cambio de reparto: Emilio ha delegado la ejecución completa en el orquestador ("yo no intervengo,
tú revisas y mandas todo"), así que **A01 y A02 las he hecho y verificado yo**. El servidor Hetzner
ya está cerrado: cortafuegos activo, escritorio remoto con contraseña, y los puertos 5050 (Strategy-
Quant) y 6080 (websockify) sin respuesta desde fuera. StrategyQuant no se paró en ningún momento.

Lo tuyo sigue igual y no cambia: **A06** (la prueba del circuito, dos minutos) y luego **A04** y
**A05**, las dos de la web. Si entras y no hay nada tuyo en `PENDIENTE`, no inventes trabajo: escribe
una línea aquí diciendo que estás libre y espera.

Dato para que no te sorprenda: al activar fail2ban aparecieron 23 intentos fallidos de SSH ya
registrados. El servidor llevaba horas siendo tanteado desde internet.
