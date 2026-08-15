# Valoración final de arquitectura

## Lo acertado de la propuesta inicial

- Métrica de crecimiento compuesto sencilla.
- Regla explícita de liquidada/superviviente.
- DSL en lugar de Python arbitrario.
- Ventanas reproducibles.
- Paralelización y memoria de experimentos.
- Separación de agentes por rol.

## Cambios necesarios

### 1. No usar un solo backtester

Una búsqueda masiva necesita velocidad, pero el ranking final necesita fidelidad. Por eso se requieren dos motores.

### 2. No confundir “no filtrar” con “solo probar una ventana”

Las ventanas adicionales no eliminan estrategias; sirven para catalogar en qué situaciones funcionan. Así se preservan estrategias de régimen específico.

### 3. Separar ranking provisional y canónico

Un resultado vectorizado puede ser líder provisional, nunca ganador definitivo.

### 4. Mantener diversidad evolutiva

Sin nichos, el algoritmo converge a clones y deja de descubrir mecanismos nuevos. La diversidad estructural no es un filtro financiero.

### 5. Modelo de liquidación por exchange

No existe una fórmula universal. El exchange de referencia debe ser un adaptador versionado.

### 6. Empezar con ETH 5m/15m

Los documentos del proyecto están centrados en ETH, tres años y ventanas de tres meses. El 1m se incorpora cuando el replay intrabar y el modelo de ejecución estén probados.

## Expectativa correcta

El sistema puede encontrar backtests con multiplicadores de miles por ciento. No puede garantizar que esas estrategias existan de forma repetible ni que sobrevivan en vivo. El objetivo del MVP es distinguir rápidamente entre:

- multiplicador producido por una regla real bajo el simulador;
- multiplicador producido por una ventana/regímen concreto;
- multiplicador falso por ejecución, look-ahead o liquidación mal modelada.
