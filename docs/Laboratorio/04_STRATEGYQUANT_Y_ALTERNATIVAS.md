# StrategyQuant y alternativas

## StrategyQuant

Fortalezas:

- generación masiva;
- evolución de reglas;
- optimización;
- pruebas de robustez;
- ecosistema orientado a estrategias automáticas.

Uso decidido: **generador especializado**, no plataforma única de verdad.

## Alternativas destacadas

- **Build Alpha:** amplitud de señales, construcción y portfolio.
- **Adaptrade:** programación genética tipada y control de complejidad.
- **EA Studio:** simplicidad y velocidad de uso.
- **QuantConnect LEAN:** motor abierto y extensible para investigación y backtest.
- **Freqtrade:** base práctica para estrategias cripto y ejecución experimental.
- **Optuna:** optimización flexible.
- **Ray:** paralelización y distribución.

## Qué no conviene reconstruir al principio

- motor de fills a nivel tick completamente propio;
- genética completa;
- editor visual avanzado;
- todos los exportadores;
- Monte Carlo genérico ya disponible en herramientas maduras.

## Qué sí debe ser propio

- formato de estrategia;
- base de experimentos;
- orquestación multiagente;
- fitness alineado con objetivos extremos;
- validación anti-overfitting;
- juez ciego;
- detector de régimen;
- monitor de degradación;
- Capital Guardian;
- integración con Hyperliquid.

## Criterio de elección

No preguntar solo «qué programa genera más estrategias», sino:

- qué datos acepta;
- qué supuestos de ejecución usa;
- cómo evita sesgo de selección;
- qué exporta;
- si permite reproducir resultados;
- cuánto cuesta integrar y auditar.
