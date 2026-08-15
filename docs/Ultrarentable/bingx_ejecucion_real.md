# Ejecución real en BingX — Informe de implementación
## Proyecto Ultrarentable · BingX USDⓈ-M Perpetual Futures

> **Objetivo del documento:** describir, con fuentes oficiales, cómo conectar una cuenta real de BingX, qué endpoints deben usarse para ejecución y seguimiento, cómo funciona el entorno simulado VST, cuáles son los límites de API relevantes para un bot, cómo debe firmar el cliente, y qué falta implementar a partir del código existente en el proyecto.
>
> **Fuentes oficiales usadas:** `https://bingx-api.github.io/docs-v3/`, `https://bingx-api.github.io/docs/`, `https://bingx.com/en/support/articles/31103871611289`, `https://bingx.com/en/learn/article/how-to-use-demo-trading-on-bingx`, `https://github.com/BingX-API/api-ai-skills/blob/main/skills/references/authentication.md`, `https://github.com/BingX-API/api-ai-skills/blob/main/skills/references/base-urls.md`, `https://github.com/BingX-API/api-ai-skills/blob/main/skills/references/rate-limits.md`, `https://github.com/BingX-API/api-ai-skills/blob/main/skills/references/error-codes.md`.

---

## 1. Estado actual del cliente en el proyecto
Ruta: `services/api/app/bingx/client.py`

El proyecto ya tiene un cliente parcial de REST:
- Autenticación HMAC-SHA256 sobre query string.
- Claves desde variables de entorno: `BINGX_API_KEY`, `BINGX_SECRET_KEY`.
- Bases URL configurables, con fallback `.pro` si falla la `.com`.
- `recvWindow` y manejo básico de errores.

Endpoints públicos ya implementados:
- `/openApi/swap/v2/quote/contracts`
- `/openApi/swap/v3/quote/klines`
- `/openApi/swap/v2/quote/premiumIndex`

Endpoints privados ya implementados:
- `/openApi/swap/v2/user/commissionRate`
- `/openApi/swap/v3/user/balance`

**Limitación importante:** el cliente actual solo implementa `GET` públicos y autenticados. No implementa `POST`/`PUT`/`DELETE` para ejecución real de órdenes, gestión de posiciones, apalancamiento, cancelaciones, batch orders, close position, VST, etc.

---

## 2. Conexión de cuenta real y API key

### 2.1 Creación de API key
Se crea desde la web de BingX: **User Center → API Management**.
- Se obtiene `API Key` + `Secret Key`.
- Por defecto la key es **solo lectura**; hay que habilitar explícitamente **Perpetual Futures Trading**.
- Se recomienda habilitar IP whitelist.

Fuente oficial: `https://github.com/BingX-API/api-ai-skills/blob/main/skills/references/authentication.md`.

### 2.2 Permisos recomendados para objetivo A (USDⓈ-M)
- Lectura.
- Perpetual Futures Trading.
- No habilitar Withdraw.
- Usar subcuenta si se quiere aislar riesgo del main account.

Fuente relacionada: `https://help.lubilabs.com/en/exchanges/bingx`.

### 2.3 KYC / verificación
- Varias operaciones avanzadas requieren **Advanced Identity Verification (KYC)**.
- Errores oficiales indican restricción por región o KYC insuficiente: `101483`, `101484` en docs oficiales.
- Para ejecución real en perpetuals, se asume cuenta verificada; si aparecen estos códigos, completar KYC en BingX.

Fuente: `https://github.com/BingX-API/api-ai-skills/blob/main/skills/references/error-codes.md`.

### 2.4 Variables de entorno sugeridas
```text
BINGX_API_KEY=
BINGX_SECRET_KEY=
BINGX_BASE_URL=https://open-api.bingx.com
BINGX_FALLBACK_URL=https://open-api.bingx.pro
BINGX_RECV_WINDOW=5000
BINGX_TIMEOUT=10
BINGX_ENVIRONMENT=prod-live
```

Para VST:
```text
BINGX_ENVIRONMENT=prod-vst
BINGX_BASE_URL=https://open-api-vst.bingx.com
BINGX_FALLBACK_URL=https://open-api-vst.bingx.pro
```

Fuente: `https://github.com/BingX-API/api-ai-skills/blob/main/skills/references/base-urls.md`.

---

## 3. Autenticación HMAC SHA-256 oficial

Reglas exactas desde la fuente oficial (`authentication.md`):
- Cabeceras obligatorias en **todas** las peticiones:
  - `X-BX-APIKEY: <API_KEY>`
  - `X-SOURCE-KEY: BX-AI-SKILL`
- Para endpoints autenticados, parámetros obligatorios:
  - `timestamp` en milisegundos.
  - `recvWindow` opcional, máximo `5000`.
  - `signature` calculada por HMAC-SHA256.
- Proceso de firma:
  1. Recoger todos los parámetros de negocio **y** `timestamp`/`recvWindow`.
  2. Ordenar claves ASCII ascendente.
  3. Concatenar como `key=value&key=value`.
  4. `signature = HMAC_SHA256(secretKey, parameterString)` en hex minúsculas.
  5. Añadir `&signature=<hex>` a la query o incluir dentro del JSON body si el endpoint acepta JSON.
- No URL-encodear antes de firmar; solo codificar valores en la URL final si contienen `[` o `{`.

El cliente actual del proyecto cumple la firma para query strings, pero **no soporta body JSON firmado**; algunos endpoints modernos aceptan `application/json`.

Fuente: `https://github.com/BingX-API/api-ai-skills/blob/main/skills/references/authentication.md`.

---

## 4. Entornos: producción real y VST/simulado

### 4.1 Producción real
- `prod-live`: `https://open-api.bingx.com` (primario), fallback `https://open-api.bingx.pro`.

### 4.2 VST/simulado
- `prod-vst`: `https://open-api-vst.bingx.com` (primario), fallback `https://open-api-vst.bingx.pro`.
- VST = Virtual USDT. No tiene valor real, no es retirable.
- El entorno VST replica comportamiento en tiempo real con mercados live.
- Cada usuario nuevo recibe `100000 VST`; si baja de `20000 VST` puede solicitar más.
- Máximo aprox. `150` órdenes abiertas en demo según soporte oficial.
- Existe endpoint para ajustar fondos VST desde API: `POST /openApi/swap/v2/trade/getVst` con `adjustType` `0` aumentar / `1` disminuir.

Fuentes:
- `https://github.com/BingX-API/api-ai-skills/blob/main/skills/references/base-urls.md`
- `https://bingx.com/en/learn/article/how-to-use-demo-trading-on-bingx`
- `https://bingxservice.zendesk.com/hc/en-001/articles/13277514625039-BingX-Tutorial-How-to-Start-Demo-Trading-Using-Virtual-USDT`

### 4.3 Recomendación para Ultrarentable
- Desarrollar primero en `prod-vst`.
- Incluir guardas tipo `BINGX_TESTNET=true` y bloqueo explícito contra `prod-live` en entornos de prueba.
- Hacer migración a `prod-live` solo tras validación completa en VST.

---

## 5. Endpoints REST clave para ejecución real

A continuación se listan los endpoints oficiales más relevantes para un bot de USDⓈ-M Perpetual Futures. La documentación oficial está en `docs-v3` y en el repo `api-ai-skills`.

### 5.1 Ejecución
- `POST /openApi/swap/v2/trade/order`
  - Place Order.
  - Rate limit: `10/s` UID / `3/s` IP.
- `POST /openApi/swap/v2/trade/order/test`
  - Validar parámetros/firma sin ejecutar.
  - Rate limit: `5/s` UID / `2/s` IP.
- `POST /openApi/swap/v2/trade/batchOrders`
  - Batch place/cancel en un solo request.
- `POST /openApi/swap/v2/trade/closeAllPositions`
  - Cerrar todas las posiciones.
- `POST /openApi/swap/v2/trade/allOpenOrders`
  - Cancel all open orders.
- `POST /openApi/swap/v1/trade/cancelReplace`
  - Cancel existing + send new in one request.
- `POST /openApi/swap/v1/trade/batchCancelReplace`
  - Batch cancel + place.

### 5.2 Consulta de órdenes
- `GET /openApi/swap/v2/trade/order`
- `GET /openApi/swap/v2/trade/openOrders`
- `GET /openApi/swap/v2/trade/allOrders`
- `GET /openApi/swap/v2/trade/allFillOrders`

### 5.3 Posiciones y apalancamiento
- `GET /openApi/swap/v2/user/positions`
- `GET /openApi/swap/v2/trade/leverage`
- `POST /openApi/swap/v2/trade/leverage`
- `POST /openApi/swap/v2/trade/marginType`
- `POST /openApi/swap/v1/positionSide/dual`
- `POST /openApi/swap/v2/trade/positionMargin`
- `GET /openApi/swap/v2/trade/positionMargin`
- `POST /openApi/swap/v2/trade/closePosition` por position ID.

### 5.4 Cuenta
- `GET /openApi/swap/v2/user/balance`
- `GET /openApi/swap/v2/user/positions`
- `GET /openApi/swap/v2/user/income`
- `POST /openApi/swap/v2/trade/getVst`

Fuente oficial API reference swap trade: `https://github.com/BingX-API/api-ai-skills/blob/main/skills/swap-trade/api-reference.md`.

---

## 6. Límites de API y comportamiento recomendado

### 6.1 Dimensiones oficiales
BingX aplica límites por **per-UID** y **per-IP** de forma independiente. Superar cualquiera devuelve `100410`.

| Dimensión | Ámbito |
| --- | --- |
| Per-UID | Por API key / cuenta autenticada |
| Per-IP | Por IP de origen, incluso en endpoints públicos |

Fuente: `https://github.com/BingX-API/api-ai-skills/blob/main/skills/references/rate-limits.md`.

### 6.2 Límites relevantes para USDⓈ-M trading
- `POST /openApi/swap/v2/trade/order`: `10/s` UID / `3/s` IP.
- `POST /openApi/swap/v2/trade/order/test`: `5/s` UID / `2/s` IP.
- `POST /openApi/swap/v2/trade/batchOrders`: `5/s` UID / `1/s` IP.
- `POST /openApi/swap/v2/trade/closeAllPositions`: `5/s` UID / `5/s` IP.
- `GET /openApi/swap/v2/user/positions`: `5/s` UID / `5/s` IP.
- `GET /openApi/swap/v2/user/balance`: `5/s` UID / `5/s` IP.
- Market data pública compartida: `500 requests / 10s` por IP.

Fuente: `https://bingx.com/en/support/articles/31103871611289` y repo oficial `rate-limits.md`.

### 6.3 Recomendación para bot
- Implementar token-bucket por endpoint.
- Backoff exponencial con jitter para `100410`.
- Circuit breaker si ratio de `100410` supera 20% en ventana de 30s.
- Limitar lógica de “reintento automático” a errores transitorios; `100421` no debe reintentarse con backoff solo.
- No compartir IP con scraping market-data si se hace en otro proceso.

Fuente: `https://github.com/BingX-API/api-ai-skills/blob/main/skills/references/rate-limits.md`.

---

## 7. WebSocket privado para seguimiento

BingX ofrece WebSocket Account Data en swap:
- Order update push.
- Account balance and position update push.
- Configuration updates such as leverage and margin mode.

### 7.1 Listen key
- Endpoint REST para generar listen key: `/openApi/user/auth/userDataStream` `POST`.
- Renovar: `PUT`.
- Cerrar: `DELETE`.
- Validez por defecto `60 minutos`.
- Renovar como máximo cada `30 minutos`.
- Límite listen key endpoints: `2/s` por UID y `2/s` por IP.

Fuente: `https://github.com/BingX-API/api-ai-skills/blob/main/skills/references/rate-limits.md`.

### 7.2 Uso en bot
El bot debería:
1. Generar listen key.
2. Abrir conexión WS privada.
3. Suscribirse a:
   - ordenes
   - balance/posiciones
4. Traducir eventos a:
   - fills
   - cambios de posición
   - actualizaciones de margen/apalancamiento
5. Actualizar estado local y escribir auditoría.

El cliente actual no tiene módulo WS ni generación/renovación de listen key.

---

## 8. Cómo debe ejecutar y hacer seguimiento un bot

### 8.1 Flujo mínimo real
1. `GET /openApi/swap/v2/user/balance` y `/positions` para estado inicial.
2. `POST /openApi/swap/v2/trade/leverage` si hace falta apalancamiento por símbolo.
3. `POST /openApi/swap/v2/trade/order` o `/order/test` primero.
4. `GET /openApi/swap/v2/trade/order` para confirmar estado.
5. Escuchar WS privado para fills y cambios de posición.
6. `POST /openApi/swap/v2/trade/closeAllPositions` o `closePosition` para salida.
7. `GET /openApi/swap/v2/user/income` para PnL realizado.

### 8.2 Riesgo y límites operativos
- El bot debe respetar tamaño mínimo de orden (`101202`) y margen disponible (`101204`, `101206`).
- Evitar `101419` por límite de órdenes pendientes.
- No operar si la posición excede límite del símbolo (`101429`, `112414`).
- Gestionar `101214` si hay settlement de funding en curso.
- En modo one-way, `positionSide` suele ser `BOTH`; en hedge mode, `LONG`/`SHORT`.
- Para cerrar posiciones aisladas puede requerirse `positionId`.

Fuente: `https://github.com/BingX-API/api-ai-skills/blob/main/skills/references/error-codes.md`.

---

## 9. Qué falta implementar en el proyecto

Comparando el cliente actual con ejecución real, faltan:

### 9.1 Cliente REST firmado completo
- Métodos `signed_post`, `signed_put`, `signed_delete`.
- Soporte de body JSON autenticado cuando corresponda.
- Wrappers específicos por dominio: trade, position, leverage, margin, order query, VST.

### 9.2 Ejecución real de órdenes
- `POST /openApi/swap/v2/trade/order`
- `POST /openApi/swap/v2/trade/order/test`
- Batch orders, cancelación, close position.
- Manejo explícito de `orderID` como string.

### 9.3 Gestión de cuenta/riesgo
- Consulta de posiciones.
- Ajuste de leverage.
- Cambio de margin mode / position mode.
- Aplicación de VST desde API.
- Límites por símbolo, tamaño mínimo, leverage máximo.

### 9.4 WebSocket privado
- Generación/renovación/cierre de listen key.
- Cliente WS con reconexión.
- Parseo de eventos de orden, balance/posición y configuración.

### 9.5 Entornos y guards
- Soporte explícito `prod-live` / `prod-vst`.
- Bloqueo accidental contra `prod-live` en pruebas.
- Timeout y fallback `.com` -> `.pro` solo en fallos de red.

### 9.6 Observabilidad
- Logging estructurado por request id / order id.
- Métricas de rate limit y errores `100410`.
- Persistencia local de fills/órdenes para auditoría.

---

## 10. Checklist de puesta en producción real

1. **Cuenta**
   - [ ] BingX registrada y KYC completada si hace falta.
   - [ ] API key creada con permisos mínimos.
   - [ ] IP whitelist configurada con la IP del bot.

2. **Configuración**
   - [ ] Variables de entorno cargadas.
   - [ ] `BINGX_ENVIRONMENT=prod-live`.
   - [ ] `recvWindow` elegido y sincronización de reloj comprobada.

3. **Cliente**
   - [ ] Cliente REST extendido con métodos POST/PUT/DELETE firmados.
   - [ ] Base URLs con fallback correcto y detección de error de red.
   - [ ] Manejo de `orderID` como string.

4. **Prueba**
   - [ ] Probar `/order/test` contra `prod-vst`.
   - [ ] Ejecutar pequeña batería real en VST y validar fills/posiciones/PNL.
   - [ ] Probar gestión de leverage y margin mode en VST.

5. **Seguimiento**
   - [ ] Listen key generada y renovada.
   - [ ] WS privado recepcionando eventos.
   - [ ] Estado local sincronizado contra REST como respaldo.

6. **Riesgo**
   - [ ] Límite por orden y por día definidos.
   - [ ] Circuit breaker y kill switch.
   - [ ] Monitoreo de `100410`, `101204`, `101206`, `101419`.

---

## 11. Resumen ejecutivo

- El proyecto ya tiene la base de autenticación HMAC-SHA256 y consultas públicas/privadas mínimas.
- Para ejecución real en USDⓈ-M hace falta ampliar el cliente a endpoints de trade, leverage, margin, order management y VST.
- El entorno oficial de prueba sin dinero real es `prod-vst` (`open-api-vst.bingx.com`), con VST.
- Los límites oficiales actuales para place-order son `10/s` por UID y `3/s` por IP desde octubre 2025.
- El seguimiento en tiempo real requiere listen key + WebSocket privado; actualmente no está implementado.
- La conexión real requiere API key con trading permitido, IP whitelist y, en ciertos casos, KYC avanzado.
