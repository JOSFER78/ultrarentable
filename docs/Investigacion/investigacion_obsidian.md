# Investigación de Obsidian — Ultrarentable, Trading y Fondeo

**Fuente:** API REST de Obsidian vía `http://100.106.212.23:27123/vault/...`  
**Token usado:** `1329c7ead1d320dcdff9050ce998162ec0cda80a38b1c2827d9ac469215a8587`  
**Fecha de la investigación:** 2026-08-08  
**Nota metodológica:** Se consultó exclusivamente la bóveda viva por API REST. El espejo local `docs/` del proyecto **no** se usó como fuente primaria, pero se cita cuando existe **solo** en el espejo y no en la API REST, para indicar ausencia en la bóveda.

---

## 1. Notas relevantes encontradas en la API REST

### 1.1 `Ultrarentable.md`
- **Ruta API:** `/vault/proyectos/trading/01 Ultrarentable/Ultrarentable.md`
- **Tipo:** ficha maestra del proyecto (`tipo: proyecto`, `categoria: trading`, `estado: activo`, `foco_actual: true`, `prioridad: alta`).
- **Estado verificado declarado:** `implementacion_parcial_no_certificada` (última verificación 2026-08-04).
- **Citas textuales clave:**
  - > “Plataforma para crear, buscar, mejorar y comprobar estrategias de trading con **StrategyQuant X**.”
  - > “Del núcleo común salen dos líneas distintas: **Ultrarentable Extremo** … y **Fondeo de Futuros**.”
  - > “El modo extremo no descarta una estrategia por Sharpe, drawdown o una curva poco estable. Sí exige datos reales, contabilidad correcta, costes, margen, liquidaciones y resultados reproducibles.”
  - > “La inspección por SSH confirma que existen el proyecto actual y su copia antigua … Todavía **no está demostrado** que la aplicación completa funcione de extremo a extremo ni que produzca estrategias rentables.”
- **Resumen:** Es la ficha canónica. Define el proyecto como fábrica de estrategias sobre StrategyQuant X, con dos salidas económicas (extremo y fondeo), un pipeline de `StrategySpec` neutro y validación independiente. Marca el estado como parcial no certificado y establece la cadena objetivo: `generación → validación → simulación funded → paper/shadow → prueba limitada`.

---

### 1.2 `Estado verificado de Ultrarentable.md`
- **Ruta API:** `/vault/proyectos/trading/01 Ultrarentable/Estado verificado de Ultrarentable.md`
- **Tipo:** referencia de evidencia (`tipo: referencia`, `metodo_verificacion: inspeccion_local_y_ssh_solo_lectura`).
- **Citas textuales clave:**
  - > “No son copias idénticas. La actual cambia documentación de estado, interfaz y puente SQX, pero la antigua conserva varios archivos de configuración ausentes en la actual.”
  - > “Interfaz … `GET /` devolvió HTTP 200 … Esto no demuestra que sus acciones, datos ni backend funcionen.”
  - > “Backend … conexión rechazada en `127.0.0.1:8000` … Existe código, pero el servicio documentado no estaba levantado.”
  - > “StrategyQuant X … `GET /mcp` devolvió HTTP 400; el código mezcla valores predeterminados `8080` y `8081` … todavía no se ha demostrado una sesión MCP válida.”
  - > “Prop firms … Existe investigación; precios y reglas requieren verificación actual antes de usarse.”
- **Resumen:** Es la nota de “hechos comprobados vs no demostrado”. Confirma existencia de código e interfaz, pero rechaza certificar backend, bridge SQX, backtester canónico, fábrica evolutiva, motores económico/de fondeo, paper/shadow ni base de prop firms actualizada.

---

### 1.3 `Funcionamiento de Ultrarentable.md`
- **Ruta API:** `/vault/proyectos/trading/01 Ultrarentable/Funcionamiento de Ultrarentable.md`
- **Tipo:** referencia funcional (`tipo: referencia`, `categoria: trading`).
- **Citas textuales clave:**
  - > “Un motor ajeno a StrategyQuant repite el backtest para detectar resultados falsos, errores de datos, costes omitidos o reglas imposibles de ejecutar.”
  - > “El MVP comienza con Bitcoin y Ethereum. Cada bala puede perder el capital asignado. Las supervivientes deben alcanzar multiplicadores capaces de compensar las pérdidas y los costes del conjunto.”
  - > “El MVP prueba una sola combinación de proveedor, cuenta, instrumento, plataforma y estrategia.”
  - > “La validación exige ventanas por régimen, walk-forward, CPCV con purga y embargo, sensibilidad a costes, perturbación de parámetros, Monte Carlo, retrasos, operaciones eliminadas y repetición en un segundo motor.”
  - > “Codex investiga, organiza, implementa, prueba y controla actualmente el proyecto. Hermes queda como futura capa de ejecución supervisada … No es la fuente de verdad ni decide por sí solo que una estrategia está aprobada.”
- **Resumen:** Explica el núcleo común, los dos motores económicos y la metodología de validación reproducible. Define también la regla de actualización de la bóveda y el rol vigente Codex/Hermes.

---

### 1.4 `Trading.md`
- **Ruta API:** `/vault/proyectos/trading/Trading.md`
- **Tipo:** hub de categoría (`tipo: hub_categoria`, `categoria: trading`).
- **Citas textuales clave:**
  - > “**[[Ultrarentable]] — foco actual.** Fábrica y validación de estrategias con dos salidas: modo extremo y fondeo de futuros. Implementación parcial pendiente de certificación.”
  - > “[[Core Sistema Hermes]] podrá ejecutar tareas supervisadas cuando cada proyecto defina sus permisos y pruebas. No es la memoria ni la fuente de verdad de Trading.”
- **Resumen:** Confirma que Ultrarentable es el foco actual y repasa el estado resumido de los proyectos de trading. No contiene detalles adicionales de fondeo o backtesting más allá del resumen de Ultrarentable.

---

### 1.5 Notas contextuales del sistema (solo lectura)
- **`Dashboard.md`** (`/vault/Dashboard.md`): Confirma foco actual en Ultrarentable y su estado `implementacion_parcial_no_certificada`. No agrega teoría nueva de trading.
- **`agents.md`** (`/vault/agents.md`): Define protocolo de trabajo bóveda↔VPS, separación de verdad verificada vs legado, y que la VPS no reorganiza por analogía con Obsidian.
- **`Hermes.md`** (`/vault/proyectos/hermes/Hermes.md`) y **`Rol Operativo Codex y Hermes.md`**: Confirman que Hermes es capa futura supervisada; Codex dirige actualmente.

---

## 2. Teoría completa del proyecto según Obsidian

### 2.1 Objetivo general
Crear, buscar, mejorar y comprobar estrategias de trading usando **StrategyQuant X** como fábrica de candidatos, preservando la lógica en un formato neutro (`StrategySpec`) para poder traducirla a MetaTrader, TradingView, NinjaTrader u otra plataforma sin cambiar su lógica.

### 2.2 Pipeline canónico
```
Datos fiables
→ StrategyQuant X genera candidatos
→ StrategySpec conserva la lógica de forma neutral
→ validación independiente
→ Motor Extremo o Motor de Fondeo
→ simulación y paper/shadow
→ ejecución limitada
→ seguimiento y aprendizaje
```

### 2.3 Modo Extremo (Ultrarentable Extremo)
- Busca distribuciones convexas: muchas “balas” mueren y unas pocas multiplican el capital.
- **Criterio económico:** `valor terminal esperado = probabilidad_de_exito × M`. Esperanza positiva si supera `1` después de costes.
- Ejemplo teórico citado: `10x` con 10 % de éxitos y 90 % de pérdidas completas, antes de comisiones, funding, slippage y errores.
- **No descarta por:** Sharpe, drawdown, estabilidad de curva, concentración de beneficios, fragilidad paramétrica, etc.
- **Sí exige:** datos reales, contabilidad correcta, costes, margen, liquidaciones, resultados reproducibles.
- MVP inicial: Bitcoin y Ethereum; motor final no debe depender de un solo mercado.

### 2.4 Motor de Fondeo de Futuros
- Recibe estrategias reproducibles y las prueba contra las reglas exactas de una cuenta funded concreta.
- Reglas a modelar: objetivo de beneficio, drawdown y su forma de cálculo, pérdida diaria, contratos permitidos, horarios y noticias, consistencia, condiciones de automatización, costes de evaluación/activación/reinicios, requisitos de retirada.
- MVP: una sola combinación de proveedor, cuenta, instrumento, plataforma y estrategia.
- Secuencia prevista a compra de evaluación: verificar estrategia, verificar reglas vigentes del proveedor, ejecución simulada.

### 2.5 Validación independiente
- Motor ajeno a SQX repite el backtest para detectar resultados falsos, errores de datos, costes omitidos o reglas imposibles de ejecutar.
- Metodología obligatoria mencionada: ventanas por régimen, walk-forward, CPCV con purga y embargo, sensibilidad a costes, perturbación de parámetros, Monte Carlo, retrasos, operaciones eliminadas y repetición en un segundo motor.
- Se buscan “mesetas robustas, no el mejor resultado aislado”.

### 2.6 Criterios de investigación reutilizables
- Datos versionados de ETH perpetuo en 1m, 5m y 15m.
- Cambios aislados sobre señal, régimen, posición o ejecución.
- Juez ciego que evalúa sin acceder al bloque final de datos.
- Cada experimento conserva hipótesis, configuración, semilla, resultados por ventana, costes, funding y decisión de rechazo o promoción.

### 2.7 Rol operativo vigente
- **Codex** dirige investigación, implementación, pruebas y control.
- **Hermes** será capa futura de ejecución supervisada, telemetría y automatización; hoy no decide aprobaciones.

---

## 3. Estado declarado (qué dice Obsidian que está verificado vs no)

### 3.1 Verificado / demostrado
- Existe proyecto actual `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/` y copia antigua separada.
- Interfaz Next.js: proceso `next-server` en puerto `3000`; `GET /` devolvió HTTP 200.
- Existe código FastAPI en `services/api/`.
- Existe `StrategySpec` (`services/strategy_core/spec.py`) y pruebas asociadas.
- Existen datos iniciales ETH/BingX en varios marcos temporales y manifiestos.
- Existen artefactos de campañas y backtests en `data/artifacts/`.
- Existe investigación documental de prop firms y API con firmas codificadas.
- Documentación canónica actualizada al 2026-08-04.

### 3.2 No demostrado / pendiente
- Interfaz capaz de completar una operación real más allá de servir HTML.
- Backend FastAPI arrancando y comunicándose con la interfaz.
- Estrategia recorriendo la cadena completa `generación → validación → simulación funded → paper/shadow → prueba limitada`.
- StrategyQuant X estableciendo sesión MCP válida y entregando candidatos de extremo a extremo.
- Backtester independiente canónico implementado y aprobado.
- Fábrica evolutiva encontrando estrategias reproducibles y rentables.
- Motor extremo simulando correctamente conjuntos de balas y cosecha de beneficios.
- Motor de fondeo reproduciendo todas las reglas de una empresa real.
- Base de prop firms actualizada automáticamente; documento analiza como datos estáticos.
- Estrategia lista para paper, shadow o dinero real.

### 3.3 Estado prudente adoptado
**Implementación parcial no certificada** mientras no se ejecuten pruebas actuales.

---

## 4. Discrepancias y contradicciones internas

1. **Backtester / Fábrica / Motor rápido**  
   - `STATUS.md` y documento legado marcan algunos componentes como activos/completados.  
   - `Estado verificado de Ultrarentable.md` y `docs/CURRENT_IMPLEMENTATION_STATUS.md` declaran backtester canónico como no implementado, FAST Engine como no aprobado, fábrica evolutiva como no aprobada.

2. **BingX como límite vs MVP**  
   - Documentación anterior limitaba el modo extremo exclusivamente a BingX.  
   - Decisión vigente de Emilio: BingX/ETH/BTC son punto de partida del MVP, no el límite final del motor.

3. **Responsabilidad del sistema**  
   - Algunos documentos asignan a Hermes la dirección del sistema.  
   - Decisión vigente: Codex dirige; Hermes será capa futura supervisada.

4. **Rutas documentadas incorrectas**  
   - `README_MIGRACION.md` y `STATUS.md` referencian `C:\Obsidian\trading\01 Ultrarentable\`.  
   - Ruta real: `C:\Obsidian\proyectos\trading\01 Ultrarentable\`.

5. **Puertos del puente SQX**  
   - Documentación declara `8080`; parte del cliente menciona `8081`; endpoint de parada usa `8081` por defecto.  
   - Observación adicional: SQX MCP estaba respondiendo HTTP 400 en `/mcp`, sin sesión MCP válida demostrada.

6. **Migración actual/antigua**  
   - No son copias idénticas. La actual cambia documentación, interfaz y puente SQX, pero la antigua conserva archivos de configuración ausentes en la actual. Migración completa no certificada.

---

## 5. Requisitos de fondeo mencionados

### 5.1 Reglas del motor de fondeo (de `Funcionamiento de Ultrarentable.md`)
- Objetivo de beneficio.
- Drawdown y forma de cálculo.
- Pérdida diaria.
- Contratos permitidos.
- Horarios y noticias.
- Consistencia.
- Condiciones de automatización.
- Costes de evaluación, activación y reinicios.
- Requisitos de retirada.

### 5.2 Alcance MVP de fondeo
- **Una sola combinación:** proveedor, cuenta, estrategia, plataforma, instrumento.
- Debe demostrar primero en histórico y simulación que puede aprobar y respetar las reglas.
- Solo después pasa a paper, shadow y prueba limitada autorizada por Emilio.

### 5.3 Base de prop firms
- Existe documento comparativo y endpoint API con firmas codificadas.
- Estado declarado: datos estáticos; no actualización automática verificada.
- Nota de `Estado verificado`: precios y reglas requieren verificación actual antes de usarse.

### 5.4 Documento exclusivo del espejo local (no presente en API REST)
- En `docs/PROP_FIRMS_DATABASE_INTERACTIVE.md` existe una base comparativa de firmas de fondeo de futuros 2026 con calificaciones, drawdown, tarifas, splits y fórmula de coste efectivo real.  
- **Importante:** ese archivo **no aparece** en la API REST de Obsidian; su contenido está solo en el espejo local `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/docs/`.  
- `docs/DEBATE_MULTIAGENTE_NORMALIZACION_FONDEO.md` también recoge un debate multiagente sobre normalización de cohortes y métricas por `$1K de drawdown`, con selección por defecto en cohorte `50K` y columna `Coste / $1K DD`. Tampoco está referenciado desde la API REST.

---

## 6. Mapa de notas leídas y rutas API

| Nota | Ruta API | Rol |
|---|---|---|
| `Ultrarentable.md` | `/vault/proyectos/trading/01 Ultrarentable/Ultrarentable.md` | Ficha maestra |
| `Estado verificado de Ultrarentable.md` | `/vault/proyectos/trading/01 Ultrarentable/Estado verificado de Ultrarentable.md` | Evidencia |
| `Funcionamiento de Ultrarentable.md` | `/vault/proyectos/trading/01 Ultrarentable/Funcionamiento de Ultrarentable.md` | Teoría |
| `Trading.md` | `/vault/proyectos/trading/Trading.md` | Hub categoría |
| `Dashboard.md` | `/vault/Dashboard.md` | Panel sistema |
| `agents.md` | `/vault/agents.md` | Protocolo agentes |
| `Hermes.md` | `/vault/proyectos/hermes/Hermes.md` | Hub Hermes |
| `Rol Operativo Codex y Hermes.md` | `/vault/proyectos/hermes/01 Core Sistema Hermes/Rol Operativo Codex y Hermes.md` | Roles |
| `wiki/Analisis_Conexion_Obsidian.md` | `/vault/wiki/Analisis_Conexion_Obsidian.md` | Investigación conexión |
| `raw/importaciones/chatgpt-antiguo-2026-08-04/IMPORTACION_CHATGPT_ANTIGUO.md` | `/vault/raw/importaciones/chatgpt-antiguo-2026-08-04/IMPORTACION_CHATGPT_ANTIGUO.md` | Histórico |

---

## 7. Hallazgos adicionales

- **El vault vivo no contiene notas adicionales de fondeo/backtesting/StrategyQuant** más allá de las tres notas canónicas de Ultrarentable y el hub Trading.md.
- El material detallado de **prop firms**, **debatemultiagente de normalización de fondeo**, **backtester canónico**, **visión de producto** y **planes de arquitectura** existe exclusivamente en el espejo local `docs/` del proyecto, no en la bóveda de Obsidian accesible por API REST.
- No se detectaron notas en `/vault/diario/` relevantes para Ultrarentable/fondeo (solo existe `_LEEME.md`).
- No se detectaron notas en `/vault/raw/` relevantes ya procesadas para Ultrarentable/fondeo (solo wrapper de importación histórica).

---

## 8. Resumen ejecutivo

1. **Teoría:** Ultrarentable es una fábrica sobre StrategyQuant X con dos motores económicos: modo extremo (`valor terminal esperado = probabilidad_de_exito × M`) y fondeo de futuros (una sola combinación MVP).
2. **Estado real declarado:** código e interfaz existen; backend, bridge SQX, validadores, backtester canónico, fábrica evolutiva, motores y ejecución real **no están certificados**.
3. **Contradicciones principales:** estados contradictorios entre documentos legado y `Estado verificado`; rutas documentadas erróneas; conflictos de puertos `8080/8081`; desalineación sobre responsabilidad Hermes vs Codex.
4. **Fondeo:** motor requiere emular reglas completas de proveedores; existe investigación estática de prop firms en el espejo local, pero no actualizada automáticamente ni referenciada desde la API REST viva.
5. **Fuente de verdad:** las 3 notas canónicas de `/vault/proyectos/trading/01 Ultrarentable/` son lo único vigente en Obsidian; todo lo demás sobre backtesting/fondeo detallado está solo en `docs/` del proyecto.
