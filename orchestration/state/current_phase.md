# Fase 6 — Monitoreo Continuo 24/7, Telemetría de Metas y Certificación Desatendida de Ruta FONDEO

> **Asignada por el Orquestador (Hermes L1)**. Ejecución en modo multi-agente por Antigravity.

## Objetivo
Consolidar el régimen de operación continua 24/7 para el sistema Ultrarentable: asegurar el monitoreo telemétrico en vivo del embudo de certificación, certificar las primeras estrategias verificadas 11/11 gates para la ruta **FONDEO** (Prop Firm hard limits) y extender los ensamblados de Meta-Estrategias a ambas rutas (ULTRA + FONDEO) expuestas en los endpoints REST y frontend UI.

## Requisitos de Ejecución Multi-Agente
- **Subagente 1 (Engine & Discovery):** Mantener activo el lazo de discovery 24/7 multiclave (112 datasets × trials) y ejecutar pases dedicados a los símbolos de FONDEO (EURUSD, GBPUSD, USDCAD, ES, NQ).
- **Subagente 2 (Certificación & Fondeo):** Ejecutar la batería de 11 gates sobre candidatos FONDEO aplicando estrictamente los límites de Prop Firm (Max DD $\le 5\%$, Profit Target $\ge 8\%$, DSR $\ge 85\%$). Persistir sellos criptográficos SHA-256 en DB canónica.
- **Subagente 3 (UI & Telemetría):** Verificar que los endpoints `/api/v2/certified/strategies` y `/api/v2/certified/meta-strategies` sirvan dinámicamente las nuevas certificaciones FONDEO y que la vista `/estrategias` de Next.js las renderice sin fallos.

## Criterio de Éxito Verificable
- [ ] ≥1 estrategia de ruta FONDEO certificada con `APPROVED_CURRENT_ENGINE` + 11/11 gates + sello SHA-256 en disco y DB.
- [ ] `GET /api/v2/certified/strategies?route=FONDEO` respondiendo `HTTP 200` con la estrategia FONDEO certificada.
- [ ] Meta-Estrategia FONDEO Risk-Parity ensamblada dinámicamente en `/api/v2/certified/meta-strategies`.
- [ ] Uptime del servicio systemd `ultrarentable-api.service` y lazo de watchdog activos sin interrupciones.

## Reglas Inquebrantables
- CERO datos inventados (REAL-ONLY).
- NUNCA `git commit` ni `git push` automáticos.
- NUNCA borrar (`rm`). Persistencia total en disco y DB canónica SQLite.
