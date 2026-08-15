# Plan de Control GUI de StrategyQuant X (preparación — fase de reconfiguración)
> Proyecto: Ultrarentable · Fecha: 2026-08-09 · Estado: **PREPARADO / en espera de plantillas**
> Este documento es la parte de infraestructura que NO depende de los informes 03-06.
> La reconfiguración CONCRETA de SQX se ejecutará cuando los agentes 3/4 entreguen las plantillas A/B.

---

## Objetivo
Preparar el canal de control de la GUI real de SQX (`computer_use` / `xdotool` / `import`) de forma que,
cuando lleguen las plantillas Perfil A/B definidas por los agentes 3/4, la reconfiguración se ejecute
de inmediato sin fricción de infraestructura.

## Regla de oro del proyecto
> La IA debe **ENTRAR en la GUI real de StrategyQuant** y usarla como un humano experto (Builder,
> evolución genética, bloques, plantillas). **NO scripts hardcodeados** que llaman `run_project` con
> parámetros fijos. (Doctrina: `ORQUESTACION_MOTOR_BUSQUEDA_20260809.md`)

## Estado verificado del canal (2026-08-09, VPS)
| Elemento | Estado | Evidencia |
|---|---|---|
| Xvfb `:99` | Corriendo | ventanas StrategyQuant detectadas |
| Ventana SQX | Visible, 1920x1029 @ (0,75) | `xdotool`: WID=58720260 |
| Captura `import` | ✅ Funciona | `/tmp/sqx_window.png` 368KB OK |
| Clic/teclado `xdotool` | ✅ Canal fiable (XTEST) | skill computer-use-linux-xvfb |
| `computer_use` capture (som) | ⚠️ Devuelve 0x0 | conocido en Xvfb; usar `import`+xdotool en su lugar |
| Web UI SQX | ✅ `http://127.0.0.1:5050` (HTTP 200) | alternativa a GUI X11 |
| Modelo con visión para leer menús | ⚠️ DeepSeek V4 Flash **no acepta imágenes** | limitación a resolver al ejecutar la reconfiguración |

## Canal de control RECOMENDADO (probado en este host)
Seguir la skill `computer-use-linux-xvfb`:
```bash
export DISPLAY=:99; export XAUTHORITY=/home/ubuntu/.Xauthority
WID=$(xdotool search --onlyvisible --name "StrategyQuant" | head -1)
eval $(xdotool getwindowgeometry --shell $WID)   # X,Y,WIDTH,HEIGHT
# clic en coords de pantalla = origen_ventana + offset_local
xdotool mousemove $((X+dx)) $((Y+dy)) click 1
# teclado
xdotool type "text"; xdotool key Return
# capturar para verificar
import -window "$WID" /tmp/sqx_check.png
```
> `computer_use(action="capture", mode="som")` NO es fiable aquí (devuelve 0x0): usar SIEMPRE `import -window`.
> Los clics nativos de cua-driver sufren EPERM en Xvfb; **`xdotool` (XTEST) es el canal fiable**.

## Alternativa: Web UI :5050
- SQX expone una web UI en `127.0.0.1:5050` (verificada HTTP 200). Puede permitir navegación del databank
  y resultados sin X11. Aunque la doctrina del proyecto pide la GUI completa del Builder (que es X11),
  la web UI sirve de respaldo de verificación.

## Bloqueo actual (transparencia)
- El modelo activo del orquestador (DeepSeek V4 Flash) **no acepta imágenes**, por lo que el orquestador
  NO puede "leer" visualmente los menús de SQX ahora mismo.
- **Resolución:** la tarea de reconfiguración GUI se asignará a un subagente con **modelo multimodal**
  (o se hará vía web UI :5050 textual). El canal X ya está preparado y esperando.
- Verificación eventual con el usuario: ofrecer screenshot entregado vía perfil `images/` cuando se ejecute.

## Siguientes pasos (dependientes)
1. ⏳ Esperar entregas de agentes 3 (`05_plantilla_sqx_perfiles_ab.md`) y 4 (`06_plan_accion_multiagente.md`).
2. Según las plantillas, crear la secuencia exacta de clic/teclado en la GUI para configurar:
   - Perfil A (Growth): fitness CAGR OOS + Kelly, bloques de momentum, filtros sesión/régimen.
   - Perfil B (Fondeo): fitness P(pasar challenge) + DD intrabar, bloques conservadores.
3. Ejecutar la reconfiguración en la GUI real con el subagente multimodal y verificar con capturas.

*Documento de infraestructura preparado por el orquestador. La ejecución concreta queda tras los informes 03-06.*
