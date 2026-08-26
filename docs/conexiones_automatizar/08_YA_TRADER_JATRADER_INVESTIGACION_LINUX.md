---
tipo: investigacion
proyecto: 01 Ultrarentable
categoria: conexiones-automatizar
fecha: 2026-08-25
ficha_maestra: "[[Ultrarentable]]"
estado: activo
tags: [ultrarentable, ya-trader, jatrader, daytradr, rithmic, linux-arm64, headless]
---

# 🔍 "YA Trader" / "JA Trader" en Linux — Investigación y Resolución

> **Pregunta original:** "investiga cómo usar un ya trader en linux... te dejé unas notas que decían que se podía al principio".
> **Verificación previa:** NO existe ninguna nota en el proyecto (`docs/`, `00_INICIO.md`, bitácoras, sesiones) mencionando "ya trader" ni "JA trader". Búsqueda exhaustiva: 0 resultados.

## 1. Veredicto: no existe ninguna plataforma llamada "JA/Ya Trader"

Tras búsqueda web exhaustiva (Jigsaw Trading, Optimus Futures, Rithmic, MarketsWiki, Earn2Trade, foros), **no existe ningún producto oficial llamado "JA Trader", "JATrader" o "Ya Trader"**. Es una de estas tres confusiones:

| Origen probable | Explicación |
|---|---|
| 🎙️ Dictado fonético de "**daytradr**" (Jigsaw Trading) | En español, "daytradr"/"day trader" se dicta como "deitrader/yeitrader/**ya trader**". Jigsaw es EL referente DOM/order-flow de prop firms |
| 🕰️ Confusión histórica con "**J-Trader**" (Patsystems) | Plataforma DMA institucional de los 2000s **basada en Java** → por eso notas antiguas decían "se podía en Linux al principio" (Java era multiplataforma). Hoy está obsoleta; ninguna prop firm la soporta |
| 👂 Confusión con R\|Trader Pro (Rithmic) o NinjaTrader | Similitud de nombres |

## 2. Las candidatas reales y su compatibilidad Linux ARM64

| Plataforma | Proveedor | ¿Linux ARM64 headless? | ¿API bots? | Prop firms |
|---|---|---|---|---|
| daytradr | Jigsaw | ❌ Solo Windows x86 (.NET+DirectX). Sin web, sin headless. Doble emulación Box64+Wine = inviable producción | ❌ No (solo ATM manual) | Se conecta vía Rithmic/CQG (Apex, Leeloo, UProfit) |
| J-Trader | Patsystems/ION | Obsoleta | — | Ninguna |
| R\|Trader Pro | Rithmic | ⚠️ Parcial: GUI web (`rtrader.rithmic.com`) + **R\|API+ nativa C++ Linux y WebSockets protobuf** para bots | ✅ | Apex, Bulenox, MFFU |
| **Tradovate API** | Tradovate/NinjaTrader | ✅ **100% nativa cloud (REST+WS)** — LA recomendada | ✅ | Topstep(via ProjectX ahora), Apex, Bulenox, MFFU |

## 3. Respuesta a la preocupación de fondo ("si es un puente hacia un PC y el PC se corta")

- Con **Tradovate API no existe puente ni PC**: tu VPS habla directo con el cloud del broker. Nada que se corte.
- El único escenario con host Windows sería una firma que EXIJA plataforma NinjaTrader/Jigsaw → se resuelve con **VPS Windows barato (~$10–30/mes)** siempre encendido, nunca con tu PC doméstico.
- Kill-switch FAIL-CLOSED: si la conexión cae, el bot cancela órdenes y aplana posiciones. Posición huérfana = imposible.

## 4. Conclusión operativa (coherente con docs 02/03)

1. **Ruta principal:** Tradovate API desde tu VPS ARM64 Python/Hermes — cero Windows, cero puentes, 24/7 real.
2. **Si una firma exige Rithmic:** usar R|API+/WebSockets directamente desde Linux (sin R|Trader desktop).
3. **daytradr/Jigsaw:** descartado para automatización (sin API); solo útil si algún día quieres DOM manual.
4. La nota que recordabas casi seguro se refería a Java (J-Trader legacy) o a NautilusTrader — este último **SÍ corre nativo en Linux** y es tu motor canónico (`[[ESPECIFICACION_COMPLETA_NAUTILUSTRADER_ULTRARENTABLE]]`).

## Fuentes
- https://www.jigsawtrading.com (daytradr: requisitos Windows-only)
- https://www.optimusfutures.com (specs daytradr)
- https://www.rithmic.com (R|API+, WebSockets)
- https://api.tradovate.com (REST/WS cloud)
- https://www.marketswiki.com/wiki/Patsystems (J-Trader legacy)
- https://www.earn2trade.com (plataformas soportadas prop firms)
