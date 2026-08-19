# DIRECTIVA MAESTRA UNIVERSAL PARA AGENTES DE IA

> **REGLA DE DESCUBRIMIENTO AUTOMÁTICO:** Cualquier agente de IA que inicie sesión en este workspace debe acatar esta directiva de forma obligatoria, transparente y continua sin necesidad de recordatorios previos.

---

## 1. GUARDARRAÍLES SUPREMOS E INQUEBRANTABLES

### 1.1 DOCTRINA ZERO-MOCKS & REAL-ONLY (CERO SIMULACIONES FALSAS)
- **PROHIBICIÓN TOTAL DE INVENTAR**: Queda terminantemente prohibido inventar datos, registros, velas, trades, métricas de rendimiento, curvas de equidad, balances, Profit Factor, Sharpe/Sortino o logs de eventos.
- **PROHIBICIÓN DE GENERADORES SINTÉTICOS**: Prohibido el uso de funciones aleatorias o generadoras sintéticas (`random`, `randint`, `uniform`, `seed`) en motores de cálculo, validación, APIs o bases de datos operacionales.
- **CERO FALLBACKS COMPLACIENTES**: Nunca insertar mocks, placeholders o resultados falsos para que una interfaz o reporte "se vea lleno o bonito".
- **GESTIÓN DETERMINISTA DE ESTADOS**:
  - Falta de información o evidencia $\longrightarrow$ `BLOCKED / NO EVIDENCE`.
  - Fallo de un motor o servicio externo $\longrightarrow$ `ENGINE_ERROR / BLOCKED`.
  - Estrategia o cálculo sin datos fuera de muestra $\longrightarrow$ `NO EVIDENCE / REJECTED`.
- **EVIDENCIA FÍSICA OBLIGATORIA**: Toda métrica y veredicto debe ser producto exclusivo de datos reales verificados en disco o respuestas contrastadas de APIs reales.

### 1.2 PRINCIPIO DE PACIENCIA Y CALIDAD FORENSE (NO HAY PRISA)
- **EL USUARIO NO TIENE PRISA**: Prohibido tomar atajos apresurados, soluciones superficiales o intentar resolver problemas complejos en un solo turno descuidado.
- **LOOPS DE REINTENTO Y AUTOCORRECCIÓN ILIMITADOS**: Ante cualquier fallo de test, discrepancia numérica o error de ejecución, itera sistemáticamente:
  $$\text{1. Diagnóstico Forense de Causa Raíz} \longrightarrow \text{2. Corrección de Código} \longrightarrow \text{3. Re-ejecución de Tests Reales} \longrightarrow \text{4. Auditoría de Resultados}$$
- Repite este ciclo cuantas veces sea necesario hasta que la solución sea matemáticamente exacta y empíricamente verificada.
- Es preferible realizar múltiples ciclos de depuración rigurosa y certificar una solución blindada, que entregar código rápido a medias.

### 1.3 PROHIBICIÓN ABSOLUTA DE INVENTAR PÁGINAS, RUTAS O COMPONENTES
- Las rutas del frontend y endpoints del backend deben ceñirse estrictamente a la arquitectura y contratos oficiales del proyecto.
- **PROHIBIDO crear subpáginas temporales, borradores o enlaces rotos** que desvíen o saturen la aplicación.

### 1.4 MANTENIMIENTO Y LIMPIEZA DEL WORKSPACE
- No dejar archivos temporales sueltos en la raíz (`.zip`, `.bat`, `.tmp`, scripts huérfanos).
- Mantener la separación limpia y desacoplada entre capas: contratos inmutables, motores de exploración, motores de validación, servicios y vistas.

---

## 2. ARQUITECTURA DINÁMICA DE EJECUCIÓN (UNIVERSAL PARA CUALQUIER PROYECTO)

- **DETECCIÓN DINÁMICA DEL ENTORNO**:
  - Descubre dinámicamente puertos, procesos, servicios y variables de entorno en lugar de asumir configuraciones estáticas predefinidas.
- **SEPARACIÓN COGNITIVA ESTRICTA**:
  - **Capa Discovery / Exploración**: Abierta a generar, optimizar y explorar hipótesis algorítmicas o soluciones técnicas.
  - **Capa Validación / Juez**: Evaluador independiente, ciego e inmutable. Evalúa las hipótesis desde cero sobre datos reales sin alterar los parámetros.
  - **Capa Certificación**: Emisión de veredictos verificables basados en evidencia matemática.
