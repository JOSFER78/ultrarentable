---
tipo: sub-nota
categoria: trading
estado: archivado
vigencia: legado
contexto_por_defecto: excluir
fecha: 2026-08-03
tags:
  - archivo
  - hyperliquid
  - obsoleto
  - polymarket
  - residuales
  - sub-nota
  - trading
  - ultrarentable
proyecto: 01 Ultrarentable
ficha_maestra: '[[Ultrarentable]]'
subtema: residuales
fecha_creacion: 2026-08-03
---

# Legado revisable de Ultrarentable

> Material antiguo conservado para comprobar si contiene código, datos o decisiones reutilizables. **No forma parte del contexto operativo de [[Ultrarentable]] y no se considera válido sin una nueva verificación.**

---

## 🎯 Navegación y Enlaces Bidireccionales
- 📌 **Ficha Maestra:** [[Ultrarentable]]
- 🔗 **Sub-notas Relacionadas:** [[Plan 10 Fases]]

---

## 1. Grid Hyperliquid
- **Qué era:** Un sistema de grids market-neutral operando en la L1 on-chain de Hyperliquid.
- **Situación:** No pertenece al Ultrarentable actual. Pendiente de revisar si conserva algún componente reutilizable; no debe asumirse que funciona.

## 2. Polymarket Rewards Harvester
- **Qué era:** Un script (`polymarket_rewards_scanner.py`) de market making que buscaba capturar subsidios por estrechar el spread en mercados de Polymarket.
- **Situación:** No forma parte de Ultrarentable. Su posible proyecto independiente se revisará por separado.

## 3. BingX Factory (Primigenio)
- **Qué era:** El entorno original de experimentación con BingX antes de la reestructuración a `ultrarentablev2/`.
- **Situación:** Fuente legacy prioritaria para comparar con la implementación actual, sin incorporar automáticamente sus resultados.

## 4. Kamikaze Lab
- **Qué era:** Scripts de alto riesgo sin filtros de drawdown. Evolucionó al actual sistema de "Balas y Estados", mucho más seguro.
- **Situación:** La idea de distribución extrema sigue vigente, pero el código y las conclusiones antiguas deben demostrarse de nuevo.

## Regla de rescate

Cada elemento se clasificará como `reutilizable`, `solo referencia` o `descartado`. Hasta completar esa revisión permanece fuera de la portada y del contexto normal del proyecto.
