# HERMES VIGÍA — el agente del VPS que monitoriza trades (diseño, 2026-09-01)

> Petición de Emilio: *"en la VPS vive Hermes, que monitorea los trades y así poder modificar
> órdenes o tamaños"* — o la mejor alternativa si la hay. Esto es el diseño evaluado.

## 1. Qué NO debe ser (alternativas descartadas y por qué)

| Alternativa | Veredicto |
| :--- | :--- |
| Una sesión interactiva de Claude 24/7 en tmux "mirando" | ❌ Frágil (se cae y nadie lo sabe), cara (contexto creciendo horas), y el propio historial del proyecto muestra que las sesiones vivas compiten por CPU |
| Un LLM decidiendo en el camino crítico del riesgo | ❌ Las reglas que salvan cuentas (pérdida diaria, trailing DD, cierre 16:59) deben ser deterministas y fail-closed, no una inferencia |
| Solo webhooks/n8n sin inteligencia | ⚠️ Válido como fontanería, pero no analiza ni adapta: no es lo que pides |

## 2. La arquitectura recomendada: 3 capas (determinista debajo, Hermes encima)

```
CAPA 1 — CENTINELA (servicio systemd, trading.slice, determinista, SIEMPRE encendido)
  · Lee posiciones/órdenes/equity del broker (Tradovate API / export de PickMyTrade) cada pocos s
  · Aplica REGLAS DURAS codificadas, fail-closed: límite de pérdida diaria, trailing DD
    intradía sobre equity FLOTANTE (misma semántica que el motor 5.15.0), cierre obligatorio
    antes de fin de sesión, kill-switch por desconexión de datos
  · Escribe estado a vigia_estado.json + espejo web; emite EVENTOS (umbral tocado, orden
    rellenada, divergencia con el backtest)
CAPA 2 — HERMES (Claude headless, bajo demanda, NO residente)
  · Se invoca por EVENTO de la capa 1 o por cron cada 15-30 min: `claude -p` (Agent SDK) con
    presupuesto acotado, lee vigia_estado.json + contexto del plan
  · Analiza: ¿el comportamiento en vivo diverge del backtest? ¿toca ajustar tamaño (dentro de
    rango pre-aprobado), mover stops, pausar una estrategia?
  · ACTÚA solo dentro de LÍMITES ESCRITOS (ver §3); todo lo demás lo ESCALA
CAPA 3 — ESCALADO A EMILIO
  · Telegram/email con el hecho, el análisis de Hermes y la acción propuesta
  · Sin respuesta ⇒ manda la regla conservadora de la capa 1 (nunca "esperar al humano" con
    una cuenta en riesgo: el centinela ya habrá cortado)
```

Por qué así: la capa 1 no puede fallar "pensando"; Hermes aporta el análisis y la adaptación
que pides (modificar órdenes/tamaños) sin ser un punto único de fallo; y el coste es por
invocación, no por hora de sesión abierta.

## 3. Límites de actuación de Hermes (V1, sellables por Emilio)

- Tamaño: solo DENTRO del rango ya aprobado por el examen F07 (nunca por encima del sizing
  del plan de la estrategia).
- Stops: solo en dirección conservadora (acercar, break-even); jamás ampliar riesgo.
- Pausar una estrategia: sí, con motivo registrado. Reactivarla: solo el orquestador o Emilio.
- Abrir posiciones nuevas: NUNCA (eso es de la estrategia exportada, no del vigía).
- Real money: **V2, solo con autorización explícita** (decisión #9 sigue vigente: demo primero).

## 4. Despliegue por fases

| Fase | Qué hace | Requisito |
| :-- | :--- | :--- |
| **V0** | Solo lee y reporta (demo Tradovate): estado, PnL flotante, distancia a límites, informe diario a `orchestration/results/vigia/` | Ventana sudo W0.6 (instalar unit); credenciales demo `[E]` |
| **V1** | Ajustes dentro de límites §3 en DEMO + escalado Telegram | V0 estable 1 semana; límites sellados por Emilio |
| **V2** | Lo mismo sobre cuenta real | Autorización explícita de Emilio, por escrito, cuenta a cuenta |

## 5. Notas técnicas

- **IP**: para demo da igual; para cuentas prop reales, el corpus `docs/conexiones_automatizar/`
  es tajante con las IP de datacenter — la ruta de órdenes real ya decidida es
  PickMyTrade+Tradovate (decisión #12) y la capa de red se resolverá en F08 con `ip_guard.py`
  y el runbook NT8 (el vigía LEE desde el VPS; el ENVÍO de órdenes reales puede tener que salir
  por otra vía — se decide en F08, no aquí).
- **Recursos**: capa 1 en Python plano (<100 MB, insignificante en el VPS liberado);
  Hermes headless solo cuesta cuando se invoca.
- **Territorio**: el vigía escribe SOLO en `results/vigia/` y su JSON de estado. Jamás toca BD
  de trabajo, datasets ni el repo.
- El centinela reutiliza la semántica ya verificada del motor 5.15.0 (reglas prop sobre equity
  flotante) — misma matemática en backtest, examen y vivo, o la divergencia será indetectable.
