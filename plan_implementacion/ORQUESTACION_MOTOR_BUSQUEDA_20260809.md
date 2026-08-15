# ORQUESTACIÓN — Controlador de estrategias: ENTRAR EN StrategyQuant como experto (NO scripts hardcodeados)
> Fecha: 2026-08-09 · Rol: orquestador + revisor (NO ejecutar)
> FOCO ÚNICO 100%: buscar BIEN estrategias — conseguir MILES de % verificables en backtest.

## CORRECCIÓN CONCEPTUAL CRÍTICA (usuario, 2026-08-09)
> "No puede crear scripts para buscar estrategias, la IA debe ENTRAR en StrategyQuant y usar
> StrategyQuant, tiene muchas variables y casos de uso como para lanzar código hardcodeado,
> así no va a aprovechar todo su uso. INVESTIGA LA MEJOR MANERA DE USAR SQ."

=> El enfoque de "scripts que lanzan run_project con parámetros fijos" está DESCARTADO.
=> La IA debe MANEJAR la GUI REAL de StrategyQuant (que corre en VPS, Xvfb :99, ventanas visibles
   según xdotool, frontend Electron strategyquantx_ui) usando computer_use (clic/teclado/visión)
   para configurar el Builder, la evolución genética, bloques, plantillas y optimización con TODA
   su riqueza de variables, como un humano experto.
=> Antes de tocar nada: INVESTIGAR la mejor manera de usar SQX (opciones reales de la GUI, el
   X-Builder, evolución, qué configuración da resultados kamikaze de miles de %).

## Evidencia de accesibilidad GUI (verificada)
- SQX corre: /home/ubuntu/StrategyQuantX/StrategyQuantX + electron strategyquantx_ui.
- Xvfb DISPLAY=:99, captura 1920x1080 OK (import), xdotool/wmctrl/scrot disponibles.
- Ventanas visibles vía xdotool search (ids 60817409, 58720260).
- Herramienta computer_use disponible para controlar esa GUI.

## Frentes (subagentes ejecutan; Hermes orquesta y revisa)
- EXPERTO-SQX-GUI: subagente con computer_use que ENTRA en la GUI de SQX, explora y configura
  la búsqueda kamikaze con todas las opciones del builder/evolución. (PRIORIDAD MÁXIMA)
- INVESTIGA-SQX: subagente que investiga la MEJOR manera de usar SQX (docs/manuales/opciones GUI)
  para sacarle el 1000%. (PRIORIDAD MÁXIMA, en paralelo)
- B (core app): modo ULTRA/FONDEO + configurador IA (visible en la web).
- BLUEPRINT ✅ entregado y revisado.
- AUDITOR: scorecard de calidad (miles de % verificable vs overfit).

## DESCARTADO / REORIENTAR
- El RUNNER de scripts hardcodeados (lanzar run_project con parámetros fijos) NO es el camino.
  Los candidatos deben salir configurando la GUI de SQX correctamente, no por script ciego.

## Recordatorio de rol
- Hermes ORGANIZA, PREPARA mandatos, SUPERVISA y REVISA. NO edita código de la app ni nada.
- Subagentes ejecutan. Mantener foco único: CONTROLADOR DE ESTRATEGIAS usando SQX como experto.
