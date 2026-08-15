# Sistema multiagente

## Regla

Los LLM proponen y explican; los motores deterministas calculan. Ningún agente puede inventar métricas ni declarar una estrategia ganadora sin artefactos del backtester.

## Roles MVP

### Coordinator

Divide campañas, controla presupuesto, reintentos y checkpoints.

### Researcher

Encuentra hipótesis y conserva fuente, fecha, mercado y supuestos.

### Strategy Architect

Traduce hipótesis a DSL y crea familias de plantillas.

### Evolution Designer

Propone mutaciones de estructura basándose en linajes y resultados.

### Simulation Auditor

Busca fugas, incoherencias y divergencias entre motores. No aplica filtros de drawdown.

### Reporter

Resume resultados sin alterar ranking.

## Memoria

Los agentes leen vistas estructuradas de la base de experimentos. No reciben miles de logs crudos cuando basta un resumen agregado y referencias a artefactos.
