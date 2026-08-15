# Trading Bots Automatizados con IA — Investigación Consolidada

**Fecha:** 8 de agosto de 2026  
**Propósito:** consolidar las investigaciones paralelas sobre trading bots, IA, backtesting, arquitectura y metodología, eliminando duplicaciones y separando conceptos sólidos de resultados de marketing.

---

# 1. La idea central

La conclusión más útil de todo el material no es “hacer un bot que opere”.

Es construir un **sistema de investigación y operación sistemática**:

```text
IDEA
 ↓
GENERACIÓN / CODIFICACIÓN
 ↓
BACKTEST
 ↓
ROBUSTEZ
 ↓
OUT-OF-SAMPLE
 ↓
WALK-FORWARD
 ↓
FORWARD / PAPER
 ↓
LIVE PEQUEÑO
 ↓
MONITORIZACIÓN
 ↓
ESCALADO / RETIRADA
```

La IA puede acelerar prácticamente todas las fases, pero no sustituye la validación estadística.

---

# 2. Qué papel debería tener la IA

La evidencia recopilada de DaviddTech apunta a una distinción fundamental:

### Mal enfoque

```text
LLM → "¿subirá BTC/NQ?" → comprar
```

### Mejor enfoque

```text
Datos
  ↓
Hipótesis cuantitativa
  ↓
Código
  ↓
Backtest
  ↓
Validación
  ↓
Reglas
  ↓
Ejecución
```

El LLM es especialmente útil como:

- investigador;
- programador;
- analista de código;
- generador de hipótesis;
- orquestador de herramientas;
- asistente de backtesting;
- documentador;
- monitor.

No debe considerarse por sí mismo una prueba de capacidad predictiva.

---

# 3. DaviddTech: la evolución más interesante

Canal:
https://www.youtube.com/@daviddtech

Los vídeos más recientes muestran una evolución:

**indicadores → estrategias → bots → IA para desarrollar estrategias → Strategy Factory → portfolios de micro-bots → agentes → ejecución.**

## Vídeos prioritarios

### How to Build an INSANELY Profitable AI Trading Bot — Full Guide
https://www.youtube.com/watch?v=86AlV6174KI

El interés principal es el flujo completo de investigación, backtesting, optimización y despliegue.

### I Gave Claude AI Access to 1500 FREE TradingView Strategies
https://www.youtube.com/watch?v=VD2TC8Ifl0w

Introduce el concepto de una **Strategy Factory** y de utilizar IA para seleccionar/gestionar muchas estrategias.

### I Gave Claude AI My Best TradingView Strategy… The Fix Was Insane
https://www.youtube.com/watch?v=Xlt-DxozPVo

Muy útil para entender cómo atacar un problema de drawdown mediante filtros de régimen.

### Our Community Found a FREE TradingView Indicator
https://www.youtube.com/watch?v=yPMLD8Y5A-M

Explora régimen de mercado, Lyapunov, TDFI y ATR.

### Every AI Trading Bot on X Looks Fake… So I Built One
https://www.youtube.com/watch?v=jnJF0W2XgqA

Especialmente interesante como crítica a los bots de IA presentados como cajas negras mágicas.

---

# 4. Framework estructurado: mejor que pedirle a una IA una estrategia desde cero

Un LLM puede producir estrategias plausibles pero defectuosas.

Es preferible darle un **espacio de búsqueda estructurado**:

1. definición del mercado;
2. régimen;
3. señal primaria;
4. confirmación;
5. filtro;
6. entrada;
7. stop;
8. salida;
9. position sizing;
10. límites de riesgo.

DaviddTech utiliza frameworks como NNFX/Strategy Boilerplate como referencia metodológica.

### Principio general

> La IA debería explorar dentro de unas reglas bien definidas, no inventar libremente el sistema que supuestamente “más gana”.

---

# 5. Pipeline de validación recomendado

## Etapa 1 — In-Sample

Se utiliza para desarrollar la hipótesis.

No sirve como prueba final.

## Etapa 2 — Out-of-Sample

Datos que no participaron en el desarrollo.

Debe ser una verdadera separación temporal.

## Etapa 3 — Walk-Forward

Entrenar/optimizar en una ventana y evaluar en una ventana posterior, repitiendo el proceso.

El objetivo es comprobar si la estrategia mantiene propiedades fuera de la muestra de desarrollo.

## Etapa 4 — Forward / Incubación

Ejecutar con datos nuevos y reglas congeladas.

## Etapa 5 — Paper / Testnet

Comprobar:

- señales;
- latencia;
- fills;
- slippage;
- reconexión;
- duplicación de órdenes;
- stops;
- estados de posición.

## Etapa 6 — Live pequeño

Sólo después de superar las anteriores.

---

# 6. El principal enemigo: overfitting

Una Strategy Factory capaz de probar miles o cientos de miles de variantes puede ser extraordinariamente potente y, al mismo tiempo, peligrosísima.

Si se prueban suficientes hipótesis, alguna parecerá espectacular por azar.

## Riesgos principales

### Data-mining bias

Se selecciona retrospectivamente la estrategia que mejor funcionó.

### Look-ahead bias

La estrategia utiliza información que no estaba disponible en el momento de la decisión.

### Repainting

La señal histórica cambia después de haberse producido.

### Sample-size bias

Una estrategia con pocas operaciones puede mostrar un resultado extraordinario sin suficiente evidencia.

### Costes irreales

No incluir:

- comisión;
- spread;
- slippage;
- latencia;
- fills parciales;
- diferencias entre precio teórico y ejecutado.

---

# 7. Filtros estadísticos recomendados

Para una fábrica de estrategias:

1. número mínimo de operaciones;
2. costes y slippage realistas;
3. separación IS/OOS/Holdout;
4. walk-forward;
5. Monte Carlo/resampling;
6. análisis de sensibilidad;
7. estabilidad de parámetros;
8. evitar estrategias cuya rentabilidad dependa de un único periodo;
9. comprobar distribución de resultados, no sólo beneficio total;
10. penalizar complejidad.

## Plateau test

No interesa que una estrategia sólo funcione con:

`RSI = 37`

pero falle con:

`RSI = 36` o `38`.

Es mejor una zona estable de parámetros.

---

# 8. Régimen de mercado

Una de las ideas más transferibles de DaviddTech es:

> No todas las estrategias deben operar en todos los mercados y condiciones.

Ejemplos de régimen:

- tendencia;
- rango;
- alta volatilidad;
- baja volatilidad;
- mercado caótico;
- mercado más persistente.

Herramientas exploradas en el material:

- Choppiness Index;
- TDFI;
- Lyapunov;
- ATR.

No deben considerarse automáticamente válidas por aparecer en un vídeo. Deben superar la misma validación que cualquier otra señal.

---

# 9. Choppiness Index

El caso analizado en DaviddTech es interesante porque utiliza el indicador como **filtro**, no necesariamente como señal primaria.

Idea:

```text
ESTRATEGIA
   +
FILTRO DE RÉGIMEN
   ↓
EVITAR PARTE DE LOS TRADES DE BAJA CALIDAD
```

Esto puede ser más robusto que modificar continuamente la señal de entrada.

---

# 10. Position sizing adaptativo

El ATR permite relacionar el tamaño de la posición con la volatilidad.

Principio:

```text
riesgo monetario deseado
------------------------
distancia del stop
=
tamaño aproximado
```

Si el stop se define como un múltiplo del ATR:

```text
StopDistance = ATR × Multiplicador

PositionSize ≈
RiskBudget / StopDistance
```

En futuros hay que añadir el valor monetario por tick/punto del contrato.

El objetivo no es ganar más por operación, sino mantener controlado el riesgo.

---

# 11. Strategy Factory

La idea de mayor potencial del material es cambiar:

> “buscar el mejor bot”

por:

> “construir una fábrica que genere, pruebe y descarte estrategias”.

Arquitectura:

```text
GENERADOR DE HIPÓTESIS
          ↓
CODIFICADOR
          ↓
BACKTESTER
          ↓
ROBUSTNESS ENGINE
          ↓
RANKING
          ↓
OOS / WALK-FORWARD
          ↓
FORWARD
          ↓
PORTFOLIO
```

---

# 12. Portfolio de micro-bots

Una única estrategia tiene riesgo de deterioro.

Un portfolio puede combinar sistemas con:

- baja correlación;
- diferentes horizontes;
- diferentes regímenes;
- diferentes instrumentos.

La diversificación debe hacerse sobre **fuentes de riesgo realmente distintas**, no simplemente multiplicando variantes casi idénticas.

---

# 13. Portfolio Manager Engine

Una arquitectura posible:

```text
MARKET DATA
     ↓
REGIME ENGINE
     ↓
STRATEGY LIBRARY
     ↓
PERFORMANCE / ROBUSTNESS
     ↓
ALLOCATION ENGINE
     ↓
RISK ENGINE
     ↓
EXECUTION
```

Puede incluir:

- límites por estrategia;
- límites por instrumento;
- correlación;
- drawdown;
- reducción automática de tamaño;
- desactivación temporal.

---

# 14. Equity Curve Trading

Una estrategia puede reducirse o desactivarse cuando su comportamiento live se deteriora respecto a su distribución esperada.

Pero cuidado:

**no convertir esto en una regla optimizada sobre el pasado.**

La decisión debe definirse antes de evaluarla.

---

# 15. Monte Carlo

No sólo interesa:

> “¿Cuánto ganó?”

También:

> “¿Qué secuencias de pérdidas podrían aparecer?”

Monte Carlo puede utilizarse para estudiar:

- drawdown probable;
- rachas de pérdidas;
- sensibilidad a la secuencia;
- percentiles de resultados.

Para una cuenta con límites de drawdown, esto es especialmente importante.

---

# 16. Risk Engine independiente

La IA nunca debería tener autoridad absoluta sobre el dinero.

Arquitectura:

```text
AI / STRATEGY
      ↓
PROPUESTA DE ORDEN
      ↓
RISK ENGINE
      ↓
¿PERMITIDA?
  ↙       ↘
NO         SÍ
 ↓          ↓
RECHAZAR   EXECUTION
```

El Risk Engine debe poder bloquear una orden incluso cuando la estrategia quiera ejecutarla.

---

# 17. Guardrails mínimos

- pérdida máxima diaria;
- drawdown máximo;
- tamaño máximo;
- número máximo de posiciones;
- exposición por instrumento;
- límite de operaciones;
- horario permitido;
- protección de conexión;
- protección de órdenes duplicadas;
- kill switch;
- estado FLAT seguro después de determinados fallos.

---

# 18. Ejecución: el bot no termina en la señal

Una señal correcta puede convertirse en una operación incorrecta por:

- webhook perdido;
- API desconectada;
- token expirado;
- orden duplicada;
- fill parcial;
- stop no colocado;
- slippage;
- reconexión incorrecta;
- desincronización entre estado local y broker.

Por eso la arquitectura debe tener un **State Manager**.

---

# 19. Middleware

Rutas típicas:

```text
TradingView
    ↓
Webhook
    ↓
Middleware
    ↓
Broker / API
    ↓
Prop Firm
```

Herramientas investigadas:

- TradersPost;
- PickMyTrade;
- TradingView webhooks;
- Rithmic;
- Tradovate.

La elección depende de la prop, broker, API y reglas vigentes.

---

# 20. OCO server-side

Cuando sea compatible, los brackets OCO gestionados por el servidor son preferibles a depender exclusivamente del cliente.

Objetivo:

```text
ENTRY
  ↓
STOP + TARGET
  ↓
si uno se ejecuta → cancelar el otro
```

Esto reduce ciertos riesgos de desconexión del cliente, aunque siempre hay que comprobar el comportamiento exacto de la API.

---

# 21. Arquitectura recomendada final

```text
                 ┌───────────────────┐
                 │    MARKET DATA    │
                 └─────────┬─────────┘
                           ↓
                 ┌───────────────────┐
                 │ REGIME ENGINE     │
                 └─────────┬─────────┘
                           ↓
              ┌────────────┴────────────┐
              ↓                         ↓
       STRATEGY LIBRARY          NEW HYPOTHESES
              ↓                         ↓
              └────────────┬────────────┘
                           ↓
                 ┌───────────────────┐
                 │ VALIDATION ENGINE │
                 └─────────┬─────────┘
                           ↓
                 ┌───────────────────┐
                 │ PORTFOLIO ENGINE  │
                 └─────────┬─────────┘
                           ↓
                 ┌───────────────────┐
                 │ RISK ENGINE       │
                 └─────────┬─────────┘
                           ↓
                 ┌───────────────────┐
                 │ EXECUTION ENGINE  │
                 └─────────┬─────────┘
                           ↓
                 ┌───────────────────┐
                 │ MONITORING        │
                 └─────────┬─────────┘
                           ↓
                  FORWARD / LIVE DATA
```

---

# 22. Qué conservar y qué descartar

## Conservar

- IA como acelerador de investigación;
- Strategy Factory;
- validación OOS;
- walk-forward;
- Monte Carlo;
- análisis de régimen;
- sizing adaptativo;
- portfolio de estrategias;
- Risk Engine;
- separación entre señal y ejecución;
- monitorización.

## No considerar evidencia por sí solo

- backtests espectaculares;
- “win rate” aislado;
- screenshots;
- títulos de YouTube;
- resultados sin costes;
- una única muestra;
- estrategias optimizadas después de conocer el resultado.

---

# 23. Conclusión

La arquitectura con mayor potencial no es un “bot mágico”.

Es un **laboratorio cuantitativo automatizado** capaz de:

1. generar hipótesis;
2. codificarlas;
3. probarlas;
4. destruir las que tienen sesgos;
5. validarlas fuera de muestra;
6. probarlas forward;
7. combinarlas;
8. controlar el riesgo;
9. ejecutar;
10. retirar sistemas que dejan de comportarse como se esperaba.

Ese es el aprendizaje más valioso de la investigación de DaviddTech.
