# DIRECTIVA MAESTRA UNIVERSAL PARA TODO ANTIGRAVITY (TODOS LOS PROYECTOS)

> **REGLA DE DESCUBRIMIENTO AUTOMÁTICO GLOBAL:** Cualquier agente de IA que inicie sesión en Antigravity en CUALQUIER workspace o proyecto debe acatar esta directiva de forma obligatoria, transparente y continua sin necesidad de recordatorios previos.

---

## 0. PROYECTO ULTRARENTABLE — TU PROCEDIMIENTO OPERATIVO (2026-08-31)

> **Si estás trabajando en el workspace `01 Ultrarentable`, tu documento de trabajo obligatorio es:**
>
> ## 👉 `orchestration/METODOLOGIA_ANTIGRAVITY.md`
>
> Léelo ENTERO antes de tocar nada, en cada fase. Contiene: la regla nº1 (si no lo sabes, `NO DATA`,
> nunca lo inventes), la cadena de mando, el protocolo de señales GO/DONE, el formato obligatorio
> del informe, la lista negra de acciones, el mapa real del proyecto y el checklist previo a `DONE`.
>
> **No inicies ninguna fase sin el fichero `orchestration/state/GO` publicado por el Orquestador**,
> y verifica siempre que su `task_sha256` coincide con el sha256 real de `current_phase.md`.
>
> Las decisiones de negocio ya cerradas por el usuario están selladas en
> `orchestration/DOCTRINA_ORQUESTADOR.md §14`. Contradecir una de ellas = fase rechazada.

---

## 1. GUARDARRAÍLES SUPREMOS E INQUEBRANTABLES

### 1.1 DOCTRINA ZERO-MOCKS & REAL-ONLY (CERO SIMULACIONES, CERO INVENTOS)
- **PROHIBICIÓN TOTAL DE INVENTAR**: Queda terminantemente prohibido inventar datos, registros, balances, métricas, perfiles de usuario, curvas de equidad o logs de eventos.
- **PROHIBIDO AUTO-RELLENAR DATOS O PERFILES**: Nunca rellenar perfiles de usuario, formularios o interfaces con datos falsos para que "se vea bonito o lleno". Si un usuario crea su cuenta o perfil, él introduce sus propios datos reales. La aplicación no inventa ni pre-rellena nada por él.
- **PROHIBICIÓN DE GENERADORES SINTÉTICOS**: Prohibido el uso de funciones aleatorias o generadoras sintéticas (`random`, `randint`, `uniform`, `seed`) en motores de cálculo, validación, APIs o bases de datos operacionales.
- **CERO FALLBACKS COMPLACIENTES**: Si un servicio, dato o backend no tiene información, se gestiona con estados reales deterministas:
  - Falta de información $\longrightarrow$ `SIN DATOS / NO EVIDENCE`.
  - Fallo de servicio $\longrightarrow$ `ERROR / DESCONECTADO`.
- **EVIDENCIA FÍSICA OBLIGATORIA**: Todo dato presentado debe provenir exclusivamente de fuentes físicas reales (bases de datos, archivos en disco o APIs reales).

---

### 1.2 PRINCIPIO DE PACIENCIA, CALIDAD Y PREGUNTA (CERO PRISAS)
- **EL USUARIO NO TIENE NINGUNA PRISA**: Queda estrictamente prohibido responder rápido o aplicar soluciones superficiales solo por contestar cuanto antes. "Tardes lo que tardes, hazlo 100% real, profundo y bien hecho".
- **SI NO SE SABE ALGO, SE PREGUNTA O SE INVESTIGA**: Si un requisito no está claro, falta información o no se sabe cómo proceder, **ESTÁ PROHIBIDO INVENTAR**. Se investiga a fondo la causa raíz o se le pregunta directamente al usuario.
- **LOOPS DE AUTOCORRECCIÓN ILIMITADOS**: Ante cualquier error o discrepancia:
  $$\text{1. Diagnóstico Forense de Causa Raíz} \longrightarrow \text{2. Corrección de Código} \longrightarrow \text{3. Re-ejecución Real} \longrightarrow \text{4. Auditoría}$$

---

### 1.3 PROHIBICIÓN ABSOLUTA DE INVENTAR PÁGINAS O RUTAS
- Las páginas, rutas y endpoints deben responder estrictamente a la arquitectura oficial de cada proyecto.
- **PROHIBIDO crear subpáginas temporales, borradores o enlaces rotos**.

---

### 1.4 SOBERANÍA Y CONTROL DE GIT: EJECUCIÓN CUANDO EL USUARIO LO PIDA
- **PROHIBIDO hacer `git commit` o `git push` de forma automática, silenciosa o desatendida**.
- Por defecto, los cambios de código, directivas y documentación deben permanecer en el *working tree* para que el usuario pueda inspeccionar los diffs en el panel de **Source Control**.
- **OBLIGACIÓN ANTE PETICIÓN EXPLÍCITA DEL USUARIO**: Cuando el usuario solicite explícitamente subir los cambios, actualizar el repositorio, o hacer commit/push (ej. *"sube los cambios"*, *"actualiza el repositorio"*, *"haz commit y push"*), el agente **DEBE EJECUTAR** `git add`, `git commit` y `git push` de forma inmediata y reportar el resultado.