# Auditoría Técnica del Data Manager de StrategyQuant X

**Fecha de ejecución:** 9 de Agosto de 2026  
**Sistema:** StrategyQuant X v144.2953 (Linux VPS, service `strategyquantx`)  
**Proyecto de referencia:** `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`  

---

## 1. Resumen Ejecutivo y Hallazgo Clave (Respuesta a la Pregunta Central)

> **HALLAZGO CLAVE:**  
> El rango **2026.02.26 → 2026.08.04** especificado en la configuración del proyecto (`project.cfx` / `Build-Task1.xml`) es un **LÍMITE DE DATOS DISPONIBLES EN DISCO**, **NO** un límite arbitrario de configuración.  
> 
> La inspección directa de la base de datos de metadatos (`data.db`) y la decodificación del binario de precios (`BTCUSDT_AUTO_H1.dat`) demuestran que **únicamente existen descargadas 3,840 barras H1** que abarcan exactamente del **26/02/2026 00:00:00 UTC al 04/08/2026 23:00:00 UTC**.  
> **No existe ni un solo día de datos históricos anterior al 26 de febrero de 2026 en StrategyQuant X.** El proyecto utiliza actualmente el 100% del historial descargado en la instalación.

---

## 2. Inventario Real de Símbolos y Rutas de Datos (BTCUSDT)

De acuerdo con el rastreo del sistema de archivos `/home/ubuntu/StrategyQuantX/user/data/` y la base de datos SQLite `data.db`:

| Parámetro | Valor Real en Sistema |
| :--- | :--- |
| **Símbolo Interno (SQX)** | `BTCUSDT_AUTO` |
| **Código Instrumento** | `BTCUSDT` |
| **Timeframe Descargado** | `H1` (1 Hora) |
| **Ruta Exacta del Binario** | `/home/ubuntu/StrategyQuantX/user/data/History/BTCUSDT_AUTO/BTCUSDT_AUTO_H1.dat` |
| **Tamaño Fichero Binario** | `153,479 bytes` (~153.5 KB) |
| **Base de Datos de Metadatos** | `/home/ubuntu/StrategyQuantX/user/data/data.db` (Tabla `DATA`, ID `12`) |
| **Proveedor Asignado** | `Binance USDT-M` |
| **Zona Horaria de Serie** | `Etc/UCT` (UTC) |

---

## 3. Rango Real de Fechas y Conteo de Barras en Disco

A partir del análisis de metadatos en la tabla `DATA` de `data.db` e inspección de estructura binaria (decodificación de timestamp 8-byte big-endian y delta-encoding OHLC):

- **Primera Barra Registrada:** `2026-02-26 00:00:00 UTC` (timestamp MS: `1772064000000`)
- **Última Barra Registrada:** `2026-08-04 23:00:00 UTC` (timestamp MS: `1785884400000`)
- **Total de Barras en Fichero:** `3,840` barras
- **Continuidad:** 160 días completos a 24 barras/día = 3,840 barras exactas (sin lagunas temporales).

### Registro Evidencial de `data.db` (Tabla `DATA`, Fila ID 12):
```text
(12, 0, 'History', 'BTCUSDT_AUTO', 'BTCUSDT', 'H1', 'Etc/UCT', None, 
 1772064000000, 1785884400000, 1, 3840, 1, 7, 230400, 'BTCUSDT', 'Binance USDT-M', 0, 1, -1, -1)
```

---

## 4. Auditoría de Serie Minutaria (M1)

- **Existe serie M1 descargada para BTCUSDT:** **NO**.
- **Ruta buscada:** `/home/ubuntu/StrategyQuantX/user/data/History/BTCUSDT_AUTO/`
- **Contenido del directorio:** Únicamente existe `BTCUSDT_AUTO_H1.dat`. No existe ninguna carpeta ni archivo para `M1`, `M5`, `M15`, ni datos de Ticks para BTCUSDT.

---

## 5. Proveedores y Conexiones Configurados

1. **Proveedor Binance USDT-M:**
   - Asignado a `BTCUSDT_AUTO` en la base de datos de datos de SQX.
   - El plugin `CryptoExchangeBinanceUsdtM.jar` y `DataSourceCrypto.jar` se encuentran cargados en el motor SQX.
2. **Brokers/Conexiones Genéricos en DB (`BROKER` table):**
   - Existen 11 plantillas predeterminadas en SQX (`XTB`, `Darwinex Zero`, `RoboForex`, `Dukascopy`, `Darwinex`, `ICMarkets`, `Pepperstone`, `OANDA`, `FTMO`, `The5ers`, `Monevis`), utilizadas principalmente para presets de spreads y comisiones.
3. **Estado de Operatividad del Servicio:**
   - El servicio `strategyquantx.service` se encuentra **OPERATIVO y corriendo 24/7** en el VPS.
   - Interfaz Web UI en `http://127.0.0.1:5050/` y servidor MCP en `http://127.0.0.1:8080/mcp`.

---

## 6. Comparativa `project.cfx` vs. Datos Reales en Disco

| Entidad | `dateFrom` | `dateTo` | Coincidencia |
| :--- | :--- | :--- | :--- |
| **Configuración (`Build-Task1.xml`)** | `2026.02.26` | `2026.8.4` | **100% Exacta** |
| **Binario Real (`BTCUSDT_AUTO_H1.dat`)** | `2026-02-26 00:00:00` | `2026-08-04 23:00:00` | **100% Exacta** |

**Conclusión:** La configuración del proyecto no está recortando artificialmente el dataset. SQX está evaluando sobre **todo el historial disponible**.

---

## 7. Estimación de Descarga de Histórico Adicional (BTCUSDT)

Si se requiere ampliar el rango temporal para optimizaciones de largo plazo:

### Escenario A: BTCUSDT H1 desde el Inicio de Binance (2017.08 → 2026.08, ~9 años)
- **Volumen de Barras H1:** ~78,840 barras
- **Tamaño de Almacenamiento Estimado:** ~3.15 MB
- **Solicitudes API REST Binance (klines, limit 1000):** ~79 llamadas
- **Tiempo de Descarga e Importación Estimado:** **~5 a 15 segundos**

### Escenario B: BTCUSDT M1 para un Subrango Reciente (2 Años: 2024.08 → 2026.08)
- **Volumen de Barras M1:** ~1,051,200 barras
- **Tamaño de Almacenamiento Estimado:** ~37.8 MB
- **Solicitudes API REST Binance (klines, limit 1000):** ~1,052 llamadas
- **Tiempo de Descarga e Importación Estimado:** **~1 a 2 minutos** (respetando límites de rate limit de Binance REST API).

---

## 8. Verificación de Rutas y Ficheros

- **Informe guardado en:**  
  `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/docs/Estado/auditoria/08_auditoria_datos_sqx.md`
- **Fichero de datos auditado:**  
  `/home/ubuntu/StrategyQuantX/user/data/History/BTCUSDT_AUTO/BTCUSDT_AUTO_H1.dat`
- **Base de datos auditada:**  
  `/home/ubuntu/StrategyQuantX/user/data/data.db`
