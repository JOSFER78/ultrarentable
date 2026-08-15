# BASE DE DATOS COMPARATIVA DE EMPRESAS DE FONDEO DE FUTUROS

## Precios reales, activaciones, reglas, retiros, reputación, fiabilidad y compatibilidad con automatización

**Fecha de investigación:** 2 de agosto de 2026  
**Zona horaria:** Europe/Madrid  
**Ámbito:** empresas públicas de evaluación y fondeo de futuros accesibles a traders minoristas  
**Cuenta de referencia para precios:** 50.000 USD, salvo que se indique otra cosa  
**Uso previsto:** selección de proveedores para el proyecto Ultra Rentable / Hermes / StrategyQuant  
**Estado:** fotografía de mercado. Los precios, promociones y reglas pueden cambiar incluso el mismo día.

---

# 1. Resumen ejecutivo

El mercado de fondeo de futuros ha crecido muy rápido. Existen decenas de marcas, pero no todas tienen la misma antigüedad, capacidad financiera, transparencia, historial de pagos ni compatibilidad con estrategias automáticas.

La primera conclusión es que no existe una única “mejor empresa”. La elección depende de cinco preguntas:

1. ¿Se operará manualmente o con StrategyQuant?
2. ¿Se necesita una API real o basta con NinjaTrader/Tradovate?
3. ¿Se quiere copiar una operación entre varias cuentas propias?
4. ¿Se busca el menor precio posible o la mayor seguridad de cobro?
5. ¿Se quiere permanecer en simulación con retiros o avanzar a una cuenta real?

La segunda conclusión es que el precio anunciado casi nunca representa el coste económico completo. Hay que separar:

- precio de la evaluación;
- descuento efectivo;
- mensualidades hasta aprobar;
- activación;
- reset o recompra;
- plataforma y datos;
- buffer previo a retirada;
- porcentaje que puede retirarse;
- límite por retiro;
- número máximo de retiros;
- coste de las cuentas que se pierden.

La tercera conclusión es especialmente importante para Ultra Rentable:

> **Una empresa puede ser buena para trading discrecional y completamente inadecuada para StrategyQuant.**

En agosto de 2026:

- **Apex Trader Funding** prohíbe bots, algoritmos y automatización de la cuenta originadora. Permite copiar operaciones manuales entre cuentas propias, pero no utilizar una estrategia automática como origen.
- **Take Profit Trader** prohíbe los bots y sistemas automáticos, aunque permite copiadores entre cuentas propias cuando la decisión y ejecución original son del trader.
- **Topstep** permite estrategias automáticas en evaluación y Express Funded y ofrece una API oficial de TopstepX/ProjectX, pero prohíbe ejecutar esa API desde VPS, VPN o servidores remotos. Además, la API de ProjectX no está permitida en la cuenta Live Funded.
- **My Funded Futures** permite estrategias automáticas propias, pero prohíbe HFT, abuso de fills simulados y copia entre traders diferentes.
- **FundedNext Futures** permite EAs y bots propios y permite copiar entre cuentas que pertenezcan al mismo titular. Sin embargo, prohíbe expresamente el *account rolling*: comprar muchas cuentas para sacrificar algunas y hacer avanzar otras de manera agresiva.
- **Tradeify** permite bots personales con límites: deben ser propios, no HFT y no compartidos con otros traders.
- **TradeDay** permite sistemas automáticos propios bajo sus reglas, pero prohíbe bots de terceros y no expone directamente la API de Tradovate.

Por ello, la línea de fondeo de Ultra Rentable debe mantenerse separada de la línea “kamikaze” de múltiples balas. El concepto de sacrificar muchas cuentas de forma deliberada puede ser considerado *account stacking*, *account rolling* o conducta no sostenible por determinadas firmas.

---

# 2. Alcance y límites de esta investigación

No existe un registro oficial mundial de todas las empresas de fondeo de futuros. Además:

- aparecen empresas nuevas continuamente;
- algunas desaparecen;
- otras cambian de nombre o producto;
- muchas páginas comparadoras contienen enlaces de afiliado;
- los precios se personalizan según campaña, país, cookie o enlace;
- una misma empresa puede tener varias generaciones de cuentas con reglas diferentes;
- las cuentas antiguas pueden conservar reglas “legacy” que ya no se venden.

Esta base incluye:

## Grupo principal: firmas activas y visibles en 2026

- Apex Trader Funding
- AquaFutures
- Atlas Funded Futures
- Blue Guardian Futures
- Blueberry Futures
- Bulenox
- DayTraders
- Elite Trader Funding
- For Traders Futures
- FundedNext Futures
- FundedSeat
- FuturesElite
- FXIFY Futures
- Goat Funded Futures
- Hola Prime Futures
- Lucid Trading
- My Funded Futures
- Phidias Prop Firm
- Take Profit Trader
- The5ers Futures
- Top One Futures
- TradeDay
- Tradeify

## Firmas consolidadas o relevantes que algunas listas modernas omiten

- Topstep
- Earn2Trade
- OneUp Trader
- UProfit
- TickTickTrader
- Leeloo Trading
- Alpha Futures
- E8 Futures
- Funded Futures Family
- Traders Launch
- The Trading Pit Futures

En total se revisan **34 marcas o programas**. No significa que todas merezcan utilizarse.

---

# 3. Metodología de evaluación

Cada firma se valora con siete dimensiones.

| Dimensión | Peso | Qué se analiza |
|---|---:|---|
| Fiabilidad de retiro | 25 % | Evidencia pública de pagos, reglas, reclamaciones y capacidad aparente |
| Antigüedad y continuidad | 15 % | Años operando y estabilidad del programa |
| Claridad de reglas | 15 % | Drawdown, consistencia, prohibiciones, discrecionalidad |
| Coste efectivo | 15 % | Evaluación, activación, mensualidades y resets |
| Condiciones de retiro | 10 % | Días, buffer, límites, frecuencia y porcentaje |
| Tecnología y automatización | 10 % | API, NinjaTrader, Tradovate, bots y copiadores |
| Soporte y transparencia | 10 % | Documentación, respuesta y publicación de cambios |

Las notas son una **valoración analítica**, no una auditoría financiera.

## Escala utilizada

- **A+ / A:** máxima confianza relativa dentro de este sector.
- **A- / B+:** firma sólida, pero con alguna limitación material.
- **B / B-:** utilizable con precaución y pruebas limitadas.
- **C:** emergente, reglas complejas o evidencia insuficiente.
- **Vigilancia:** no utilizar como proveedor principal sin nuevas verificaciones.

## Cómo se valora el cobro

Ninguna de estas señales por sí sola demuestra solvencia:

- puntuación de Trustpilot;
- capturas en redes sociales;
- un “payout certificate”;
- testimonios de influencers;
- volumen de afiliados;
- afirmaciones de la propia empresa.

Se combinan:

- historial temporal;
- documentación oficial;
- existencia de ruta a live;
- volumen de comentarios;
- reclamaciones repetidas;
- evidencia independiente;
- rastreadores de pagos;
- claridad contractual;
- cambios de reglas;
- facilidad o dificultad real de cumplir la retirada.

---

# 4. Advertencia esencial sobre el modelo de negocio

La mayoría de estas compañías **no son brokers ni FCM regulados**. Muchas venden una evaluación en simulación y, tras aprobar, mantienen al trader en una cuenta simulada desde la que pagan recompensas reales.

Esto no significa automáticamente que sean fraudulentas, pero sí implica:

- el saldo mostrado no es necesariamente capital real depositado a nombre del trader;
- el pago depende del contrato con la empresa;
- la empresa puede revisar conductas y cumplimiento;
- las reglas pueden ser más importantes que la rentabilidad;
- la supervivencia de la empresa depende de su gestión financiera y de su modelo de ingresos.

Los datos públicos del sector muestran tasas de éxito bajas. Topstep publicó que en 2024 aproximadamente el 12,4 % de los participantes consiguió financiación y que el 28,3 % de los financiados recibió al menos un pago. Earn2Trade publicó para 2025 que el 8,89 % de las nuevas suscripciones aprobó y que alrededor del 18 % de sus cuentas live o LiveSim realizó al menos una retirada.

Por tanto:

> El coste esperado no es el precio de una evaluación. Es el precio medio de todas las evaluaciones necesarias hasta conseguir un retiro.

---

# 5. Fórmula correcta del coste

## 5.1. Coste de acceso a una cuenta financiada

```text
Coste hasta financiación =
evaluaciones compradas
+ renovaciones
+ resets
+ activación
+ datos
+ plataforma
```

## 5.2. Coste hasta primer retiro

```text
Coste hasta primer retiro =
coste hasta financiación
+ cuentas financiadas perdidas antes de cobrar
+ meses adicionales
+ costes de ejecución
- reembolsos de evaluación
```

## 5.3. Coste económico real de una estrategia

```text
Beneficio neto =
retiros cobrados
- evaluaciones
- activaciones
- resets
- plataformas
- datos
- comisiones
- impuestos
```

Una firma que vende una evaluación por 20 USD puede ser más cara que otra de 100 USD si cobra 150 USD de activación o limita mucho las retiradas.

---

# 6. Clasificación general de confianza

## Nivel 1 — Proveedores prioritarios

| Firma | Nota analítica | Motivo principal |
|---|---:|---|
| Topstep | 87/100 · A | Máxima antigüedad, ruta real a live, API oficial y estadísticas públicas |
| Earn2Trade | 84/100 · A- | Programa antiguo, oferta de partner real/LiveSim y reglas documentadas |
| TradeDay | 83/100 · A- | Desde 2020, sin activación, reglas claras y ruta a live |
| My Funded Futures | 82/100 · A- | Fuerte actividad de pagos, sin activación y automatización propia permitida |
| OneUp Trader | 80/100 · A- | Modelo con socios de financiación, coste simple y trayectoria larga |

## Nivel 2 — Proveedores utilizables con condiciones

| Firma | Nota | Condición importante |
|---|---:|---|
| Apex Trader Funding | 78/100 · B+ | Gran escala y evidencia de pagos, pero no sirve para bots |
| Tradeify | 78/100 · B+ | Barato, bots personales permitidos y actividad de pagos; empresa joven |
| Bulenox | 76/100 · B+ | Buen historial relativo, pero activación y reglas de retiro más pesadas |
| Take Profit Trader | 74/100 · B | Cobros rápidos y marca conocida, pero prohíbe automatización |
| Lucid Trading | 73/100 · B | Reglas modernas y claras; historial más corto |
| FundedNext Futures | 72/100 · B | Bots y copia propia permitidos; programa de futuros reciente y cambiante |
| Alpha Futures | 70/100 · B | Documentación razonable y pagos visibles; empresa joven |
| UProfit | 69/100 · B- | Marca conocida y productos nuevos; verificar reglas concretas |
| TickTickTrader | 68/100 · B- | Trayectoria suficiente, pero muchos modelos y reglas complejas |
| Elite Trader Funding | 66/100 · B- | Gran variedad y descuentos; complejidad elevada |

## Nivel 3 — Experimentales o secundarios

AquaFutures, Atlas, Blue Guardian Futures, Blueberry Futures, DayTraders, For Traders Futures, FundedSeat, FuturesElite, FXIFY Futures, Goat Funded Futures, Hola Prime Futures, Phidias, The5ers Futures, Top One Futures, E8 Futures, Funded Futures Family, Traders Launch y The Trading Pit Futures.

Estas empresas pueden ser válidas, pero no deberían ser el primer destino de un sistema automático con capital operativo hasta acumular más evidencia propia.

---

# 7. Clasificación específica para StrategyQuant y Hermes

## Mejores candidatos para un MVP automático

### 1. My Funded Futures

- Permite estrategias automáticas propias.
- Prohíbe HFT y explotación de simulación.
- No cobra activación en Rapid.
- Tiene pagos diarios en determinados planes.
- Puede pasar a capital real.
- El precio de 50K Rapid se ha mostrado alrededor de 79 USD antes de descuentos.
- El código promocional `300K` anunciaba un 50 % en la fecha de consulta.

**Riesgo:** debe poder demostrarse que el algoritmo es propio, razonable y replicable en mercado real.

### 2. Topstep

- Permite automatización.
- Ofrece API oficial TopstepX/ProjectX.
- La API cuesta 29 USD/mes; Topstep anunciaba un descuento permanente del 50 % con código `topstep`.
- Permite copiar entre cuentas propias.
- Tiene una ruta definida a cuenta real.

**Limitaciones críticas:**

- el tráfico debe originarse en el dispositivo personal;
- VPS, VPN y servidores remotos están prohibidos;
- ProjectX API no está permitida en la Live Funded Account;
- prohíbe *account stacking* y estrategias que exploten fills simulados.

Es adecuada para un MVP local, pero no encaja directamente con un Hermes ejecutándose exclusivamente en una VPS remota.

### 3. FundedNext Futures

- Permite bots y EAs tanto en Challenge como en cuenta financiada.
- Permite copiadores entre cuentas del mismo titular e incluso entre firmas si todas pertenecen al mismo titular.
- Prohíbe HFT, latencia, grids, spam de órdenes y explotación de fills.
- Prohíbe expresamente sacrificar cuentas mediante *account rolling*.
- Rapid Pro 50K se anunciaba a 149,99 USD; con add-on de DLL, 109,99 USD.
- No requiere activación adicional en sus modelos actuales.

**Riesgo:** reglas y productos han cambiado muy rápido en 2026. Debe versionarse la ficha del proveedor.

### 4. Tradeify

- Permite bots personales.
- Prohíbe bots compartidos y HFT.
- No cobra activación en Growth/Select.
- Precio orientativo 50K: Growth 97 USD y Select 107 USD antes de promociones.
- Código `TNT`: 40 % en las primeras cinco compras, según la página de promociones consultada.
- Evidencia pública de pagos relativamente activa.

### 5. TradeDay

- Acepta sistemas propios bajo reglas de mercado real.
- Prohíbe bots comprados de terceros.
- No entrega acceso directo a la API de Tradovate.
- Puede integrarse mediante NinjaTrader u otra capa admitida.
- 50K desde 59 USD y sin activación en la campaña observada.
- Ruta a cuenta live.

## Empresas no adecuadas para StrategyQuant automático

### Apex Trader Funding

La documentación de 2026 prohíbe:

- automatización;
- bots;
- scripts;
- lógica preprogramada;
- algoritmos como origen de la operativa.

El copiador es aceptable únicamente cuando la operación original se introduce manualmente por el titular.

### Take Profit Trader

Prohíbe:

- sistemas automáticos;
- bots;
- ejecución algorítmica.

Permite copiadores entre cuentas propias, pero no convierte una estrategia de StrategyQuant en operativa permitida.

### Earn2Trade

Aunque puede aceptar determinadas herramientas de trading, desde 2026 no permite copiar operaciones entre sus cuentas. Esto reduce su utilidad para una futura granja de cuentas.

---

# 8. Comparativa de costes de una cuenta 50K

Los importes son en USD y representan una fotografía del 2 de agosto de 2026. Los códigos pueden caducar. Cuando una web utiliza precio dinámico se indica “checkout”.

| Firma / plan | Precio base 50K | Promoción observada | Activación | Coste aproximado si se aprueba a la primera | Observación |
|---|---:|---:|---:|---:|---|
| Topstep Standard | 49/mes | No general verificada | 149 | 198 en el primer mes | Si tarda más, se suman meses |
| Topstep sin activación | 95/mes | — | 0 | 95 en el primer mes | Más caro si tarda varios meses |
| Apex EOD / Intraday | Dinámico | hasta 90 %, `SAVENOW` | Según modalidad | Confirmar en checkout | Tiene productos con activación y variantes sin activación |
| MFFU Rapid | 79/mes | 50 %, `300K` | 0 | ~39,50 si el código aplica | Gran precio, validar fecha |
| Take Profit Trader | 170/mes | 40 % + activación 0, `NOFEE40` | 0 en promo | 102 | Sin promo: activación aproximada 130 |
| TradeDay Intraday | 131 base / 59 oferta | 55 % ya reflejado | 0 | 59 | Mensual hasta aprobar |
| TradeDay EOD → funded intraday | 175 / 79 | 55 % | 0 | 79 | EOD solo en evaluación |
| TradeDay EOD completo | 189 / 85 | 55 % | 0 | 85 | Reglas de retiro más restrictivas |
| Earn2Trade Gauntlet Mini | desde 68 | Variable | Sin pago inicial; se descuenta del primer retiro | desde 68 de caja | Confirmar precio 50K en checkout |
| Bulenox 50K | 175/mes | 89 %, `GUIDE` | 148 | ~167,25 | La activación domina el coste |
| OneUp Trader 50K | 75/mes | Sin código general verificado | 75 | 150 | Reset 50 |
| UProfit ONE 50K | 120 | Variable | 0 | 120 | Plan concreto; comprobar política vigente |
| Tradeify Growth | 97 | 40 %, `TNT` | 0 | ~58,20 | Primeras cinco compras |
| Tradeify Select | 107 | 40 %, `TNT` | 0 | ~64,20 | Un solo pago, sin activación |
| FundedNext Rapid Pro 50K | 299,98 base | 149,99 lanzamiento | 0 | 149,99 | Con DLL add-on: 109,99 |
| LucidFlex 50K | Precio checkout | 50 %, `VAULT`, dos usos | 0 | Confirmar | Una sola tarifa, sin mensualidad |
| Alpha Futures 50K eval | ~119–129 según plan | Variable | Según plan | ~119–129 | Direct Qualified 50K: 519 |
| Elite Trader Funding | Plan variable | 90 %, `GUIDE` | 47–307 según tamaño/plan | Variable | Muy importante revisar el producto exacto |
| DayTraders | Variable | 85 %, `GUIDE` | Anunciada como 0 | Checkout | Marca joven |
| Hola Prime Futures | Variable | activación 0 + posible devolución | 0 | Checkout | Código `HOLAJUL35` parece ligado a julio: verificar |

## Interpretación

El precio promocional más bajo no siempre es el mejor:

- MFFU y Tradeify combinan descuento con activación cero.
- Bulenox parece muy barato hasta sumar 148 USD.
- Topstep sin activación es barato si se aprueba pronto.
- Apex necesita verificar el producto exacto; existen cuentas estándar y “all-in” sin activación.
- Take Profit Trader es atractivo con `NOFEE40`, pero no sirve para automatización.
- TradeDay tiene un coste total muy claro, pero su split inicial puede ser inferior al de competidores.

---

# 9. Promociones y códigos observados

## Advertencia

Los códigos de afiliado:

- pueden dejar de funcionar sin aviso;
- pueden aplicarse solo a nuevos clientes;
- pueden tener máximo de usos;
- normalmente no cubren activación ni reset;
- no cambian las reglas ni el porcentaje de retiro;
- pueden crear una comisión para la página que los publica.

Siempre se debe abrir una ventana privada, comparar el precio oficial y capturar la pantalla final antes de pagar.

| Firma | Oferta observada | Código | Alcance |
|---|---:|---|---|
| Apex | hasta 90 % | `SAVENOW` | Evaluaciones nuevas; no activación ni reset |
| Elite Trader Funding | 90 % | `GUIDE` | Planes seleccionados |
| Bulenox | 89 % | `GUIDE` | Option 1 |
| DayTraders | 85 % | `GUIDE` | Trail Accounts |
| Phidias | 80 % | `GUIDE` | OTP Premium y Fundamental |
| Top One Futures | 72 % | `GUIDE` | Elite Access |
| FundedSeat | 60 % | `GUIDE` | Primera compra |
| Blueberry Futures | 60 % | `GUIDE` | Evaluaciones |
| TradeDay | 55 % + activación 0 | `GUIDE` | Según producto |
| FundedNext Futures | 55 % | `JLFLEX` | Flex, nuevos usuarios |
| AquaFutures | 50 % | `GUIDE` | Nuevos clientes |
| For Traders Futures | 50 % | `GUIDE` | 1 Step Fast Pro |
| Goat Funded Futures | 50 % | `GUIDE` | Todas las cuentas |
| My Funded Futures | 50 % | `300K` | Todas las cuentas anunciadas |
| Lucid Trading | 50 % | `VAULT` | Dos usos |
| Atlas Funded Futures | 40 % | `GUIDE` | Todas las cuentas |
| Take Profit Trader | 40 % + activación 0 | `NOFEE40` | Tests |
| Tradeify | 40 % | `TNT` | Primeras cinco compras |
| FuturesElite | 35 % | `GUIDE` | Prime |
| FXIFY Futures | 30 % | `GUIDE` | Todas las cuentas |
| Blue Guardian Futures | 25 % | `GUIDE` | Todas las cuentas |
| The5ers Futures | 10 % | `GUIDE` | Todas las cuentas |
| Hola Prime Futures | activación 0 + devolución | `HOLAJUL35` | Verificar: nombre ligado a julio |

**Regla operativa para Hermes:** ninguna promoción se almacena como precio permanente. Debe guardarse con:

```yaml
code:
discount:
first_seen:
last_verified:
eligible_products:
activation_included:
max_uses:
source:
checkout_verified:
```

---

# 10. Análisis detallado de las principales firmas

# 10.1. Topstep

## Perfil

- Fundada en 2012.
- Es una de las precursoras del modelo moderno de evaluación de futuros.
- Tiene sede y trayectoria empresarial reconocibles.
- Dispone de Express Funded en simulación y Live Funded con capital real.
- Lanzó acceso API oficial en TopstepX durante 2026.

## Cuenta 50K

### Ruta Standard

- 49 USD mensuales.
- 149 USD de activación al aprobar.
- Coste si se aprueba en el primer mes: 198 USD.

### Ruta sin activación

- 95 USD mensuales.
- Activación 0.
- Coste si se aprueba en el primer mes: 95 USD.

### Reglas principales

- Objetivo: 3.000 USD.
- Maximum Loss Limit.
- Consistencia: mejor día inferior al 50 % del objetivo.
- Puede aprobarse en dos días.
- Máximo aproximado: 5 minis o 50 micros.

## Retiros

- Express Funded ofrece rutas basadas en días ganadores o consistencia.
- Split general: 90/10.
- Existen límites por retiro en Express.
- La cuenta puede ser trasladada a Live.
- En Live, después de suficientes días de referencia se puede desbloquear hasta el 100 % de la parte disponible.

## Automatización

- Permitida con condiciones.
- API TopstepX/ProjectX: 29 USD/mes.
- Descuento anunciado para clientes Topstep: 14,50 USD/mes con `topstep`.
- Prohibido operar desde VPS, VPN o servidor remoto.
- API ProjectX prohibida en Live Funded.
- El trader es responsable de cualquier fallo del algoritmo.

## Fiabilidad de cobro

**Muy alta dentro del sector.**

Puntos positivos:

- mayor antigüedad;
- ruta real a live;
- estadísticas públicas;
- volumen grande;
- reglas documentadas.

Puntos negativos:

- incidencias técnicas de TopstepX en 2025 afectaron reputación;
- Trustpilot se situaba alrededor de 3,6/5 con más de 14.000 opiniones en la captura consultada;
- soporte y plataforma recibieron críticas durante periodos de alta demanda.

## Veredicto

La mejor referencia institucional y una de las mejores opciones para un MVP automático **si la ejecución se realiza desde un equipo personal**. No encaja sin cambios con un Hermes que opere solo desde VPS.

**Nota: 87/100.**

---

# 10.2. Earn2Trade

## Perfil

- Una de las marcas más antiguas del sector.
- Se presenta como empresa de educación y evaluación.
- Tras aprobar, garantiza una oferta de una firma socia.
- Ofrece LiveSim y posibilidad de cuenta real.

## Gauntlet Mini 50K

- Precio anunciado desde 68 USD.
- Objetivo: 3.000 USD.
- Drawdown EOD: 2.000 USD.
- Pérdida diaria: 1.100 USD.
- Consistencia: 30 %.
- Hasta 6 contratos.
- Sin días mínimos.
- Noticias permitidas.

## Cuenta financiada

- LiveSim o Live.
- Sin activación pagada por adelantado.
- Sin mensualidad después de aprobar.
- Sin consistencia para retirar.
- Sin buffer adicional indicado.
- Retiros semanales.
- Split:
  - 50 % por debajo del primer umbral;
  - 80 % una vez superado.

## Multiplicación de cuentas

- Hasta cinco evaluaciones concurrentes.
- Menor número en financiadas.
- Desde 2026 no permite copiadores entre sus programas.

## Fiabilidad

**Alta.**

Ventajas:

- antigüedad;
- ruta a socio de financiación;
- estadísticas de aprobaciones y retiros;
- condiciones financiadas sin activación inicial.

Desventajas:

- daily loss limit;
- split inicial inferior al 90–100 % que anuncian otras;
- no permite copiar operaciones;
- relación contractual final puede depender del partner.

## Veredicto

Excelente para validar una estrategia y acceder a una relación de financiación más tradicional. Menos apropiada para una granja de cuentas replicadas.

**Nota: 84/100.**

---

# 10.3. TradeDay

## Perfil

- Fundada en 2020.
- Fundadores con experiencia profesional declarada en futuros.
- Combina evaluación, Funded Sim y transición a Funded Live.
- No cobra activación.

## Precios 50K observados

| Modalidad | Precio actual | Regla principal |
|---|---:|---|
| Intraday | 59/mes | Drawdown intradía |
| EOD evaluación / intradía financiada | 79/mes | EOD al evaluar |
| EOD completo | 85/mes | EOD en financiada, más consistencia |

## Reglas

- Objetivo: 3.000 USD.
- Drawdown: 2.000 USD.
- 5 contratos / 50 micros.
- Consistencia:
  - 30 % en modalidades estándar;
  - 45 % en la modalidad EOD completa.
- Días mínimos:
  - 5 en las primeras;
  - 3 en EOD completo.

## Retiro

### Modelo estándar

- Sin buffer.
- Posible desde el primer día elegible.
- Mínimo 250 USD.
- Split:
  - 50/50 por debajo de 4.000 USD netos;
  - 80/20 por encima;
  - 90/10 en live.

### EOD financiada

- Cinco días rentables.
- 150 USD diarios en 50K.
- Máximo de 1.500 USD por solicitud.
- Split 80/20 en sim y 90/10 en live.

## Automatización

- Sistemas automáticos propios pueden utilizarse bajo la política.
- Bots comprados a terceros están prohibidos.
- No ofrece la API Tradovate directamente al trader.
- Puede requerir NinjaTrader o una integración permitida.

## Fiabilidad

**Alta.**

Puntos positivos:

- sin activación;
- precios claros;
- ruta live;
- documentación;
- Trustpilot alrededor de 4,6 con más de 1.300 opiniones y respuesta elevada a negativas.

Puntos negativos:

- split inicial 50 % en determinadas cuentas;
- diferencia entre drawdown de evaluación y financiada en algunas rutas;
- automatización no tan sencilla como una API abierta.

## Veredicto

Uno de los mejores equilibrios entre coste, claridad y viabilidad. Muy buen candidato para una primera cuenta si el adaptador técnico encaja.

**Nota: 83/100.**

---

# 10.4. My Funded Futures

## Perfil

- Crecimiento muy rápido desde 2023.
- Amplia variedad de planes.
- Fuerte volumen visible de opiniones y pagos.
- Ruta de transición a capital real.

## Rapid 50K

- Precio observado: 79 USD/mes.
- Código anunciado: `300K`, 50 %.
- Activación: 0.
- Objetivo: 3.000 USD.
- Drawdown EOD en evaluación: 2.000 USD.
- Sin daily loss limit.
- Cinco minis / 50 micros en evaluación.
- Consistencia 50 % solo en evaluación.
- Puede aprobarse en dos días.

## Retiros Rapid

- Buffer para 50K: alrededor de 2.100 USD.
- Retiro diario tras cumplir condiciones.
- Split 90/10.
- Sin consistencia en la fase financiada Rapid.
- Puede pasar a cuenta real por decisión de riesgo.

## Automatización

- Estrategias automáticas propias permitidas.
- HFT prohibido.
- Prohibido explotar fills simulados.
- Prohibida copia entre traders distintos.
- El algoritmo debe respetar reglas CME cuando pase a live.

## Fiabilidad

**Alta, con menor antigüedad que Topstep.**

Ventajas:

- activación cero;
- precio bajo;
- pagos frecuentes;
- automatización propia;
- Trustpilot alrededor de 4,9 con más de 20.000 opiniones en la captura consultada;
- aparece entre firmas con actividad frecuente en rastreadores de pagos.

Riesgos:

- crecimiento muy rápido;
- varias generaciones de planes;
- una puntuación de reseñas extraordinariamente alta no sustituye auditoría;
- cambios de reglas y productos deben versionarse.

## Veredicto

Probablemente el mejor equilibrio inicial para un sistema automático de StrategyQuant, siempre que se mantenga baja frecuencia, lógica propia y ejecución realista.

**Nota: 82/100.**

---

# 10.5. OneUp Trader

## Perfil

- Marca veterana del sector.
- Se define como empresa de reclutamiento que conecta traders con firmas de financiación.
- Utiliza socios de funding.

## Precio 50K

- 75 USD al iniciar.
- 75 USD de activación tras aprobar.
- Total inicial: 150 USD.
- Reset: 50 USD.

## Reglas y financiada

- Hasta 6 contratos en evaluación.
- Posibilidad de 60 micros.
- Comisión simulada de 2,50 USD por lado, excepto micros.
- Tras aprobar se revisan resultados y se firma con el partner.
- Los costes de intercambio pueden cubrirse según el acuerdo de funding.

## Retiros

Las condiciones dependen parcialmente del socio y del umbral de la cuenta. La documentación muestra ejemplos de saldo mínimo antes de retirar.

## Fiabilidad

**Alta relativa.**

Ventajas:

- trayectoria larga;
- precio simple;
- financiación a través de partner;
- menor dependencia de marketing masivo.

Riesgos:

- términos finales del partner;
- menos información pública agregada de pagos que Topstep o MFFU;
- hay que verificar automatización y copia para el acuerdo exacto.

## Veredicto

Buena empresa para diversificar proveedor después del MVP. No sería la primera integración técnica sin confirmar antes el acuerdo de automatización.

**Nota: 80/100.**

---

# 10.6. Apex Trader Funding

## Perfil

- Fundada en 2021.
- Una de las marcas de mayor escala.
- Permite hasta 20 Performance Accounts.
- Desde el 1 de marzo de 2026 vende una generación nueva de productos; las cuentas anteriores son Legacy.

## Cuenta nueva EOD 50K

- Objetivo: 3.000 USD.
- Drawdown EOD: 2.000 USD.
- Daily Loss Limit: 1.000 USD.
- Máximo: 6 contratos.
- Sin consistencia en evaluación.
- Acceso de 30 días.
- Pago único, sin renovación automática.
- Existen variantes estándar con activación y variantes “All-In” sin activación.

## Retiro EOD 50K

- Cinco días con al menos 250 USD de beneficio diario.
- Safety Net: 52.100 USD.
- Saldo mínimo para solicitar: 52.600 USD.
- Consistencia del 50 %.
- Mínimo de retiro: 500 USD.
- Máximo seis retiros por PA.
- Split anunciado: 100 % de la cantidad aprobada.

## Precios y promociones

- Código oficial: `SAVENOW`.
- Hasta 90 % en evaluaciones.
- El descuento no se aplica a activación ni resets.
- Los importes exactos dependen de tipo de cuenta y checkout.
- No comprar sin capturar el coste total de evaluación más PA.

## Evidencia de pagos

- Gran volumen de pagos declarado por la empresa.
- Business Insider verificó mediante recibos y extractos un pago acumulado de aproximadamente 1,9 millones USD a un trader en 2024.
- Trustpilot rondaba 4,2 con más de 20.000 opiniones.

## Problemas y restricciones

- Automatización y algoritmos prohibidos.
- La cuenta originadora debe operarse manualmente.
- Copia permitida entre cuentas propias en la misma dirección.
- Máximo total de 20 PA.
- Dos días de al menos 50 USD dentro de cada ventana móvil de 30 días para evitar cierre por inactividad.
- Reglas Legacy y nuevas son distintas.

## Fiabilidad

**Alta capacidad de pago, pero riesgo contractual superior a Topstep.**

Apex ha demostrado que puede realizar pagos grandes. No obstante, la firma ha sufrido críticas por revisiones, cierres y cambios de reglas en generaciones anteriores. La nueva estructura intenta simplificar el proceso, pero todavía debe probarse a lo largo del tiempo.

## Veredicto

Buena opción para trading manual y grupos de cuentas, pero **no debe utilizarse para StrategyQuant automático**.

**Nota general: 78/100. Compatibilidad automática: muy baja.**

---

# 10.7. Tradeify

## Perfil

- Firma joven, aproximadamente dos años de trayectoria.
- Programas Growth, Select y alternativas directas.
- Activación cero en Growth/Select.
- Ruta de sim a live.

## Precios 50K

- Growth: alrededor de 97 USD.
- Select: alrededor de 107 USD.
- Código `TNT`: 40 % en las primeras cinco compras.
- Total promocional orientativo:
  - Growth: 58,20 USD;
  - Select: 64,20 USD.

## Reglas

- Objetivo 50K: 3.000 USD.
- Growth:
  - drawdown alrededor de 2.000 USD;
  - daily loss limit;
  - máximo 4 contratos / 40 micros.
- Select:
  - otra combinación de evaluación y elección de payout.
- EOD trailing que puede bloquearse tras alcanzar determinado saldo.

## Automatización

- Bots personales permitidos.
- Deben ser de uso exclusivo del trader.
- No HFT.
- No compartir el bot entre firmas o personas de forma prohibida.
- Hay que revisar la política completa antes de desplegar.

## Retiro

- Split general 90 % en planes promocionados.
- Opciones de retiro diario o por ciclos, según Select/Growth.
- No activación.
- Actividad visible en rastreadores de pagos.

## Fiabilidad

**Media-alta.**

Ventajas:

- precio;
- automatización;
- documentación;
- Trustpilot alrededor de 4,6 con miles de opiniones;
- pagos frecuentes observables.

Riesgo principal: menor antigüedad.

## Veredicto

Uno de los mejores proveedores secundarios para el sistema automático.

**Nota: 78/100.**

---

# 10.8. Bulenox

## Perfil

- Opera desde principios de la década de 2020.
- Utiliza Rithmic/NinjaTrader y modelos de Master Account.
- Tiene descuentos muy agresivos.

## 50K

- Precio regular aproximado: 175 USD/mes.
- Promoción `GUIDE`: 89 % en Option 1.
- Precio promocional aproximado: 19,25 USD.
- Activación: 148 USD.
- Total a primera aprobación: 167,25 USD.

## Reglas

- Objetivo: 3.000 USD.
- Drawdown: aproximadamente 2.500 USD según opción.
- Daily loss en determinadas cuentas: 1.100 USD.
- Hasta 7 contratos en evaluación.
- Escalado en Master.

## Retiro

- Primeros retiros con límites.
- Diez días de negociación para determinados ciclos.
- Safety threshold.
- Primeros tres retiros 50K con tope aproximado de 1.500 USD.
- Primeros 10.000 USD al 100 % y después 90 %, según programa.

## Fiabilidad

**Media-alta.**

- Trustpilot alrededor de 4,7 con más de 1.700 opiniones.
- Antigüedad superior a muchas firmas nuevas.
- El problema no es tanto cobrar como cumplir correctamente reglas, umbrales y ciclos.

## Veredicto

Adecuada para diversificar, pero la activación reduce mucho el atractivo del descuento.

**Nota: 76/100.**

---

# 10.9. Take Profit Trader

## Perfil

- Marca conocida y enfocada en retiros rápidos.
- Test 50K a 170 USD/mes.
- PRO en simulación y PRO+ conectado al mercado por invitación.

## Reglas 50K

- Objetivo: 3.000 USD.
- Drawdown EOD: 2.000 USD.
- Daily Loss Limit de 1.100 USD, que puede retirarse según fase.
- Máximo 6 contratos / 60 micros.
- Sin regla de consistencia tradicional.
- Bots prohibidos.
- Posiciones contrarias prohibidas.

## Precio

- Precio normal: 170 USD.
- Activación habitual aproximada: 130 USD.
- Promoción observada: `NOFEE40`.
  - 40 % de descuento.
  - activación 0.
  - total aproximado: 102 USD.
- En mayo de 2026 existió `NOFEE50`, total 85 USD, pero fue temporal y no debe considerarse vigente.

## Retiros

- PRO permite solicitudes rápidas.
- Split 90 %.
- Sin espera mínima anunciada en algunos productos.
- Permite copiador entre cuentas propias.
- PRO+ es una ruta a ejecución real.

## Fiabilidad

**Media-alta, pero con controversias contractuales.**

Ventajas:

- rapidez;
- marca visible;
- pagos reales desde cuentas simuladas;
- Trustpilot alrededor de 4,3 con más de 10.000 opiniones.

Riesgos:

- aproximadamente 12 % de opiniones de una estrella en la captura;
- política estricta contra bots;
- reclamaciones públicas sobre detección de comportamiento automatizado;
- la empresa puede clasificar patrones como no independientes.

## Veredicto

Válida para trading discrecional, no para el motor automático de StrategyQuant.

**Nota: 74/100.**

---

# 10.10. Lucid Trading

## Perfil

- Firma joven, con productos desarrollados especialmente en 2025–2026.
- Documentación detallada.
- Modelos Flex, Direct y Maxx.

## LucidFlex 50K

- Tarifa única.
- Sin mensualidad.
- Sin activación.
- Objetivo: 3.000 USD.
- Drawdown EOD: 2.000 USD.
- Consistencia 50 % en evaluación.
- 4 minis / 40 micros.
- Sin daily loss limit.

## Financiada

- Sin consistencia.
- Sin buffer específico de retiro.
- Drawdown EOD.
- Split 90/10.
- Escalado dinámico.

## Retiros

- Días rentables con mínimo de 150 USD en 50K.
- Mínimo 500 USD.
- Hasta 50 % del beneficio y máximo 2.000 USD por solicitud en 50K.
- Máximo cinco retiros antes de pasar a live.
- Pago procesado normalmente en hasta dos días laborables tras aprobación.

## Promoción

- `VAULT`: 50 %, limitado a dos usos.
- El precio final de 50K debe verificarse en checkout.

## Fiabilidad

**Media-alta para su edad.**

Fortalezas:

- reglas claras;
- no activación;
- ruta live;
- productos adecuados para estrategias automatizables si la política lo autoriza.

Debilidad: poco historial longitudinal.

## Veredicto

Prometedora para segunda fase, no como único proveedor inicial.

**Nota: 73/100.**

---

# 10.11. FundedNext Futures

## Perfil

- La empresa matriz es grande en CFD.
- La línea de futuros es reciente.
- En 2026 ha cambiado productos varias veces: Flex, Rapid, Bolt, Rapid Pro y Daily.
- Desde julio de 2026 Rapid y Bolt anteriores dejaron de venderse o resetearse en algunas modalidades.

## Rapid Pro / Daily 50K

- Precio base indicado: 299,98 USD.
- Precio lanzamiento: 149,99 USD.
- Con add-on DLL: 109,99 USD.
- Activación: 0.
- Una fase.
- Posibilidad de aprobar en un día.
- EOD trailing.
- Split 90 %.

## Automatización y copia

Permitido:

- bots propios;
- EAs propios;
- copia entre cuentas propias;
- copia entre distintas firmas si todas pertenecen al mismo titular;
- herramientas como Replikanto o funciones de Tradovate.

Prohibido:

- account rolling;
- grupos de señales;
- copiar a otra persona;
- HFT;
- latencia;
- grids;
- fills irreales;
- order spam;
- hedging correlacionado;
- flipping agresivo.

## Retiros

- Rapid Pro: ciclos de tres días.
- Rapid Daily: recompensas diarias.
- Las reglas cambian según modelo, buffer, DLL y consistencia.

## Fiabilidad

**Media-alta, con riesgo de cambio.**

La marca matriz aporta capacidad operativa, pero el producto futures todavía no tiene el historial de Topstep o Earn2Trade.

## Veredicto

Muy interesante para automatización y múltiples cuentas propias, pero incompatible con el concepto de sacrificar cuentas deliberadamente.

**Nota: 72/100.**

---

# 10.12. Alpha Futures

## Perfil

- Firma reciente.
- Ofrece evaluaciones y programas Direct Qualified.
- Varias políticas de payout.

## 50K

- Evaluaciones alrededor de 119–129 USD según producto.
- Direct Qualified: aproximadamente 519 USD.
- DQ:
  - objetivo de retiro 3.000 USD primero;
  - 2.000 USD posteriormente;
  - drawdown EOD 2.000 USD;
  - daily loss 1.000 USD;
  - consistencia 20 %;
  - máximo de retiro 2.000 USD.

## Fiabilidad

**Media.**

Tiene documentación y actividad de pagos, pero todavía necesita historial.

## Veredicto

Adecuada para pruebas secundarias, especialmente si ofrece un plan que encaje exactamente con la estrategia.

**Nota: 70/100.**

---

# 11. Base compacta de firmas restantes

| Firma | Antigüedad relativa | Split anunciado | Frecuencia anunciada | Automatización | Valoración |
|---|---|---:|---|---|---|
| UProfit | Media/alta | Según plan | Política actualizada 2026 | Verificar plan | B- |
| TickTickTrader | Media | Según modelo | Ciclos y topes | Verificar | B- |
| Elite Trader Funding | Media | Hasta 100 % inicial | 8 días aprox. | EAs en varios planes | B- |
| Leeloo Trading | Media/alta | Variable | Según plan | Verificar | B- |
| Phidias | Media | 80 % | Diaria anunciada | EAs permitidos | C+ |
| FXIFY Futures | Nueva | Hasta 100 % | 14 días | Bots no permitidos según comparador | C+ |
| Blue Guardian Futures | Nueva | 100/90 % | Desde 3 días | Bots/copia restringidos | C+ |
| Top One Futures | Nueva | 90 % | Diaria | Bots no permitidos | C+ |
| FuturesElite | Nueva | 95 % | 5 días | Verificar | C+ |
| The5ers Futures | Producto futures nuevo | 80 % | 14 días | Verificar | C+ |
| For Traders Futures | Nueva | Hasta 100 % | Diaria | Asistentes sí; verificar bot completo | C |
| AquaFutures | Nueva | Hasta 100 % | 7 días | EAs no | C |
| DayTraders | Muy nueva | 100 % | Diaria | EAs anunciados | C |
| Blueberry Futures | Muy nueva | 90 % | 5 días | Verificar | C |
| FundedSeat | Muy nueva | 90 % | Diaria | Verificar | C |
| Hola Prime Futures | Nueva | 90 % | 5 días | Verificar | C |
| Atlas Funded Futures | Nueva | 80 % | 14 días | EAs no / sin overnight | C- |
| Goat Funded Futures | Nueva | Hasta 100 % | 5 días | Bots no | C- |
| E8 Futures | Nueva | Variable | Variable | Verificar | C |
| Funded Futures Family | Nueva | Variable | Variable | Verificar | C |
| Traders Launch | Media | Variable | Variable | Verificar | C |
| The Trading Pit Futures | Marca internacional | Variable | Variable | Verificar producto | C+ |

## Regla de utilización

Las firmas de nivel C no deben recibir múltiples cuentas desde el primer día. El proceso correcto es:

1. una evaluación;
2. una cuenta financiada;
3. un retiro pequeño;
4. segundo retiro;
5. prueba de soporte;
6. entonces considerar escalar.

---

# 12. Trustpilot y reputación pública

Fotografía aproximada consultada en agosto de 2026:

| Firma | Puntuación aproximada | Volumen aproximado | Lectura |
|---|---:|---:|---|
| My Funded Futures | 4,9 | 20.000+ | Muy positiva, pero crecimiento e invitación de reseñas |
| Bulenox | 4,7 | 1.700+ | Buena |
| Earn2Trade | 4,7 | 4.900+ | Buena y con trayectoria |
| TradeDay | 4,6 | 1.300+ | Buena |
| Tradeify | 4,6 | 3.700+ | Buena, empresa joven |
| Apex | 4,2 | 20.000+ | Gran volumen y críticas relevantes |
| Take Profit Trader | 4,3 | 10.000+ | Buena media, porcentaje significativo de negativas |
| Topstep | 3,6 | 14.000+ | Dañada por incidencias técnicas y soporte |

## Cómo leerlo

Una puntuación de 4,9 no demuestra mayor solvencia que una de 3,6.

Puede ocurrir que:

- una empresa solicite opiniones después de cada pago;
- una firma pequeña tenga pocas negativas;
- una empresa antigua acumule años de incidencias;
- una campaña de soporte produzca miles de reseñas;
- los usuarios satisfechos o enfadados estén sobrerrepresentados.

Para elegir proveedor, el volumen de pagos y la claridad de contrato pesan más que una diferencia de décimas.

---

# 13. Comparativa de reglas críticas

## Drawdown

De mejor a peor para una estrategia normal:

1. estático;
2. EOD trailing que se bloquea;
3. EOD trailing permanente;
4. intradía sobre balance realizado;
5. intradía sobre equity no realizada.

Una estrategia de StrategyQuant debe simular exactamente el mecanismo. No basta con filtrar por drawdown máximo.

## Consistencia

- Sin consistencia: más fácil aprobar, pero puede haber revisión de conducta.
- 50 %: permite aprobar en dos días.
- 40 %: obliga a tres o más sesiones en la práctica.
- 30 %: requiere beneficios distribuidos.
- 20 %: exige mucha uniformidad.

## Buffer

Un buffer no es una pérdida, pero retrasa el primer euro retirable.

Ejemplo:

```text
Cuenta 50K
Drawdown: 2.000
Safety net: 2.100
Mínimo de retiro: 500

Saldo mínimo aproximado para solicitar:
52.600
```

## Payout caps

Es necesario distinguir:

- porcentaje de beneficio que puede solicitarse;
- máximo en dólares;
- número máximo de retiros;
- cierre o paso a live después de cierto número;
- reducción del saldo y efecto sobre drawdown.

Una empresa que anuncia “100 % split” puede permitir retirar menos dinero que otra con 80 % si tiene caps más estrictos.

---

# 14. Fiabilidad de cobro: señales positivas y negativas

## Señales positivas

- varios años operando;
- documentación con historial de cambios;
- ruta a cuenta live;
- payout policy con ejemplos;
- pagos mediante proveedores externos trazables;
- soporte que responde a negativas;
- reglas objetivas;
- ausencia de cambios retroactivos;
- cuentas legacy respetadas;
- estados y métricas públicas.

## Señales negativas

- promociones permanentes del 90 % sin explicación económica;
- activación oculta;
- payout policy difícil de encontrar;
- términos que permiten cerrar “a discreción” sin criterios;
- cambio frecuente de productos;
- retirada condicionada por reglas no visibles en compra;
- soporte solo por Discord;
- opiniones idénticas;
- influencers que solo muestran enlaces afiliados;
- prohibiciones ambiguas sobre “comportamiento no profesional”;
- retrasos masivos simultáneos;
- empresa demasiado nueva para tener historial.

## Procedimiento antes de comprar

1. Guardar PDF o captura de:
   - precio;
   - activación;
   - reglas;
   - payout;
   - automatización;
   - copia;
   - términos.
2. Registrar fecha y plan.
3. Preguntar a soporte por escrito si la estrategia automática está permitida.
4. Describir:
   - frecuencia;
   - duración media;
   - órdenes;
   - plataforma;
   - copiador;
   - servidor.
5. Conservar la respuesta.
6. Realizar un primer retiro pequeño.
7. No acumular una gran cantidad en sim antes de probar el pago.

---

# 15. Recomendaciones por objetivo

## Máxima seguridad relativa

1. Topstep.
2. Earn2Trade.
3. TradeDay.
4. OneUp Trader.
5. My Funded Futures.

## Mejor para automatización propia

1. My Funded Futures.
2. Topstep, con ejecución local.
3. FundedNext Futures.
4. Tradeify.
5. TradeDay.

## Mejor precio total 50K observado

1. MFFU Rapid con descuento, aproximadamente 39,50 USD.
2. Tradeify Growth con descuento, aproximadamente 58,20 USD.
3. TradeDay Intraday, 59 USD.
4. Tradeify Select con descuento, aproximadamente 64,20 USD.
5. Topstep sin activación, 95 USD si se aprueba en el primer mes.
6. Take Profit Trader con `NOFEE40`, 102 USD, solo manual.
7. FundedNext Rapid Pro con DLL, 109,99 USD.

## Mejor para múltiples cuentas manuales

1. Apex.
2. Topstep.
3. Take Profit Trader.
4. FundedNext, solo cuentas propias y sin account rolling.
5. Tradeify.

## Mejor ruta real a live

1. Topstep.
2. Earn2Trade.
3. TradeDay.
4. OneUp Trader.
5. MFFU.
6. Take Profit Trader PRO+.
7. Lucid.

---

# 16. Recomendación concreta para Ultra Rentable

## MVP automático

La primera cuenta debería elegirse entre:

### Opción A — MFFU Rapid 50K

La opción más directa por:

- precio;
- activación cero;
- bot propio permitido;
- retiro frecuente;
- EOD en evaluación;
- ruta live.

### Opción B — Tradeify Select/Growth 50K

Interesante por:

- precio bajo;
- activación cero;
- bots personales;
- varias modalidades de retirada;
- integración con plataformas conocidas.

### Opción C — Topstep 50K

La mejor por prestigio, pero exige resolver:

- ejecución desde dispositivo personal;
- prohibición de VPS;
- API no disponible en Live Funded;
- account stacking prohibido.

### Opción D — FundedNext Rapid Pro 50K

Adecuada si se quiere:

- bot;
- copia entre cuentas propias;
- pago frecuente;
- cuenta de una sola fase.

Pero debe excluirse totalmente la lógica de sacrificar cuentas.

## Proveedores que no deben usarse en el MVP automático

- Apex.
- Take Profit Trader.
- Cualquier firma que no confirme por escrito el uso de bots.

## Estrategia de diversificación futura

Después de dos retiros reales en el primer proveedor:

1. añadir un segundo proveedor de nivel A/B+;
2. usar la misma estrategia con parámetros de riesgo adaptados;
3. comprobar diferencias de fills;
4. separar credenciales;
5. limitar exposición global;
6. incorporar un tercer proveedor solo después de validar el sistema.

---

# 17. Diseño de la base de datos para Hermes

Cada proveedor deberá guardarse como un registro versionado.

```yaml
provider_id: mffu
name: My Funded Futures
last_verified: 2026-08-02
confidence: high

company:
  founded: 2023
  jurisdiction: null
  years_active: 3
  live_path: true

automation:
  own_bot: allowed
  hft: prohibited
  vps: verify
  api: platform_dependent
  copy_own_accounts: allowed_with_conditions
  copy_other_people: prohibited

plans:
  - plan_id: rapid_50k
    phase: evaluation
    price_regular: 79
    billing: monthly
    promotion:
      code: 300K
      discount_percent: 50
      verified_date: 2026-08-02
    activation_fee: 0
    profit_target: 3000
    drawdown:
      amount: 2000
      type: eod_trailing
    daily_loss_limit: null
    consistency_eval: 50
    minimum_days: 2
    max_minis: 5
    max_micros: 50

funded:
  split: 90
  payout_frequency: daily
  buffer_50k: 2100
  consistency: null
  live_transition: true

reliability:
  score: 82
  grade: A-
  payout_confidence: high
  notes: []

sources:
  official_rules: []
  official_payouts: []
  terms: []
  promotions: []
```

## Campos obligatorios

- fecha de última verificación;
- URL oficial;
- plan;
- versión;
- precio;
- promoción;
- activación;
- reset;
- drawdown;
- consistencia;
- payout;
- automatización;
- copia;
- noticias;
- overnight;
- máximo de cuentas;
- ruta live;
- incidencias;
- puntuación;
- nivel de confianza.

---

# 18. Sistema automático de actualización

Hermes debe revisar las fuentes:

## Diariamente

- promociones;
- estado de páginas;
- códigos;
- precio de checkout.

## Semanalmente

- payout policy;
- reglas;
- automatización;
- plataformas;
- cuentas máximas.

## Mensualmente

- Trustpilot;
- nuevos proveedores;
- proveedores cerrados;
- cambios de términos;
- evidencia de pagos.

## Antes de cada compra

- verificación manual del checkout;
- activación;
- reglas del plan;
- autorización de automatización;
- restricciones de país.

## Alertas

Hermes debe notificar si:

- cambia el drawdown;
- aparece activación;
- se elimina API;
- se prohíben bots;
- se reduce el payout;
- aumenta el buffer;
- cambia el número máximo de cuentas;
- hay una ola de reclamaciones;
- la web deja de responder;
- el soporte confirma reglas distintas a la documentación.

---

# 19. Fuentes principales

## Directorios y comparadores

- The Prop Firm Guide — directorio de firmas de futuros:  
  https://thepropfirmguide.com/futures-all-firms/

- The Prop Firm Guide — promociones:  
  https://thepropfirmguide.com/futures-deals/

- The Prop Firm Guide — comparación de reglas:  
  https://thepropfirmguide.com/prop-firm-rules-comparison/

- The Prop Firm Guide — payout tracker:  
  https://thepropfirmguide.com/prop-firm-payout-tracker/

- Prop Firm Match — futuros:  
  https://propfirmmatch.com/futures

Estas páginas contienen enlaces de afiliado. Se utilizan como índice, no como fuente única.

## Topstep

- Programa: https://www.topstep.com/our-program
- Parámetros: https://help.topstep.com/en/articles/8284197-trading-combine-parameters
- API: https://help.topstep.com/en/articles/11187768-topstepx-api-access
- Estrategias prohibidas: https://help.topstep.com/en/articles/10305426-prohibited-trading-strategies-at-topstep
- Live: https://help.topstep.com/en/articles/10657969-live-funded-account-parameters

## Apex

- Página principal: https://apextraderfunding.com/
- Reglas EOD: https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-evaluations/
- Retiros EOD: https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-payouts/
- Activación: https://apextraderfunding.com/help-center/billing/pa-activation-process-deadline-explained/
- Cupón: https://apextraderfunding.com/coupon-code/
- Actividades prohibidas: https://apextraderfunding.com/help-center/getting-started/prohibited-activities/
- Número de cuentas: https://apextraderfunding.com/help-center/performance-accounts-pa/how-many-paid-funded-accounts-am-i-allowed-to-have/

## My Funded Futures

- Rapid: https://myfundedfutures.com/plans/rapid
- Reglas de prácticas: https://help.myfundedfutures.com/en/articles/8444599-fair-play-and-prohibited-trading-practices
- Payout policy: https://help.myfundedfutures.com/en/articles/13745661-payout-policy-overview-best-and-fastest-prop-firm-payouts

## TradeDay

- Página principal y precios: https://www.tradeday.com/
- Cómo funciona: https://www.tradeday.com/how-it-works
- Automatización: https://tradeday.freshdesk.com/en/support/solutions/articles/103000085101-automated-algo-and-bot-trading

## Earn2Trade

- Gauntlet Mini: https://www.earn2trade.com/gauntlet-mini
- Página principal: https://www.earn2trade.com/
- Copiadores: https://help.earn2trade.com/en/articles/12034590-am-i-allowed-to-copy-trades-across-multiple-accounts

## Take Profit Trader

- Página principal y precios: https://takeprofittrader.com/
- Políticas: https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/34431153546397-TakeProfitTrader-Universal-Trading-Policies-UTP
- Copiador: https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/34431176505245-Trade-Copier-Policy

## OneUp Trader

- Billing: https://help.oneuptrader.com/article/371-how-does-the-billing-work
- Proceso: https://help.oneuptrader.com/article/520-getting-funded-process

## FundedNext Futures

- Automatización: https://helpfutures.fundednext.com/en/articles/14298560-is-the-usage-of-automated-trading-systems-eas-and-bots-allowed-in-fundednext-futures
- Prácticas prohibidas: https://helpfutures.fundednext.com/en/articles/14298337-what-are-the-prohibited-trading-strategies-of-fundednext-futures
- Precios: https://helpfutures.fundednext.com/en/articles/15053874-what-are-the-available-account-sizes-and-their-prices-in-fundednext-futures

## Tradeify

- Pricing: https://help.tradeify.co/en/articles/14369021-tradeify-pricing-reference
- Growth: https://help.tradeify.co/en/articles/10495915-growth-evaluation-accounts
- Financiada: https://help.tradeify.co/en/articles/10495917-how-do-i-get-funded-after-passing-an-evaluation

## Lucid

- LucidFlex evaluación: https://support.lucidtrading.com/en/articles/12945790-lucidflex-evaluation-account
- Financiada: https://support.lucidtrading.com/en/articles/12945795-lucidflex-funded-account
- Retiros: https://support.lucidtrading.com/en/articles/12945796-lucidflex-payouts

## Bulenox

- Acuerdo Master 2026: https://form.jotform.com/230508683548160/prefill/651480816239650b578f13093d20
- Qualification: https://bulenox.com/help/qualification-account/

## Información independiente del sector

- Business Insider, industria y tasas de éxito:  
  https://www.businessinsider.com/what-is-prop-trading-pass-challenge-gen-z-millennial-traders-2025-12

- Business Insider, verificación de pago Apex:  
  https://www.businessinsider.com/day-trading-strategy-tips-prop-firm-payouts-kane-simmons-2026-5

---

# 20. Conclusión final

La selección correcta para Ultra Rentable no debe comenzar comprando diez cuentas baratas.

Debe comenzar así:

1. elegir una firma que permita bots por escrito;
2. seleccionar un plan 50K sin activación o con coste total claro;
3. simular exactamente sus reglas;
4. operar una cuenta;
5. realizar un primer retiro;
6. realizar un segundo retiro;
7. verificar que no existe conflicto entre StrategyQuant, el copiador y los términos;
8. añadir un segundo proveedor;
9. escalar únicamente después.

La recomendación provisional es:

> **MFFU o Tradeify para el primer MVP automático; Topstep para máxima reputación si se resuelve la limitación de ejecución local; FundedNext como segunda capa; TradeDay como proveedor sólido con integración más controlada.**

Apex y Take Profit Trader pueden ser muy útiles para trading manual y copia de cuentas propias, pero no deben formar parte del motor automático de StrategyQuant mientras mantengan la prohibición actual de bots.

Esta base debe considerarse viva. Cada precio, promoción y regla debe verificarse de nuevo en el checkout y en el contrato antes de comprar.

---

**Fin del informe**
