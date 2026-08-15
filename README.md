# 🎯 Ultrarentable — Laboratorio de Estrategias de Trading (BingX + StrategyQuant X)

> **Guía de entrada para cualquier IA o persona que retome el proyecto.**
> Lee este archivo primero. Luego `ESTADO.md` para saber cómo vamos. Luego la bitácora (`plan_implementacion/bitacora/`) para el historial de sesiones.

---

## 1. Qué es este proyecto

Ultrarentable es un laboratorio para **descubrir, validar y desplegar estrategias de trading algorítmico** sobre futuros perpetuos de BingX, usando **StrategyQuant X (SQX)** como motor de búsqueda genética de estrategias.

El proyecto tiene dos modos de operación:

| Modo | Objetivo | Drawdown | Estilo |
|------|----------|----------|--------|
| **ULTRA (Kamikaze)** | Estrategias de **miles de %** de retorno | Sin filtro de DD (solo ruina real DD≥100%) | Se quema la cuenta 8/10 veces; las 2 que sobreviven pagan todo |
| **FONDEO** | Aprobar exámenes de prop firms | DD bajo, consistencia obligatoria | Conservador, reglas estrictas |

**Ruta canónica (FUENTE ÚNICA):** `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

⚠️ Existen copias obsoletas en otros paths — **NO tocarlas**. Solo esta ruta es válida.

---

## 2. Servicios y cómo ver/abrir la web

Todos los servicios corren 24/7 en el VPS vía `systemd --user`.

| Servicio | Comando de estado | Puerto | Acceso |
|----------|-------------------|--------|--------|
| **Frontend Next.js** | `systemctl --user status ultrarentable-web` | `0.0.0.0:3000` | VPS: `http://localhost:3000` · PC: `http://100.104.148.117:3000` |
| **API FastAPI** | `systemctl --user status ultrarentable-api` | `0.0.0.0:8000` | Proxeado por el frontend en el mismo origen (:3000 → :8000) |
| **StrategyQuant X** | `systemctl --user status strategyquantx` | MCP `127.0.0.1:8080` · Web UI `127.0.0.1:5050` | Solo VPS local |

### Cómo abrir la web

- **Desde el VPS:** `http://localhost:3000` en cualquier navegador.
- **Desde el PC del usuario (vía Tailscale):** `http://100.104.148.117:3000`
- **Desde Hermes Desktop:** el preview carga la web por la IP Tailscale; la API se proxea en el mismo origen (sin CORS).

### Rutas principales de la web

| Ruta | Función |
|------|---------|
| `/` | Consola de búsqueda de estrategias (home) |
| `/strategyquant` | Laboratorio SQX vía MCP |
| `/bifurcacion/ultrarentable` | Proceso Ultra (kamikaze) |
| `/bifurcacion/fondeo` | Proceso Fondeo |
| `/leaderboard` | Ranking de estrategias |

> **Nota técnica:** El frontend proxea la API por rewrites en `apps/web/next.config.ts` para evitar problemas de CORS.

---

## 3. StrategyQuant X (SQX)

SQX es el motor de búsqueda genética de estrategias. Corre en el VPS 24/7.

| Componente | Detalle |
|------------|---------|
| **Proceso** | `systemctl --user status strategyquantx` |
| **GUI/Electron** | Corre en Xvfb `DISPLAY=:99` (sin monitor físico) |
| **MCP (Machine Control Protocol)** | `http://127.0.0.1:8080/mcp` — permite controlar SQX programáticamente |
| **Web UI (parcial)** | `http://127.0.0.1:5050` — interfaz web limitada |
| **Instalación** | `/home/ubuntu/StrategyQuantX` |

### Doctrina de uso de SQX

- **NO usar scripts hardcodeados** para buscar estrategias.
- La IA debe **entrar en StrategyQuant y usarlo como un experto**, aprovechando sus muchas variables, bloques genéticos, y configuraciones.
- Ver `plan_implementacion/GUIA_EXPERTO_USAR_SQUANT.md` para el flujo completo.

---

## 4. Obsidian (teoría del usuario)

La teoría, planes y notas de investigación del usuario viven en **Obsidian** en su PC Windows.

### Acceso desde el VPS

| Método | Disponibilidad | Detalle |
|--------|----------------|---------|
| **Espejo local `docs/`** | ✅ Siempre | Copia local en este proyecto — usar cuando el PC esté apagado |
| **API REST vía Tailscale** | ⚡ Cuando el PC está encendido | `http://100.106.212.23:27123` |

### Uso de la API REST de Obsidian

```bash
# Leer una nota
curl -H "Authorization: Bearer 1329c7ead1d320dcdff9050ce998162ec0cda80a38b1c2827d9ac469215a8587" \
  http://100.106.212.23:27123/vault/proyectos/trading/01%20Ultrarentable/<nota>.md

# Buscar en la bóveda
curl -H "Authorization: Bearer 1329c7ead1d320dcdff9050ce998162ec0cda80a38b1c2827d9ac469215a8587" \
  "http://100.106.212.23:27123/search/?query=kamikaze"
```

**Cliente Python disponible en:**
`/home/ubuntu/workspace/pro/hermes/01 Gestor Conexión Hermes PC y Obsidian/scripts/obsidian_client.py`

### Mapeo de rutas Obsidian ↔ VPS

| Obsidian (PC) | VPS |
|---------------|-----|
| `C:\Obsidian\proyectos\trading\01 Ultrarentable` | `/home/ubuntu/workspace/pro/trading/01 Ultrarentable` |

---

## 5. Cómo hacer seguimiento — Continuar el proyecto

> **Regla: cualquier IA que retome el proyecto debe seguir este flujo de lectura.**

### Flujo de lectura al incorporarse

```
0. MULTIAGENTE_Y_SEGUIMIENTO.md  ← PRIMERO: cómo se trabaja (orquestador + subagentes)
                                    y cómo se hace seguimiento/actualización.
1. README.md          ← Estás aquí. Entiende qué es y cómo acceder.
2. ESTADO.md          ← Resumen vivo: qué está hecho, qué falta, próximo paso.
3. plan_implementacion/bitacora/<fecha>.md  ← Historial cronológico de sesiones.
4. plan_implementacion/*.md  ← Documentos de investigación y planes detallados.
5. docs/              ← Espejo de teoría de Obsidian + investigaciones.
```

> 📌 **`MULTIAGENTE_Y_SEGUIMIENTO.md`** es el documento maestro: explica el modelo
> orquestador-multiagente (analiza → manda → comprueba → verifica) y el sistema de
> seguimiento/actualización exacto. Léelo antes que nada si eres un agente nuevo.

### Estructura de seguimiento

| Archivo/Carpeta | Propósito |
|-----------------|---------|
| `MULTIAGENTE_Y_SEGUIMIENTO.md` | **Documento maestro**: modelo multiagente + sistema de seguimiento/actualización + convención de registro. |
| `ESTADO.md` | **Estado vivo del proyecto.** Qué está hecho (✅), qué falta (🔴), próximo paso concreto. Se actualiza al final de cada sesión. |
| `plan_implementacion/bitacora/` | **Bitácora cronológica.** Una entrada `.md` por fecha de sesión (ej: `2026-08-09.md`). Registra qué se hizo, qué se descubrió, decisiones tomadas, y cómo continuar. |
| `plan_implementacion/*.md` | **Documentos de investigación y planes.** Blueprint, guías, auditorías, orquestación. |
| `docs/` | **Espejo de teoría de Obsidian** + investigaciones propias del VPS. |

### Convención de registro

- **Al terminar cada sesión de trabajo**, actualizar `ESTADO.md` y crear/actualizar la entrada de bitácora del día.
- **Cada búsqueda de estrategias** debe registrar: configuración usada, resultados obtenidos (con métricas reales), y conclusiones.
- **Nunca dejar el proyecto sin indicar el próximo paso** en `ESTADO.md`.

---

## 6. Doctrina y reglas clave

### 🔴 REAL-ONLY (regla inquebrantable)

**Prohibido inventar métricas, resultados de backtest, o datos financieros.** Todo debe venir de ejecución real (SQX, backtest verificable) con evidencia. Si no hay datos, se dice "no hay datos".

### 🎯 Objetivo

- **ULTRA:** Estrategias de **miles de % de retorno** en backtest. Se acepta ruina (DD≥100%) en la mayoría de runs. El objetivo es encontrar las pocas que sobreviven con retornos explosivos.
- **FONDEO:** Estrategias que aprueben exámenes de prop firms con DD controlado y consistencia.

### 🧠 Uso de SQX como experto

- No hardcodear búsquedas con scripts fijos.
- Usar SQX con sus variables nativas (bloques genéticos, fitness personalizado, universo de indicadores).
- Ver `plan_implementacion/GUIA_EXPERTO_USAR_SQUANT.md`.

### 🔒 Otras reglas

- **Fuente única:** solo trabajar en `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`.
- **No reiniciar servicios sin avisar** (corren 24/7).
- **Tests canónicos:** `services/api/tests/` (no `tests/` raíz, que está obsoleto).
- **BD operacional:** `~/.local/state/ultrarentable/ultrarentable.sqlite3`.
- **Syncthing ELIMINADO** — no hay sincronización automática PC↔VPS.

---

## 7. Estado actual resumido

> Para el estado detallado y actualizado, ver `ESTADO.md`.

### ✅ Hecho

- Investigación consolidada: catálogo de 28 técnicas, informe máster de trading bots.
- Blueprint del controlador de estrategias mundial (`BLUEPRINT_CONTROLADOR_ESTRATEGIAS_MUNDIAL.md`).
- Guía de uso experto de SQX (`GUIA_EXPERTO_USAR_SQUANT.md`).
- Auditoría de candidatos kamikaze con scorecard de calidad (`AUDITORIA_CANDIDATOS_KAMIKAZE.md`).
- Core backend con modo Ultra/Fondeo + configurador (125 tests passing).
- Panel configurador IA en la web (frontend Next.js funcionando).
- SQX desbloqueado y generando candidatos reales (serie 4.1.x).
- Servicios desplegados 24/7 (API, web, SQX).
- Acceso a Obsidian vía Tailscale REST verificado.

### 🔴 Pendiente

- **Ningún candidato de miles de %** encontrado aún (mejor actual: ~2.24% IS retorno).
- Afinar búsqueda kamikaze nivel 2: fitness personalizado por retorno, universo ampliado de indicadores, más generaciones.
- Resolver acceso GUI virtual de SQX para inspección visual.
- Plan de orquestación del motor de búsqueda (`ORQUESTACION_MOTOR_BUSQUEDA_20260809.md`).
- Completar pipeline fondeo (prop firms con cuenta gratis).

---

## 8. Documentos clave de referencia

| Documento | Ubicación | Contenido |
|-----------|-----------|----------|
| Blueprint controlador | `plan_implementacion/BLUEPRINT_CONTROLADOR_ESTRATEGIAS_MUNDIAL.md` | Protocolo para validar estrategias de miles de % |
| Guía experto SQX | `plan_implementacion/GUIA_EXPERTO_USAR_SQUANT.md` | Cómo usar SQX como experto: GUI, variables, flujo kamikaze y fondeo |
| Auditoría candidatos | `plan_implementacion/AUDITORIA_CANDIDATOS_KAMIKAZE.md` | Scorecard de calidad + diagnóstico de candidatos |
| Orquestación motor | `plan_implementacion/ORQUESTACION_MOTOR_BUSQUEDA_20260809.md` | Plan de orquestación del controlador de estrategias |
| Plan maestro 12 fases | `docs/Estado/PLAN_MAESTRO_12_FASES.md` | Plan modular del proyecto completo |
| Investigación consolidada | `docs/Investigacion/01_TRADING_BOTS_INVESTIGACION_CONSOLIDADA.md` | Catálogo de 28 técnicas y análisis |
| Estado del sistema real | `docs/Estado/estado_sistema_real.md` | Estado técnico verificado del sistema |
| Prop firms gratis | `docs/Fondeo/prop_firms_cuenta_gratis.md` | Investigación de prop firms con cuenta gratis |
